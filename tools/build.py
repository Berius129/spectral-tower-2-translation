"""Build a translated copy of the disc from script/*.json.

Usage: python3 tools/build.py "path/to/original.bin" [--fullwidth]

Writes build/Spectral Tower II (English).bin/.cue. The original is never modified.
English is encoded with DTE (letter pairs drawn into kanji glyphs, see dte.py).
--fullwidth uses full-width characters (ＡＢＣ) instead, without touching the font.
"""
import argparse
import collections
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(__file__))
import codepatch
import dte
import exestrings
import graphics
import movie_subs
import psxiso
import sttext

ROOT = os.path.join(os.path.dirname(__file__), '..')
SCRIPT = os.path.join(ROOT, 'script')
BUILD = os.path.join(ROOT, 'build')
NAME = 'Spectral Tower II (English)'
EXE = '/SLPS_011.79'
KANJI = re.compile(r'[一-鿿]')
MIN_CELLS = 16


def load_script(folder):
    """Yield (disc path, all entries) for every JSON file."""
    for dirpath, _, names in os.walk(folder):
        for name in sorted(names):
            if name.endswith('.json'):
                jf = os.path.join(dirpath, name)
                path = '/' + os.path.relpath(jf, folder)[:-5].replace(os.sep, '/')
                yield path, json.load(open(jf, encoding='utf-8'))


def jp_width(jp):
    """Longest visual line of the original text, in cells (one per character)."""
    parts = dte.split_line(jp, jp)
    widest = cur = 0
    for is_text, chunk in parts:
        if is_text:
            cur += len(chunk)
            widest = max(widest, cur)
        elif dte.LINE_RESET.fullmatch(chunk):
            cur = 0
    return widest


def has_english(e):
    """An entry has English, or is meant to be empty ("mode": "empty", e.g. a
    prefix English doesn't need)."""
    return bool(e['en']) or e.get('mode') == 'empty'


def encode_text(e, table, fullwidth):
    """English of one entry as the game's text (str)."""
    if fullwidth or e.get('mode') == 'fullwidth':
        return sttext.to_fullwidth(e['en'])
    return table.encode(dte.split_line(e['jp'], e['en']))


def check_syntax(e, where):
    """Warn about anything in the English that would be kept as a raw
    control code but is not in the original (it would show as garbage)."""
    extra = [m for m in dte.SYNTAX.findall(e['en'])
             if m.startswith('(') and m not in dte.SYNTAX.findall(e['jp'])]
    if extra:
        print(f'WARNING {where}: not in the original, kept as raw codes: {" ".join(extra)}')
        return 1
    return 0


def check_codes(e, where):
    """Warn when control codes are missing or extra. Order and line breaks
    may change in English (e.g. a name moves inside the sentence)."""
    def codes(text):
        return collections.Counter(c for c in sttext.CONTROL.findall(text) if c != '￥ｎ')
    if codes(e['jp']) != codes(e['en']):
        print(f'WARNING {where}: control codes differ from the original')
        return 1
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('bin')
    ap.add_argument('--fullwidth', action='store_true')
    ap.add_argument('--script', default=SCRIPT, help='folder with the translation JSON files')
    ap.add_argument('--name', default=NAME, help='output file name (without extension)')
    ap.add_argument('--no-movies', action='store_true', help='skip video subtitle replacement (slow)')
    args = ap.parse_args()

    os.makedirs(BUILD, exist_ok=True)
    out_bin = os.path.join(BUILD, args.name + '.bin')
    print('copying image...')
    shutil.copyfile(args.bin, out_bin)
    with open(os.path.join(BUILD, args.name + '.cue'), 'w') as f:
        f.write(f'FILE "{args.name}.bin" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n')

    img = psxiso.Image(out_bin, writable=True)
    script = list(load_script(args.script))
    exe_entries = next((entries for path, entries in script if path == EXE), [])
    script = [(path, entries) for path, entries in script if path != EXE]
    errors = warnings = 0

    table = None
    if not args.fullwidth:
        keep, counts = set(), collections.Counter()
        for entries in [exe_entries] + [entries for _, entries in script]:
            for e in entries:
                # kanji kept inside a translation (e.g. 終) must keep their glyph
                keep.update(KANJI.findall(e['en']))
                if e['en'] and e.get('mode') == 'fullwidth':
                    continue
                if has_english(e):
                    for is_text, chunk in dte.split_line(e['jp'], e['en']):
                        if is_text:
                            counts.update(c for c in dte.pairs(chunk) if dte.is_pair(c))
                else:
                    keep.update(KANJI.findall(e['jp']))
        table = dte.Table([p for p, _ in counts.most_common()], keep, dte.load_assigned())
        dte.save_assigned(table.code)
        print(f'DTE: {len(table.code)} letter pairs ({len(counts)} in use)')
        if table.overwritten:
            print(f'WARNING {len(table.overwritten)} kanji still used by Japanese text were overwritten')
            warnings += 1

    patched = translated = 0
    exe = img.read(EXE)
    for e in exe_entries:
        if not has_english(e):
            continue
        where = f'{EXE} {e["offset"]}'
        off = int(e['offset'], 16)
        if e.get('locked'):
            print(f'ERROR {where}: string shares bytes with another one and cannot be translated yet')
            errors += 1
            continue
        if exe[off:off + len(e['jp'].encode(sttext.ENCODING))].decode(sttext.ENCODING) != e['jp']:
            print(f'ERROR {where}: Japanese text does not match the disc')
            errors += 1
            continue
        warnings += check_codes(e, where)
        try:
            exe = exestrings.patch(exe, off, encode_text(e, table, args.fullwidth).encode(sttext.ENCODING),
                                   e['max'], e.get('joined', False))
            translated += 1
        except (ValueError, UnicodeEncodeError) as ex:
            print(f'ERROR {ex}')
            errors += 1
    font = dte.load_font()
    if table:
        exe = table.patch_font(exe, font)
    exe = codepatch.apply(exe, font)
    img.write(EXE, exe)
    graphics.apply(img)

    for path, entries in script:
        todo = [e for e in entries if has_english(e)]
        if not todo:
            continue
        cells = max([MIN_CELLS] + [jp_width(e['jp']) for e in entries])
        lines = sttext.decode(img.read(path))
        for e in todo:
            where = f'{path} line {e["line"]}'
            if lines[e['line']] != e['jp']:
                print(f'ERROR {where}: Japanese text does not match the disc')
                errors += 1
                continue
            warnings += check_codes(e, where)
            warnings += check_syntax(e, where)
            if not args.fullwidth:
                width = dte.visual_width(dte.split_line(e['jp'], e['en']))
                if width > cells:
                    print(f'WARNING {where}: a line is {width * 2} letters long, the window fits about {cells * 2}')
                    warnings += 1
            lines[e['line']] = encode_text(e, table, args.fullwidth)
            translated += 1
        try:
            img.write(path, sttext.encode(lines))
            patched += 1
        except (ValueError, UnicodeEncodeError) as ex:
            print(f'ERROR {ex}')
            errors += 1
    img.close()
    if not args.no_movies and not errors:
        tools = [movie_subs.JAVA, movie_subs.JPSXDEC, movie_subs.FFMPEG]
        missing = [t for t in tools if not os.path.exists(t)]
        if missing:
            print(f'WARNING videos skipped, missing: {", ".join(missing)}')
            warnings += 1
        else:
            movie_subs.main(out_bin, [])
    print(f'{patched} files patched, {translated} lines translated, {warnings} warnings, {errors} errors')
    print(f'-> {out_bin}')
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()

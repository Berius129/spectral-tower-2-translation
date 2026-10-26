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
import dte
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
        elif chunk in ('￥ｎ', '(B)', '(E)'):
            cur = 0
    return widest


def exe_kanji(exe):
    """Kanji used by Japanese strings inside the executable."""
    found = set()
    for run in re.findall(rb'(?:[\x81-\x9f\xe0-\xef][\x40-\xfc])+', exe):
        try:
            found.update(KANJI.findall(run.decode(sttext.ENCODING)))
        except UnicodeDecodeError:
            pass
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('bin')
    ap.add_argument('--fullwidth', action='store_true')
    ap.add_argument('--script', default=SCRIPT, help='folder with the translation JSON files')
    ap.add_argument('--name', default=NAME, help='output file name (without extension)')
    args = ap.parse_args()

    os.makedirs(BUILD, exist_ok=True)
    out_bin = os.path.join(BUILD, args.name + '.bin')
    print('copying image...')
    shutil.copyfile(args.bin, out_bin)
    with open(os.path.join(BUILD, args.name + '.cue'), 'w') as f:
        f.write(f'FILE "{args.name}.bin" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n')

    img = psxiso.Image(out_bin, writable=True)
    script = list(load_script(args.script))
    errors = warnings = 0

    table = None
    if not args.fullwidth:
        exe = img.read(EXE)
        keep = exe_kanji(exe)
        counts = collections.Counter()
        for _, entries in script:
            for e in entries:
                if e['en']:
                    for is_text, chunk in dte.split_line(e['jp'], e['en']):
                        if is_text:
                            counts.update(c for c in dte.pairs(chunk) if dte.is_pair(c))
                else:
                    keep.update(KANJI.findall(e['jp']))
        table = dte.Table([p for p, _ in counts.most_common()], keep)
        img.write(EXE, table.patch_font(exe, dte.load_font()))
        print(f'DTE: {len(table.code)} letter pairs')
        if table.overwritten:
            print(f'WARNING {len(table.overwritten)} kanji still used by Japanese text were overwritten')
            warnings += 1

    patched = translated = 0
    for path, entries in script:
        todo = [e for e in entries if e['en']]
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
            if sttext.CONTROL.findall(e['jp']) != sttext.CONTROL.findall(e['en']):
                print(f'WARNING {where}: control codes differ from the original')
                warnings += 1
            if args.fullwidth:
                lines[e['line']] = sttext.to_fullwidth(e['en'])
            else:
                parts = dte.split_line(e['jp'], e['en'])
                width = dte.visual_width(parts)
                if width > cells:
                    print(f'WARNING {where}: a line is {width * 2} letters long, the window fits about {cells * 2}')
                    warnings += 1
                lines[e['line']] = table.encode(parts)
            translated += 1
        try:
            img.write(path, sttext.encode(lines))
            patched += 1
        except (ValueError, UnicodeEncodeError) as ex:
            print(f'ERROR {ex}')
            errors += 1
    img.close()
    print(f'{patched} files patched, {translated} lines translated, {warnings} warnings, {errors} errors')
    print(f'-> {out_bin}')
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()

"""Build a translated copy of the disc from script/*.json.

Usage: python3 tools/build.py "path/to/original.bin" [--fullwidth]

Writes build/Spectral Tower II (English).bin/.cue. The original is never modified.
--fullwidth converts English to full-width characters (ＡＢＣ), useful for
testing before the game's font supports narrow ASCII.
"""
import argparse
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(__file__))
import psxiso
import sttext

ROOT = os.path.join(os.path.dirname(__file__), '..')
SCRIPT = os.path.join(ROOT, 'script')
BUILD = os.path.join(ROOT, 'build')
NAME = 'Spectral Tower II (English)'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('bin')
    ap.add_argument('--fullwidth', action='store_true')
    args = ap.parse_args()

    os.makedirs(BUILD, exist_ok=True)
    out_bin = os.path.join(BUILD, NAME + '.bin')
    print('copying image...')
    shutil.copyfile(args.bin, out_bin)
    with open(os.path.join(BUILD, NAME + '.cue'), 'w') as f:
        f.write(f'FILE "{NAME}.bin" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n')

    img = psxiso.Image(out_bin, writable=True)
    patched = translated = errors = 0
    for dirpath, _, names in os.walk(SCRIPT):
        for name in sorted(names):
            if not name.endswith('.json'):
                continue
            jf = os.path.join(dirpath, name)
            path = '/' + os.path.relpath(jf, SCRIPT)[:-5].replace(os.sep, '/')
            entries = [e for e in json.load(open(jf, encoding='utf-8')) if e['en']]
            if not entries:
                continue
            lines = sttext.decode(img.read(path))
            for e in entries:
                if lines[e['line']] != e['jp']:
                    print(f'ERROR {path} line {e["line"]}: Japanese text does not match the disc')
                    errors += 1
                    continue
                if sttext.CONTROL.findall(e['jp']) != sttext.CONTROL.findall(e['en']):
                    print(f'WARNING {path} line {e["line"]}: control codes differ from the original')
                lines[e['line']] = sttext.to_fullwidth(e['en']) if args.fullwidth else e['en']
                translated += 1
            try:
                img.write(path, sttext.encode(lines))
                patched += 1
            except (ValueError, UnicodeEncodeError) as ex:
                print(f'ERROR {ex}')
                errors += 1
    img.close()
    print(f'{patched} files patched, {translated} lines translated, {errors} errors')
    print(f'-> {out_bin}')
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()

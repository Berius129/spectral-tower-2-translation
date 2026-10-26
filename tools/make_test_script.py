"""Generate a test script where every Japanese run is replaced by English
filler of the same byte size, to check how the game renders Latin text.

Usage: python3 tools/make_test_script.py OUT_DIR [--fullwidth] [prefix ...]

Prefixes limit which files are filled (e.g. FIX0/FIX00001 BCHARA/MSG).
Section headers like [...] are left untouched.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
import sttext

SCRIPT = os.path.join(os.path.dirname(__file__), '..', 'script')
FILLER = 'The quick brown fox jumps over the lazy dog 0123456789 '
RUN = re.compile(r'[　-ヿ一-鿿！-～｡-￯]+')


def fill(n_bytes, fullwidth):
    n = n_bytes // 2 if fullwidth else n_bytes
    s = (FILLER * (n // len(FILLER) + 1))[:n]
    return sttext.to_fullwidth(s) if fullwidth else s


def convert(line, fullwidth):
    out, pos = [], 0
    # control codes like ￥ｎ are full-width but must survive
    for m in sttext.CONTROL.finditer(line):
        out.append(_fill_runs(line[pos:m.start()], fullwidth))
        out.append(m.group())
        pos = m.end()
    out.append(_fill_runs(line[pos:], fullwidth))
    return ''.join(out)


def _fill_runs(s, fullwidth):
    return RUN.sub(lambda m: fill(len(m.group().encode(sttext.ENCODING)), fullwidth), s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('prefixes', nargs='*')
    ap.add_argument('--fullwidth', action='store_true')
    args = ap.parse_args()
    count = 0
    for dirpath, _, names in os.walk(SCRIPT):
        for name in names:
            jf = os.path.join(dirpath, name)
            rel = os.path.relpath(jf, SCRIPT)
            if args.prefixes and not any(rel.startswith(p) for p in args.prefixes):
                continue
            entries = json.load(open(jf, encoding='utf-8'))
            for e in entries:
                if not e['jp'].startswith('[') and not e.get('locked') and not e['en']:
                    e['en'] = convert(e['jp'], args.fullwidth)
                    count += 1
            out = os.path.join(args.out, rel)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            json.dump(entries, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{count} test lines -> {args.out}')


if __name__ == '__main__':
    main()

"""Check which executable translations fit their space.

Usage: python3 tools/fit.py [--all]
Lists entries of script/SLPS_011.79.json whose English is too long
(--all: every translated entry with its size).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import dte
import sttext

PATH = os.path.join(os.path.dirname(__file__), '..', 'script', 'SLPS_011.79.json')


def size(e):
    if e.get('mode') == 'fullwidth':
        text = sttext.to_fullwidth(e['en'])
        return len(text.encode(sttext.ENCODING))
    n = 0
    for is_text, chunk in dte.split_line(e['jp'], e['en']):
        n += 2 * len(dte.pairs(chunk)) if is_text else len(chunk.encode(sttext.ENCODING))
    return n


def main():
    entries = json.load(open(PATH, encoding='utf-8'))
    done = [e for e in entries if e['en']]
    bad = 0
    for e in done:
        n = size(e)
        if n > e['max'] or '--all' in sys.argv:
            print(f'{e["offset"]:>9} {n:3d}/{e["max"]:<3d} {"TOO LONG " if n > e["max"] else ""}{e["en"]}')
            bad += n > e['max']
    print(f'{len(done)}/{len(entries)} translated, {bad} too long')


if __name__ == '__main__':
    main()

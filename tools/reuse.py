"""Fill untranslated entries whose Japanese text is identical to an
already translated one (translation memory). Line labels such as ALL, or
DEF, are ignored when matching and each entry keeps its own.

Usage: python3 tools/reuse.py [prefix ...]
Only files under script/<prefix> are filled (default: all). Prints how
many entries were filled.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import dte

SCRIPT = os.path.join(os.path.dirname(__file__), '..', 'script')


def split_label(text):
    m = dte.PREFIX.match(text)
    return (m.group(), text[m.end():]) if m else ('', text)


def main(prefixes):
    files = []
    for dirpath, _, names in os.walk(SCRIPT):
        for name in names:
            if name.endswith('.json'):
                files.append(os.path.join(dirpath, name))
    memory = {}
    for f in files:
        for e in json.load(open(f, encoding='utf-8')):
            if e['en'] and 'line' in e:
                label, body = split_label(e['jp'])
                if e['en'].startswith(label):
                    memory.setdefault(body, e['en'][len(label):])
    filled = 0
    for f in files:
        rel = os.path.relpath(f, SCRIPT)
        if prefixes and not any(rel.startswith(p) for p in prefixes):
            continue
        entries = json.load(open(f, encoding='utf-8'))
        changed = False
        for e in entries:
            label, body = split_label(e['jp']) if 'line' in e else ('', None)
            if not e['en'] and body in memory:
                e['en'] = label + memory[body]
                changed = True
                filled += 1
        if changed:
            with open(f, 'w', encoding='utf-8') as fh:
                json.dump(entries, fh, ensure_ascii=False, indent=1)
                fh.write('\n')
    print(f'{filled} entries filled from translation memory')


if __name__ == '__main__':
    main(sys.argv[1:])

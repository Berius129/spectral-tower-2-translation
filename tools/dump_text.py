"""Extract every translatable line from the original disc into script/*.json.

Usage: python3 tools/dump_text.py "path/to/Spectral Tower II (Japan).bin"

Existing translations in script/ are kept: only lines whose Japanese text
changed (or new lines) are reset.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import exestrings
import psxiso
import sttext

ROOT = os.path.join(os.path.dirname(__file__), '..')
SCRIPT = os.path.join(ROOT, 'script')


def save(path, entries, key):
    """Write entries to script/<path>.json, keeping translations whose key still matches."""
    out = os.path.join(SCRIPT, path.lstrip('/') + '.json')
    if os.path.exists(out):
        old = {key(e): e['en'] for e in json.load(open(out, encoding='utf-8'))}
        for e in entries:
            e['en'] = old.get(key(e), '')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=1)
        f.write('\n')


def main(bin_path):
    img = psxiso.Image(bin_path)

    strings = exestrings.find(img.read(exestrings.PATH))
    entries = [{'offset': f'{s["offset"]:#x}', 'max': s['max'], 'jp': s['jp'], 'en': ''}
               | ({'locked': True} if s['locked'] else {}) for s in strings]
    save(exestrings.PATH, entries, lambda e: (e['offset'], e['jp']))
    print(f'{exestrings.PATH}: {len(entries)} strings')

    files = lines_total = 0
    for path in sorted(p for p in img.files if sttext.TEXT_FILES.match(p)):
        raw = img.read(path)
        lines = sttext.decode(raw)
        assert sttext.encode(lines) == raw, f'{path}: round trip failed'
        entries = [{'line': i, 'jp': l, 'en': ''} for i, l in enumerate(lines) if sttext.JAPANESE.search(l)]
        if not entries:
            continue
        save(path, entries, lambda e: (e['line'], e['jp']))
        files += 1
        lines_total += len(entries)
    print(f'{files} files, {lines_total} lines -> script/')


if __name__ == '__main__':
    main(sys.argv[1])

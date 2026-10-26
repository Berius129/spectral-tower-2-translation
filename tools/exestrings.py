"""Japanese strings inside the executable SLPS_011.79 (menus, battle, system).

Strings are plain cp932, NUL-terminated. Only strings referenced by code
(lui/addiu pairs) or by pointer tables are taken, and only from the two
data areas (the code area in between yields false positives).
Translations are written in place, so each one must fit in the original
string plus its trailing NUL padding.
"""
import re
import struct

import sttext

PATH = '/SLPS_011.79'
BASE = 0x80010000  # RAM address of file offset 0x800
DATA_AREAS = [(0x800, 0xA000), (0xBD000, None)]  # file offsets
# Kana or kanji; strings with only full-width digits/symbols are number glyphs
JAPANESE = re.compile(r'[぀-ヿ一-鿿]')
SYNTAX = re.compile(r'%[-0-9]*[sdxc]|\([0-9A-Za-z]+\)')


def _referenced(exe):
    end = BASE + len(exe) - 0x800
    words = struct.unpack_from(f'<{(len(exe) - 0x800) // 4}I', exe, 0x800)
    refs = set()
    for i, w in enumerate(words):
        if BASE <= w < end:
            refs.add(w)
        if w >> 26 == 0x0F:  # lui rt,hi ... addiu rx,rt,lo
            rt, hi = (w >> 16) & 31, w & 0xFFFF
            for v in words[i + 1:i + 32]:
                if v >> 26 == 0x0F and (v >> 16) & 31 == rt:
                    break
                if v >> 26 == 0x09 and (v >> 21) & 31 == rt:
                    lo = v & 0xFFFF
                    refs.add(((hi << 16) + lo - (0x10000 if lo & 0x8000 else 0)) & 0xFFFFFFFF)
    return {a - BASE + 0x800 for a in refs if BASE <= a < end}


def _in_data(off):
    return any(lo <= off < (hi or 1 << 32) for lo, hi in DATA_AREAS)


def find(exe):
    """Return [{'offset', 'max', 'jp', 'locked'}] sorted by offset."""
    found = []
    for off in sorted(_referenced(exe)):
        if not _in_data(off):
            continue
        raw = exe[off:exe.find(b'\0', off)]
        try:
            text = raw.decode(sttext.ENCODING)
        except UnicodeDecodeError:
            continue
        # the font has no half-width katakana, so those bytes are data, not text
        if not raw or not JAPANESE.search(text) or any(ord(c) < 0x20 or '｡' <= c <= 'ﾟ' for c in text):
            continue
        if re.search(r'[\x21-\x7e]', SYNTAX.sub('', text)):
            continue
        found.append({'offset': off, 'size': len(raw), 'jp': text})
    starts = [s['offset'] for s in found]
    ends = [s['offset'] + s['size'] for s in found]
    for i, s in enumerate(found):
        end = ends[i]
        pad = end
        while pad < len(exe) and exe[pad] == 0:
            pad += 1
        nxt = starts[i + 1] if i + 1 < len(starts) else len(exe)
        s['max'] = min(pad, nxt) - s['offset'] - 1  # keep one NUL
        # a pointer into the middle of this string, or this string inside another
        s['locked'] = nxt < end or (i > 0 and ends[i - 1] > s['offset'])
        del s['size']
    return found


def patch(exe, offset, text_bytes, max_len):
    if len(text_bytes) > max_len:
        raise ValueError(f'{PATH} {offset:#x}: {len(text_bytes)} bytes, only {max_len} fit')
    exe = bytearray(exe)
    exe[offset:offset + max_len + 1] = text_bytes + b'\0' * (max_len + 1 - len(text_bytes))
    return bytes(exe)

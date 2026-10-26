"""DTE (dual-tile encoding): English text is written as pairs of half-width
letters, each pair drawn into the glyph of a JIS level-1 kanji.

The game only renders 2-byte Shift-JIS. Its font lives in SLPS_011.79 as
1bpp 16x11 glyphs (22 bytes each, MSB = leftmost pixel); kanji 0x889F-0x9872
are stored in JIS order starting at file offset KANJI_TABLE.
"""
import os
import re

import sttext

KANJI_TABLE = 0xACFAC  # file offset in SLPS_011.79 (RAM 0x800BC7AC)
GLYPH_BYTES = 22
GLYPH_ROWS = 11
FONT_TOP = 1  # first glyph row used by the 9-row half-width font
LEFT_X, RIGHT_X = 0, 6  # pixel column of each letter in the pair

FONT_PATH = os.path.join(os.path.dirname(__file__), 'font_5x9.txt')

# Line labels at the start of a line: TALK0:  ALL,  30:0,  -1,2,3,4,
PREFIX = re.compile(r'^(?:[A-Z_]*-?\d*[:,])+')
# Syntax inside the text: control codes, line break, choice markers, printf
SYNTAX = re.compile(r'\([0-9A-Za-z:]+\)|￥ｎ|=CP\d+,?|%[-0-9]*[sdxc]')


def kanji_codes():
    """All JIS level-1 kanji codes in glyph-table order."""
    codes = []
    for lead in range(0x88, 0x99):
        for trail in list(range(0x40, 0x7F)) + list(range(0x80, 0xFD)):
            code = lead << 8 | trail
            if 0x889F <= code <= 0x9872:
                codes.append(code)
    assert len(codes) == 2965
    return codes


def code_char(code):
    return bytes([code >> 8, code & 0xFF]).decode(sttext.ENCODING)


def load_font():
    font, cur = {}, None
    for line in open(FONT_PATH, encoding='utf-8'):
        line = line.rstrip('\n')
        if line.startswith('== '):
            cur = ' ' if line[3:] == 'space' else line[3:]
            font[cur] = []
        elif cur is not None and line:  # comments are only allowed before the first glyph
            font[cur].append(line)
    return font


def split_line(jp, en):
    """Split an English line into (is_text, chunk) parts, keeping the
    original line label and all syntax as-is."""
    parts = []
    m = PREFIX.match(jp)
    if m and en.startswith(m.group()):
        parts.append((False, m.group()))
        en = en[m.end():]
    pos = 0
    for s in SYNTAX.finditer(en):
        if s.start() > pos:
            parts.append((True, en[pos:s.start()]))
        parts.append((False, s.group()))
        pos = s.end()
    if pos < len(en):
        parts.append((True, en[pos:]))
    return parts


def pairs(text):
    """Split text into cells: ASCII runs become letter pairs, any other
    character (…, ♪, kana) is kept as a single native cell."""
    cells = []
    for run in re.findall(r'[\x20-\x7e]+|[^\x20-\x7e]', text):
        if not run.isascii():
            cells.append(run)
            continue
        if len(run) % 2:
            run += ' '
        cells.extend(run[i:i + 2] for i in range(0, len(run), 2))
    return cells


def is_pair(cell):
    return cell.isascii()


def visual_width(parts):
    """Longest visual line in cells (one cell = one pair)."""
    widest = cur = 0
    for is_text, chunk in parts:
        if is_text:
            cur += len(pairs(chunk))
            widest = max(widest, cur)
        elif chunk in ('￥ｎ', '(B)', '(E)'):
            cur = 0
    return widest


class Table:
    """Assigns a kanji code to every letter pair."""

    def __init__(self, used_pairs, keep_kanji):
        """used_pairs: pairs ordered by frequency. keep_kanji: kanji still
        needed by untranslated Japanese text; they are used last."""
        codes = kanji_codes()
        free = [c for c in codes if code_char(c) not in keep_kanji]
        busy = [c for c in codes if code_char(c) in keep_kanji]
        order = free + busy
        if len(used_pairs) > len(order):
            raise ValueError(f'{len(used_pairs)} distinct pairs, only {len(order)} glyphs available')
        self.code = dict(zip(used_pairs, order))
        self.overwritten = [code_char(c) for c in busy[:max(0, len(used_pairs) - len(free))]]

    def encode(self, parts):
        out = []
        for is_text, chunk in parts:
            if is_text:
                chunk = ''.join(code_char(self.code[c]) if is_pair(c) else c for c in pairs(chunk))
            out.append(chunk)
        return ''.join(out)

    def patch_font(self, exe, font):
        exe = bytearray(exe)
        index = {c: i for i, c in enumerate(kanji_codes())}
        for pair, code in self.code.items():
            glyph = bytearray(GLYPH_BYTES)
            for ch, x0 in zip(pair, (LEFT_X, RIGHT_X)):
                rows = font.get(ch, font['?'])
                for r, row in enumerate(rows):
                    y = FONT_TOP + r
                    if y >= GLYPH_ROWS:
                        break
                    for x, px in enumerate(row):
                        if px == '#':
                            bit = 15 - (x0 + x)
                            glyph[y * 2 + (1 - bit // 8)] |= 1 << (bit % 8)
            off = KANJI_TABLE + index[code] * GLYPH_BYTES
            exe[off:off + GLYPH_BYTES] = glyph
        return bytes(exe)

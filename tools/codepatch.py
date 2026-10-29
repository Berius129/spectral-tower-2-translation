"""Code patches for SLPS_011.79: narrow full-width Latin letters.

Also the name entry cursor: it is placed at x = index * 13 - 5 above the
name being typed, which assumes every character is a full cell. NAME_HOOK
counts the characters before the cursor in half cells (letters 1, digits
and punctuation 2) so the cursor stays on the next position.

The text engine places glyph N of a line at
    x = window_x + column * window_spacing
where column counts characters (routine 0x8001AA..., draw at 0x8001BDB4).
These patches count the column in half cells instead: normal characters
add 2, full-width A-Z/a-z add 1 (only in windows whose spacing is < 16,
so wide-spaced grids such as name entry keep their layout), and the draw
code divides the product by 2. Names typed in the name entry screen are
full-width letters, so they now look like normal English text.

The hook routine lives in the last glyphs of the kanji table, which DTE
does not use (dte.RESERVED_GLYPHS).
"""
import struct

import dte

BASE = 0x80010000  # RAM address of file offset 0x800

REG = {name: i for i, name in enumerate(
    'zero at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 '
    's0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra'.split())}

# Symbol-table glyph indices (compact table, see README)
FULLWIDTH_UPPER = 157  # Ａ
FULLWIDTH_LOWER = 183  # ａ
SYMBOL_TABLE = 0xAA2A4

HOOK_FILE = dte.KANJI_TABLE + (2965 - dte.RESERVED_GLYPHS) * dte.GLYPH_BYTES
HOOK_RAM = HOOK_FILE - 0x800 + BASE


def _r(op, rs, rt, rd, sa, fn):
    return (op << 26) | (REG[rs] << 21) | (REG[rt] << 16) | (REG[rd] << 11) | (sa << 6) | fn


def _i(op, rs, rt, imm):
    return (op << 26) | (REG[rs] << 21) | (REG[rt] << 16) | (imm & 0xFFFF)


def addu(rd, rs, rt): return _r(0, rs, rt, rd, 0, 0x21)
def subu(rd, rs, rt): return _r(0, rs, rt, rd, 0, 0x23)
def or_(rd, rs, rt): return _r(0, rs, rt, rd, 0, 0x25)
def sll(rd, rt, sa): return _r(0, 'zero', rt, rd, sa, 0x00)
def sra(rd, rt, sa): return _r(0, 'zero', rt, rd, sa, 0x03)
def jr(rs): return _r(0, rs, 'zero', 'zero', 0, 0x08)
def lui(rt, imm): return _i(0x0F, 'zero', rt, imm)
def ori(rt, rs, imm): return _i(0x0D, rs, rt, imm)
def addiu(rt, rs, imm): return _i(0x09, rs, rt, imm)
def sltiu(rt, rs, imm): return _i(0x0B, rs, rt, imm)
def lbu(rt, imm, rs): return _i(0x24, rs, rt, imm)
def beq(rs, rt, offset): return _i(0x04, rs, rt, offset)
def jal(target): return (0x03 << 26) | ((target >> 2) & 0x3FFFFFF)


NOP = 0

# Called instead of "addiu t0,t0,1" (column += 1); t0 = column.
# s3 = window offset, s6 = window text buffer (2 bytes per character).
HOOK = [
    lui('at', 0x801C),
    addu('at', 'at', 's3'),
    lbu('t1', -24348, 'at'),      # window spacing
    lbu('t2', -24367, 'at'),      # index of the current character
    sltiu('t1', 't1', 16),
    beq('t1', 'zero', 13),        # wide spacing -> wide
    sll('t2', 't2', 1),
    addu('t2', 's6', 't2'),
    lbu('t1', 0, 't2'),
    lbu('t2', 1, 't2'),
    sll('t1', 't1', 8),
    or_('t1', 't1', 't2'),        # Shift-JIS code
    ori('t2', 'zero', 0x8260),
    subu('t2', 't1', 't2'),
    sltiu('t2', 't2', 0x829B - 0x8260),  # Ａ..ｚ
    beq('t2', 'zero', 3),         # not a letter -> wide
    NOP,
    jr('ra'),
    addiu('t0', 't0', 1),         # narrow: half a cell
    jr('ra'),                     # wide: a full cell
    addiu('t0', 't0', 2),
]

# Name entry: replaces a0 = index * 13 with the width of the characters
# before the cursor. In: v1 = cursor index. Out: a0. Clobbers v0, at, a1, a2.
NAME_BUFFER = 0x801B7B88  # the name being edited, 2 bytes per character
NAME_HOOK = [
    lui('a1', NAME_BUFFER >> 16),
    addiu('a1', 'a1', NAME_BUFFER & 0xFFFF),
    or_('a2', 'v1', 'zero'),
    or_('a0', 'zero', 'zero'),     # half cells
    beq('a2', 'zero', 10),         # loop: done?
    addiu('a2', 'a2', -1),
    lbu('v0', 0, 'a1'),
    lbu('at', 1, 'a1'),
    sltiu('v0', 'v0', 0x82),       # 0x81xx punctuation: wide
    addiu('a0', 'a0', 1),
    sltiu('at', 'at', 0x60),       # 0x824F-0x8258 digits: wide
    or_('v0', 'v0', 'at'),
    addu('a0', 'a0', 'v0'),
    beq('zero', 'zero', -10),
    addiu('a1', 'a1', 2),
    sll('v0', 'a0', 1),            # done: a0 = half cells * 13 / 2
    addu('v0', 'v0', 'a0'),
    sll('v0', 'v0', 2),
    addu('v0', 'v0', 'a0'),
    jr('ra'),
    sra('a0', 'v0', 1),
]
NAME_HOOK_RAM = HOOK_RAM + len(HOOK) * 4

# (RAM address, original word, new word)
PATCHES = [
    (0x8001AEB4, NOP, jal(HOOK_RAM)),
    (0x8001AEB8, addiu('t0', 't0', 1), NOP),
    (0x8001BDDC, NOP, sra('v1', 'v1', 1)),  # x offset = column * spacing / 2
    (0x8006FFFC, sll('v0', 'v1', 1), jal(NAME_HOOK_RAM)),
    (0x80070000, addu('v0', 'v0', 'v1'), NOP),
    (0x80070004, sll('a0', 'v0', 2), NOP),
    (0x80070008, addu('a0', 'a0', 'v1'), NOP),
]


def _off(ram):
    return ram - BASE + 0x800


def apply(exe, font):
    exe = bytearray(exe)
    assert (len(HOOK) + len(NAME_HOOK)) * 4 <= dte.RESERVED_GLYPHS * dte.GLYPH_BYTES
    for ram, old, new in PATCHES:
        cur = struct.unpack_from('<I', exe, _off(ram))[0]
        if cur != old:
            raise ValueError(f'{ram:#x}: expected {old:#010x}, found {cur:#010x}')
        struct.pack_into('<I', exe, _off(ram), new)
    struct.pack_into(f'<{len(HOOK) + len(NAME_HOOK)}I', exe, HOOK_FILE, *HOOK, *NAME_HOOK)

    # Full-width letters become single half-width letters at the left of the cell
    for first, letters in ((FULLWIDTH_UPPER, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
                           (FULLWIDTH_LOWER, 'abcdefghijklmnopqrstuvwxyz')):
        for i, ch in enumerate(letters):
            off = SYMBOL_TABLE + (first + i) * dte.GLYPH_BYTES
            exe[off:off + dte.GLYPH_BYTES] = dte.draw_glyph(font, ch + ' ')
    return bytes(exe)

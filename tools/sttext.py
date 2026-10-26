"""Spectral Tower II text files: Shift-JIS (cp932) with every byte XOR 0xFF,
lines separated by CRLF."""
import re

ENCODING = 'cp932'
NEWLINE = '\r\n'

# Directories whose files are XOR-encoded text
TEXT_FILES = re.compile(
    r'^/(BCHARA/MSG/.*\.TXT'
    r'|COMMON/(DIEMSG|MAIL)\.DAT'
    r'|DRAMA/DRAMA\d+\.DAT'
    r'|FIX[01]/[^/]+/FIX(_EV)?\d+\.DAT'
    r'|ITEM/I\d/ITEM\d+\.DAT'
    r'|ROOTSDAT/RTS\d/\d+\.RTS)$')

JAPANESE = re.compile(r'[　-ヿ一-鿿！-￯]')

# Control codes that must survive translation untouched
CONTROL = re.compile(r'\([0-9A-Z]+\)|￥ｎ|%[-0-9]*[sdxc]')


def xor(data):
    return bytes(b ^ 0xFF for b in data)


def decode(data):
    return xor(data).decode(ENCODING).split(NEWLINE)


def encode(lines):
    return xor(NEWLINE.join(lines).encode(ENCODING))


def to_fullwidth(text):
    """Convert ASCII to full-width, leaving control codes alone."""
    out, pos = [], 0
    for m in CONTROL.finditer(text):
        out.append(_fw(text[pos:m.start()]))
        out.append(m.group())
        pos = m.end()
    out.append(_fw(text[pos:]))
    return ''.join(out)


# Full-width forms missing from the game font (cp932 puts them in the IBM
# extension area): use the closest JIS symbol
FW_SPECIAL = {' ': '　', "'": '’', '"': '”'}


def _fw(s):
    return ''.join(FW_SPECIAL.get(c) or (chr(ord(c) + 0xFEE0) if '!' <= c <= '~' else c) for c in s)

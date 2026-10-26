"""Edits to graphics (TIM images) on the disc.

COMMON/STWIN.TIM holds the UI sheet with button labels (4bpp). Most labels
are already English; "ルーツ" becomes "ROOT", built from the letters of the
"SORT" label so the style matches. The box is 22 px wide, too narrow for
"ROOTS".
"""
import tim

STWIN = '/COMMON/STWIN.TIM'

# Letter columns (x, width) in the SORT label, rows 57-62
SORT_LETTERS = {'S': (194, 4), 'O': (199, 4), 'R': (204, 4), 'T': (209, 5)}
SORT_TOP = 57
# ルーツ label: interior x 97..117, text rows 49-54
ROOTS_BOX = (97, 117)
ROOTS_TOP = 49
BACKGROUND = 4
ROWS = 6


def _get(data, t, x, y):
    b = data[t['img_off'] + (y * t['width'] + x) // 2]
    return b & 15 if x % 2 == 0 else b >> 4


def _set(data, t, x, y, v):
    i = t['img_off'] + (y * t['width'] + x) // 2
    data[i] = (data[i] & 0xF0) | v if x % 2 == 0 else (data[i] & 0x0F) | (v << 4)


def roots_label(data):
    data = bytearray(data)
    t = tim.read(bytes(data))
    x0, x1 = ROOTS_BOX
    for y in range(ROOTS_TOP, ROOTS_TOP + ROWS):
        for x in range(x0, x1 + 1):
            _set(data, t, x, y, BACKGROUND)
    x = x0 + 1
    for ch in 'ROOT':
        sx, w = SORT_LETTERS[ch]
        for dy in range(ROWS):
            for dx in range(w):
                _set(data, t, x + dx, ROOTS_TOP + dy, _get(data, t, sx + dx, SORT_TOP + dy))
        x += w + 1
    assert x - 1 <= x1 + 1
    return bytes(data)


def apply(img):
    img.write(STWIN, roots_label(img.read(STWIN)))

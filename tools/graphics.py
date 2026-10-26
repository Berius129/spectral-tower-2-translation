"""Edits to graphics (TIM images) on the disc.

COMMON/STWIN.TIM holds the UI sheet with button labels (4bpp). Most labels
are already English; "ルーツ" becomes "ROOT", built from the letters of the
"SORT" label so the style matches. The box is 22 px wide, too narrow for
"ROOTS".
"""
import dte
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


TREASURE = '/COMMON/TREASURE.TIM'
# "予想" (guess) above the chest-hit bar, 8bpp; the ▽ arrow starts at x 168
AIM_AREA = (130, 238, 166, 255)  # x0, y0, x1, y1 inclusive
AIM_TOP_LEFT = (132, 240)
AIM_SCALE = 2
TRANSPARENT, LIGHT, SHADOW = 255, 21, 1


def aim_label(data):
    """Replace 予想 with AIM, drawn with the DTE font at 2x."""
    data = bytearray(data)
    t = tim.read(bytes(data))
    font = dte.load_font()
    w = t['width']

    def put(x, y, v):
        data[t['img_off'] + y * w + x] = v

    x0, y0, x1, y1 = AIM_AREA
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            put(x, y, TRANSPARENT)
    pixels = set()
    for i, ch in enumerate('AIM'):
        for r, row in enumerate(font[ch][:7]):
            for c, p in enumerate(row):
                if p == '#':
                    for dy in range(AIM_SCALE):
                        for dx in range(AIM_SCALE):
                            pixels.add((AIM_TOP_LEFT[0] + (i * 6 + c) * AIM_SCALE + dx,
                                        AIM_TOP_LEFT[1] + r * AIM_SCALE + dy))
    for x, y in pixels:  # shadow first, one pixel down-right
        if (x + 1, y + 1) not in pixels and x + 1 <= x1 and y + 1 <= y1:
            put(x + 1, y + 1, SHADOW)
    for x, y in pixels:
        put(x, y, LIGHT)
    return bytes(data)


def apply(img):
    img.write(STWIN, roots_label(img.read(STWIN)))
    img.write(TREASURE, aim_label(img.read(TREASURE)))

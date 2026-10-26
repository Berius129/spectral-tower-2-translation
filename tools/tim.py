"""Minimal PlayStation TIM reader/writer (4bpp and 8bpp with CLUT, 16bpp)."""
import struct
import zlib


def read(data):
    magic, flags = struct.unpack_from('<II', data, 0)
    assert magic == 0x10, 'not a TIM'
    bpp = {0: 4, 1: 8, 2: 16, 3: 24}[flags & 7]
    pos = 8
    clut = None
    if flags & 8:
        size, x, y, w, h = struct.unpack_from('<IHHHH', data, pos)
        clut = list(struct.unpack_from(f'<{w * h}H', data, pos + 12))
        pos += size
    size, x, y, w, h = struct.unpack_from('<IHHHH', data, pos)
    img_off = pos + 12
    width = w * 16 // bpp
    raw = data[img_off:img_off + w * h * 2]
    if bpp == 4:
        px = [b >> s & 15 for b in raw for s in (0, 4)]
    elif bpp == 8:
        px = list(raw)
    else:
        px = list(struct.unpack_from(f'<{w * h}H', raw))
    return {'bpp': bpp, 'clut': clut, 'width': width, 'height': h, 'pixels': px, 'img_off': img_off}


def color(c):
    return ((c & 31) << 3, (c >> 5 & 31) << 3, (c >> 10 & 31) << 3, 0 if c == 0 else 255)


def to_png(t, path, palette=0, scale=1):
    w, h = t['width'], t['height']
    if t['bpp'] == 16:
        rgba = [color(c) for c in t['pixels']]
    else:
        n = 16 if t['bpp'] == 4 else 256
        pal = t['clut'][palette * n:(palette + 1) * n]
        rgba = [color(pal[i]) for i in t['pixels']]
    rows = []
    for y in range(h):
        row = bytearray()
        for x in range(w):
            row += bytes(rgba[y * w + x]) * scale
        rows.append(b'\0' + bytes(row))
    raw = b''.join(r for r in rows for _ in range(scale))

    def chunk(tag, body):
        return struct.pack('>I', len(body)) + tag + body + struct.pack('>I', zlib.crc32(tag + body))
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w * scale, h * scale, 8, 6, 0, 0, 0))
                + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))

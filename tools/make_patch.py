"""Make an xdelta (VCDIFF, RFC 3284) patch from the original disc to the
translated one, and check it by applying it.

Usage: python3 tools/make_patch.py ORIGINAL.bin TRANSLATED.bin OUT.xdelta

The translated image is the same size as the original, so each window
copies the unchanged bytes from the same place in the source and adds the
changed ones. Plain VCDIFF with the default code table and no secondary
compression: xdelta3, xdelta UI, Delta Patcher and Rom Patcher JS apply it.
"""
import hashlib
import sys

MAGIC = b'\xd6\xc3\xc4\x00'
VCD_SOURCE = 0x01
WINDOW = 1 << 20     # target bytes per window
MIN_COPY = 16        # shorter unchanged runs are cheaper as part of an ADD
BLOCK = 64           # compare in blocks first, bytes only inside changed blocks
# default code table (RFC 3284 section 5.6): size 0 means the size follows
ADD0, COPY0_MODE0 = 1, 19


def varint(n):
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.append(0x80 | (n & 0x7F))
        n >>= 7
    return bytes(reversed(out))


def read_varint(data, pos):
    n = 0
    while True:
        b = data[pos]
        pos += 1
        n = (n << 7) | (b & 0x7F)
        if not b & 0x80:
            return n, pos


def changed_spans(src, tgt):
    """[start, end) ranges where the bytes differ; gaps shorter than
    MIN_COPY are merged, since copying them costs more than adding them."""
    spans = []
    for b in range(0, len(tgt), BLOCK):
        if src[b:b + BLOCK] == tgt[b:b + BLOCK]:
            continue
        for k in range(b, min(b + BLOCK, len(tgt))):
            if src[k] != tgt[k]:
                if spans and k - spans[-1][1] < MIN_COPY:
                    spans[-1][1] = k + 1
                else:
                    spans.append([k, k + 1])
    return spans


def window(src, tgt, start):
    """Encode target[start:start + len(tgt)] against the source bytes at the same place."""
    data, inst, addr = bytearray(), bytearray(), bytearray()
    pos = 0
    for a, b in changed_spans(src, tgt) + [[len(tgt), len(tgt)]]:
        if a > pos:
            inst += bytes([COPY0_MODE0]) + varint(a - pos)
            addr += varint(pos)  # VCD_SELF: offset in the source segment
        if b > a:
            inst += bytes([ADD0]) + varint(b - a)
            data += tgt[a:b]
        pos = b
    body = (bytes([0]) + varint(len(data)) + varint(len(inst)) + varint(len(addr))
            + bytes(data) + bytes(inst) + bytes(addr))
    head = varint(len(tgt)) + body  # target window length, then the rest
    return (bytes([VCD_SOURCE]) + varint(len(src)) + varint(start)
            + varint(len(head)) + head)


def make(src, tgt):
    out = bytearray(MAGIC + b'\x00')
    for start in range(0, len(tgt), WINDOW):
        out += window(src[start:start + WINDOW], tgt[start:start + WINDOW], start)
    return bytes(out)


def apply(src, patch):
    """Minimal VCDIFF decoder for what make() writes (ADD and COPY mode 0)."""
    assert patch[:4] == MAGIC and patch[4] == 0
    pos, out = 5, bytearray()
    while pos < len(patch):
        ind = patch[pos]
        pos += 1
        assert ind == VCD_SOURCE
        slen, pos = read_varint(patch, pos)
        spos, pos = read_varint(patch, pos)
        _, pos = read_varint(patch, pos)
        tlen, pos = read_varint(patch, pos)
        assert patch[pos] == 0
        pos += 1
        dlen, pos = read_varint(patch, pos)
        ilen, pos = read_varint(patch, pos)
        alen, pos = read_varint(patch, pos)
        data = patch[pos:pos + dlen]
        inst = patch[pos + dlen:pos + dlen + ilen]
        addr = patch[pos + dlen + ilen:pos + dlen + ilen + alen]
        pos += dlen + ilen + alen
        seg = src[spos:spos + slen]
        win, d, i, a = bytearray(), 0, 0, 0
        while i < len(inst):
            code = inst[i]
            size, i = read_varint(inst, i + 1)
            if code == ADD0:
                win += data[d:d + size]
                d += size
            elif code == COPY0_MODE0:
                at, a = read_varint(addr, a)
                win += seg[at:at + size]
            else:
                raise ValueError(f'unexpected instruction {code}')
        assert len(win) == tlen
        out += win
    return bytes(out)


def main(orig, trans, out):
    src = open(orig, 'rb').read()
    tgt = open(trans, 'rb').read()
    if len(src) != len(tgt):
        sys.exit('the images must be the same size')
    patch = make(src, tgt)
    if apply(src, patch) != tgt:
        sys.exit('patch check failed')
    open(out, 'wb').write(patch)
    print(f'{out}: {len(patch)} bytes, checked')
    for name, data in (('original', src), ('patched', tgt)):
        print(f'{name}: MD5 {hashlib.md5(data).hexdigest()}  SHA-1 {hashlib.sha1(data).hexdigest()}')


if __name__ == '__main__':
    main(*sys.argv[1:4])

"""Read and patch files inside a PS1 MODE2/2352 .bin image (single data track).

Files are patched in place: the new data must fit in the sectors already
allocated to the file. EDC/ECC are recomputed for every rewritten sector.
"""
import struct

SECTOR = 2352
DATA = 2048
HDR = 24  # sync(12) + header(4) + subheader(8)


def _edc_table():
    t = []
    for i in range(256):
        e = i
        for _ in range(8):
            e = (e >> 1) ^ (0xD8018001 if e & 1 else 0)
        t.append(e)
    return t


def _ecc_tables():
    f, b = [0] * 256, [0] * 256
    for i in range(256):
        j = (i << 1) ^ (0x11D if i & 0x80 else 0)
        f[i] = j
        b[i ^ j] = i
    return f, b


EDC = _edc_table()
ECC_F, ECC_B = _ecc_tables()


def edc(data):
    e = 0
    for x in data:
        e = (e >> 8) ^ EDC[(e ^ x) & 0xFF]
    return e


def _ecc_pq(src, major_count, minor_count, major_mult, minor_inc):
    # src: 2340 bytes starting at the header (offset 12 of the sector)
    size = major_count * minor_count
    out = bytearray(major_count * 2)
    for major in range(major_count):
        index = (major >> 1) * major_mult + (major & 1)
        a = b = 0
        for _ in range(minor_count):
            t = src[index]
            index += minor_inc
            if index >= size:
                index -= size
            a ^= t
            b ^= t
            a = ECC_F[a]
        a = ECC_B[ECC_F[a] ^ b]
        out[major] = a
        out[major + major_count] = a ^ b
    return out


def fix_sector(sec):
    """Recompute EDC/ECC of a Mode 2 Form 1 sector (bytearray, 2352 bytes)."""
    struct.pack_into('<I', sec, 0x818, edc(sec[0x10:0x818]))
    # ECC is computed with the 4-byte header treated as zero
    saved = bytes(sec[12:16])
    sec[12:16] = b'\0\0\0\0'
    src = bytearray(sec[12:])
    p = _ecc_pq(src, 86, 24, 2, 86)
    src[0x81C - 12:0x81C - 12 + 172] = p
    q = _ecc_pq(src, 52, 43, 86, 88)
    sec[0x81C:0x81C + 172] = p
    sec[0x8C8:0x8C8 + 104] = q
    sec[12:16] = saved


class Image:
    def __init__(self, path, writable=False):
        self.f = open(path, 'r+b' if writable else 'rb')
        self.files = {}  # path -> (lba, size, dirrec_sector, dirrec_offset)
        pvd = self.read_sector(16)
        assert pvd[1:6] == b'CD001', 'not an ISO9660 image'
        root = pvd[156:190]
        self._walk(struct.unpack_from('<I', root, 2)[0],
                   struct.unpack_from('<I', root, 10)[0], '/')

    def read_sector(self, lba):
        self.f.seek(lba * SECTOR + HDR)
        return self.f.read(DATA)

    def _walk(self, lba, size, path):
        for s in range((size + DATA - 1) // DATA):
            data = self.read_sector(lba + s)
            i = 0
            while i < DATA and data[i]:
                rec = data[i:i + data[i]]
                elba, esz = struct.unpack_from('<I', rec, 2)[0], struct.unpack_from('<I', rec, 10)[0]
                name = rec[33:33 + rec[32]]
                if name not in (b'\0', b'\1'):
                    name = name.decode('ascii').split(';')[0]
                    if rec[25] & 2:
                        self._walk(elba, esz, path + name + '/')
                    else:
                        self.files[path + name] = (elba, esz, lba + s, i)
                i += data[i]

    def read(self, path):
        lba, size = self.files[path][:2]
        out = b''.join(self.read_sector(lba + i) for i in range((size + DATA - 1) // DATA))
        return out[:size]

    def write(self, path, data):
        lba, size, rsec, roff = self.files[path]
        cap = (size + DATA - 1) // DATA * DATA
        if len(data) > cap:
            raise ValueError(f'{path}: {len(data)} bytes does not fit in {cap} allocated bytes')
        padded = data + b'\0' * ((DATA - len(data) % DATA) % DATA)
        for i in range(len(padded) // DATA):
            self._write_sector(lba + i, padded[i * DATA:(i + 1) * DATA])
        if len(data) != size:
            self.f.seek(rsec * SECTOR)
            sec = bytearray(self.f.read(SECTOR))
            struct.pack_into('<I', sec, HDR + roff + 10, len(data))
            struct.pack_into('>I', sec, HDR + roff + 14, len(data))
            self._put(rsec, sec)
            self.files[path] = (lba, len(data), rsec, roff)

    def _write_sector(self, lba, data):
        self.f.seek(lba * SECTOR)
        sec = bytearray(self.f.read(SECTOR))
        assert not sec[18] & 0x20, f'sector {lba} is Form 2'
        sec[HDR:HDR + DATA] = data
        self._put(lba, sec)

    def _put(self, lba, sec):
        fix_sector(sec)
        self.f.seek(lba * SECTOR)
        self.f.write(sec)

    def close(self):
        self.f.close()

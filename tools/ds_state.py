"""Read a DuckStation save state (.sav) and bring it into tools/emu.py.

Usage: python3 tools/ds_state.py STATE.sav OUT_RAM.bin DISC.bin
       python3 tools/ds_state.py STATE.sav OUT.state DISC.bin BASE.state

The first form writes the 2 MB main RAM. The second writes a PCSX-ReARMed
state: BASE.state (any state of the same game in the field) with its RAM and
VRAM replaced by the DuckStation ones. CPU, sound and CD state stay from
BASE, which the game tolerates while it runs its main loop.

Uses the zstd library bundled with DuckStation. The 2 MB RAM is found
inside the decompressed state by looking for the game's executable header
region (the copy of SLPS_011.79 loaded at 0x80010000).
"""
import ctypes as C
import struct
import sys

ZSTD = '/Applications/DuckStation.app/Contents/Frameworks/libzstd.1.dylib'
RAM_SIZE = 2 * 1024 * 1024
VRAM_SIZE = 1024 * 1024
# offsets inside a PCSX-ReARMed (libretro) state of this core build
PCSX_RAM = 0x9025
PCSX_VRAM = 0x299745


def decompress(blob, size):
    z = C.CDLL(ZSTD)
    z.ZSTD_decompress.restype = C.c_size_t
    out = C.create_string_buffer(size)
    n = z.ZSTD_decompress(out, C.c_size_t(size), blob, C.c_size_t(len(blob)))
    z.ZSTD_isError.restype = C.c_uint
    if z.ZSTD_isError(C.c_size_t(n)):
        raise RuntimeError('zstd error')
    return out.raw[:n]


def compress(data):
    z = C.CDLL(ZSTD)
    z.ZSTD_compressBound.restype = C.c_size_t
    z.ZSTD_compress.restype = C.c_size_t
    cap = z.ZSTD_compressBound(C.c_size_t(len(data)))
    out = C.create_string_buffer(cap)
    n = z.ZSTD_compress(out, C.c_size_t(cap), data, C.c_size_t(len(data)), 3)
    return out.raw[:n]


def to_duckstation(template, pcsx_state, media_path, out):
    """Write a DuckStation state: TEMPLATE.sav with RAM and VRAM taken from a
    PCSX state and its disc path set to MEDIA_PATH (the .cue to open)."""
    d = open(template, 'rb').read()
    data = bytearray(state_data(template))
    st = open(pcsx_state, 'rb').read()
    base = ram_offset(data)
    data[base:base + RAM_SIZE] = st[PCSX_RAM:PCSX_RAM + RAM_SIZE]
    v = data.find(b'GPU-VRAM') + 8
    data[v:v + VRAM_SIZE] = st[PCSX_VRAM:PCSX_VRAM + VRAM_SIZE]
    path_len, path_off = struct.unpack_from('<2I', d, 0xA8)
    shot_size, shot_off = struct.unpack_from('<2I', d, 0xC0)
    shot = d[shot_off:shot_off + shot_size]
    blob = compress(bytes(data))
    media = media_path.encode()
    head = bytearray(d[:path_off])
    struct.pack_into('<2I', head, 0xA8, len(media), path_off)
    struct.pack_into('<2I', head, 0xC0, shot_size, path_off + len(media))
    struct.pack_into('<4I', head, 0xC8, 2, len(blob), len(data), path_off + len(media) + shot_size)
    open(out, 'wb').write(bytes(head) + media + shot + blob)


def ram_offset(data):
    """RAM inside a decompressed DuckStation state: 0x47 bytes after the
    "Bus" section tag (checked against the executable code in RAM)."""
    t = data.find(b'\x03\x00\x00\x00Bus')
    if t < 0:
        raise RuntimeError('Bus section not found')
    return t + 0x47


def state_data(path):
    d = open(path, 'rb').read()
    assert d[:4] == b'DUCC', 'not a DuckStation state'
    # header tail: data compression type, compressed size, uncompressed size, offset
    ctype, csize, usize, off = struct.unpack_from('<4I', d, 0xC8)
    assert ctype == 2, f'unsupported compression {ctype}'
    return decompress(d[off:off + csize], usize)


def main(path, out, exe=None, base_state=None):
    data = state_data(path)
    marker = exe[0x800 + 0x40000:0x800 + 0x40000 + 256] if exe else None
    if marker:
        i = data.find(marker)
        assert i >= 0, 'RAM not found'
        base = i - 0x50000
    else:
        raise SystemExit('pass the game executable to locate RAM')
    ram = data[base:base + RAM_SIZE]
    if base_state is None:
        open(out, 'wb').write(ram)
        print(f'RAM at state offset {base:#x}, {RAM_SIZE} bytes -> {out}')
        return
    v = data.find(b'GPU-VRAM') + 8
    st = bytearray(open(base_state, 'rb').read())
    st[PCSX_RAM:PCSX_RAM + RAM_SIZE] = ram
    st[PCSX_VRAM:PCSX_VRAM + VRAM_SIZE] = data[v:v + VRAM_SIZE]
    open(out, 'wb').write(st)
    print(f'-> {out}')


if __name__ == '__main__':
    sys.path.insert(0, __file__.rsplit('/', 1)[0])
    import psxiso
    exe = psxiso.Image(sys.argv[3]).read('/SLPS_011.79') if len(sys.argv) > 3 else None
    main(sys.argv[1], sys.argv[2], exe, sys.argv[4] if len(sys.argv) > 4 else None)

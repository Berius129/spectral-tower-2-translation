"""Headless PlayStation emulator for automated testing: a minimal libretro
frontend around the PCSX-ReARMed core, controlled through a UNIX socket.

Start the server (keeps running until "quit"):
    python3 tools/emu.py serve "build/....cue"
Send commands:
    python3 tools/emu.py run 60                 advance 60 frames
    python3 tools/emu.py press cross [frames]   hold a button (default 4 frames), then release 8 frames
    python3 tools/emu.py hold up 30             hold a button for 30 frames (no release pause)
    python3 tools/emu.py seq "cross 4,run 30,down,cross"   several commands in one go
    python3 tools/emu.py shot path.png [2]      screenshot of the current frame (optionally scaled)
    python3 tools/emu.py save name / load name  save states in STATES
    python3 tools/emu.py peek 0x80012345 16     read RAM (hex dump)
    python3 tools/emu.py poke 0x80012345 0102   write RAM bytes (hex)
    python3 tools/emu.py find 1a2b              search RAM for bytes, prints addresses
    python3 tools/emu.py dump path.bin          write all 2 MB of RAM to a file
    python3 tools/emu.py ramload path.bin       replace all of RAM with a file
    python3 tools/emu.py card load|save path    memory card 1 from/to a raw 128 KB file (.mcd)
    python3 tools/emu.py quit
Buttons: cross circle square triangle start select up down left right l1 r1 l2 r2.
"""
import ctypes as C
import os
import socket
import struct
import sys
import zlib

HOME = os.path.expanduser('~')
CORE = os.environ.get('LIBRETRO_CORE', f'{HOME}/.local/libretro/pcsx_rearmed_libretro.dylib')
SYSTEM = os.environ.get('LIBRETRO_SYSTEM', f'{HOME}/.local/libretro/system')
STATES = os.environ.get('EMU_STATES', os.path.join(os.path.dirname(__file__), '..', 'build', 'states'))
SOCK = os.environ.get('EMU_SOCKET', '/tmp/st2emu.sock')

BUTTONS = {'cross': 0, 'square': 1, 'select': 2, 'start': 3, 'up': 4, 'down': 5, 'left': 6, 'right': 7,
           'circle': 8, 'triangle': 9, 'l1': 10, 'r1': 11, 'l2': 12, 'r2': 13}
RAM_BASE = 0x80000000
RETRO_MEMORY_SAVE_RAM = 0
RETRO_MEMORY_SYSTEM_RAM = 2

ENV_CB = C.CFUNCTYPE(C.c_bool, C.c_uint, C.c_void_p)
VIDEO_CB = C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
AUDIO_CB = C.CFUNCTYPE(None, C.c_int16, C.c_int16)
AUDIO_BATCH_CB = C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t)
POLL_CB = C.CFUNCTYPE(None)
STATE_CB = C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint)


class GameInfo(C.Structure):
    _fields_ = [('path', C.c_char_p), ('data', C.c_void_p), ('size', C.c_size_t), ('meta', C.c_char_p)]


# core options we want instead of the defaults
OPTIONS = {b'pcsx_rearmed_bios': b'auto', b'pcsx_rearmed_frameskip_type': b'disabled',
           b'pcsx_rearmed_memcard1': b'libretro'}


def png(path, width, height, rgb):
    raw = b''.join(b'\0' + rgb[y * width * 3:(y + 1) * width * 3] for y in range(height))

    def chunk(tag, body):
        return struct.pack('>I', len(body)) + tag + body + struct.pack('>I', zlib.crc32(tag + body))
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
                + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))


class Emu:
    def __init__(self, cue):
        self.core = C.CDLL(CORE)
        self.pixfmt = 0  # 0 = 0RGB1555, 1 = XRGB8888, 2 = RGB565
        self.frame = None
        self.pressed = set()
        # strings handed to the core must stay at a fixed address
        self._sysdir = C.create_string_buffer(SYSTEM.encode())
        self._options = {k: C.create_string_buffer(v) for k, v in OPTIONS.items()}
        self._keep = [ENV_CB(self.env), VIDEO_CB(self.video), AUDIO_CB(lambda l, r: None),
                      AUDIO_BATCH_CB(lambda d, n: n), POLL_CB(lambda: None), STATE_CB(self.state)]
        c = self.core
        c.retro_set_environment(self._keep[0])
        c.retro_set_video_refresh(self._keep[1])
        c.retro_set_audio_sample(self._keep[2])
        c.retro_set_audio_sample_batch(self._keep[3])
        c.retro_set_input_poll(self._keep[4])
        c.retro_set_input_state(self._keep[5])
        c.retro_init()
        self._path = C.c_char_p(os.path.abspath(cue).encode())
        info = GameInfo(self._path, None, 0, None)
        c.retro_load_game.argtypes = [C.POINTER(GameInfo)]
        c.retro_load_game.restype = C.c_bool
        if not c.retro_load_game(C.byref(info)):
            raise RuntimeError('core could not load the game')
        c.retro_get_memory_data.restype = C.c_void_p
        c.retro_get_memory_size.restype = C.c_size_t
        c.retro_serialize_size.restype = C.c_size_t
        c.retro_serialize.restype = C.c_bool
        c.retro_unserialize.restype = C.c_bool
        self.ram_ptr = c.retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM)
        self.ram_size = c.retro_get_memory_size(RETRO_MEMORY_SYSTEM_RAM)

    def env(self, cmd, data):
        cmd &= 0xFFFF
        if cmd == 3:  # GET_CAN_DUPE
            C.cast(data, C.POINTER(C.c_bool))[0] = True
            return True
        if cmd in (9, 31):  # GET_SYSTEM_DIRECTORY, GET_SAVE_DIRECTORY
            C.cast(data, C.POINTER(C.c_void_p))[0] = C.addressof(self._sysdir)
            return True
        if cmd == 10:  # SET_PIXEL_FORMAT
            self.pixfmt = C.cast(data, C.POINTER(C.c_int))[0]
            return True
        if cmd == 15:  # GET_VARIABLE
            key = C.cast(data, C.POINTER(C.c_char_p))[0]
            value = self._options.get(key)
            if value is None:
                return False
            C.cast(data, C.POINTER(C.c_void_p))[1] = C.addressof(value)
            return True
        if cmd == 17:  # GET_VARIABLE_UPDATE
            C.cast(data, C.POINTER(C.c_bool))[0] = False
            return True
        if cmd == 52:  # GET_CORE_OPTIONS_VERSION
            C.cast(data, C.POINTER(C.c_uint))[0] = 0
            return True
        return False

    def video(self, data, width, height, pitch):
        if data:  # NULL: same frame as before
            self.frame = (width, height, pitch, C.string_at(data, pitch * height))

    def rgb(self):
        """The last frame as (width, height, RGB bytes)."""
        width, height, pitch, buf = self.frame
        rgb = bytearray(width * height * 3)
        o = 0
        for y in range(height):
            row = buf[y * pitch:y * pitch + pitch]
            if self.pixfmt == 1:
                px = memoryview(row)[:width * 4]
                rgb[o:o + width * 3:3] = px[2::4]
                rgb[o + 1:o + width * 3:3] = px[1::4]
                rgb[o + 2:o + width * 3:3] = px[0::4]
            else:
                for x in range(width):
                    v = row[x * 2] | row[x * 2 + 1] << 8
                    if self.pixfmt == 2:
                        r, g, b = v >> 11, (v >> 5) & 63, v & 31
                        rgb[o + x * 3:o + x * 3 + 3] = bytes((r << 3 | r >> 2, g << 2 | g >> 4, b << 3 | b >> 2))
                    else:
                        r, g, b = (v >> 10) & 31, (v >> 5) & 31, v & 31
                        rgb[o + x * 3:o + x * 3 + 3] = bytes((r << 3 | r >> 2, g << 3 | g >> 2, b << 3 | b >> 2))
            o += width * 3
        return width, height, bytes(rgb)

    def state(self, port, device, index, button):
        return 1 if port == 0 and device == 1 and button in self.pressed else 0

    def run(self, frames):
        for _ in range(frames):
            self.core.retro_run()

    def ram(self):
        return (C.c_ubyte * self.ram_size).from_address(self.ram_ptr)

    def addr(self, a):
        return (a - RAM_BASE if a >= RAM_BASE else a) & 0x1FFFFF

    def save(self, name):
        size = self.core.retro_serialize_size()
        buf = C.create_string_buffer(size)
        if not self.core.retro_serialize(buf, C.c_size_t(size)):
            raise RuntimeError('serialize failed')
        os.makedirs(STATES, exist_ok=True)
        with open(os.path.join(STATES, name + '.state'), 'wb') as f:
            f.write(buf.raw)

    def load(self, name):
        data = open(os.path.join(STATES, name + '.state'), 'rb').read()
        if not self.core.retro_unserialize(C.c_char_p(data), C.c_size_t(len(data))):
            raise RuntimeError('unserialize failed')

    def command(self, line):
        parts = line.split()
        op, args = parts[0], parts[1:]
        if op == 'run':
            self.run(int(args[0]) if args else 1)
        elif op in ('press', 'hold'):
            names = args[0].split('+')
            frames = int(args[1]) if len(args) > 1 else 4
            self.pressed = {BUTTONS[n] for n in names}
            self.run(frames)
            self.pressed = set()
            if op == 'press':
                self.run(8)
        elif op == 'shot':
            w, h, rgb = self.rgb()
            k = int(args[1]) if len(args) > 1 else 1  # nearest-neighbour scale, easier to read
            if k > 1:
                rows = []
                for y in range(h):
                    row = b''.join(rgb[(y * w + x) * 3:(y * w + x) * 3 + 3] * k for x in range(w))
                    rows.extend([row] * k)
                w, h, rgb = w * k, h * k, b''.join(rows)
            png(args[0], w, h, rgb)
            return f'{w}x{h}'
        elif op == 'save':
            self.save(args[0])
        elif op == 'load':
            self.load(args[0])
            self.run(1)
        elif op == 'peek':
            a, n = self.addr(int(args[0], 16)), int(args[1]) if len(args) > 1 else 16
            return bytes(self.ram()[a:a + n]).hex(' ')
        elif op == 'poke':
            a, data = self.addr(int(args[0], 16)), bytes.fromhex(args[1])
            ram = self.ram()
            for i, b in enumerate(data):
                ram[a + i] = b
        elif op == 'find':
            needle = bytes.fromhex(args[0])
            hay = bytes(self.ram())
            out, i = [], hay.find(needle)
            while i != -1 and len(out) < 200:
                out.append(f'{RAM_BASE + i:08x}')
                i = hay.find(needle, i + 1)
            return ' '.join(out)
        elif op == 'card':  # card load|save path: memory card 1 contents (raw 128 KB, DuckStation .mcd)
            size = self.core.retro_get_memory_size(RETRO_MEMORY_SAVE_RAM)
            ptr = self.core.retro_get_memory_data(RETRO_MEMORY_SAVE_RAM)
            if not ptr:
                raise RuntimeError(f'the core exposes no memory card (size {size})')
            card = (C.c_ubyte * size).from_address(ptr)
            if args[0] == 'load':
                data = open(args[1], 'rb').read()[:size]
                C.memmove(card, data, len(data))
            else:
                with open(args[1], 'wb') as f:
                    f.write(bytes(card))
        elif op == 'ramload':  # replace all of RAM with a 2 MB file (e.g. from a DuckStation state)
            data = open(args[0], 'rb').read()[:self.ram_size]
            C.memmove(self.ram(), data, len(data))
        elif op == 'dump':
            with open(args[0], 'wb') as f:
                f.write(bytes(self.ram()))
        elif op == 'seq':
            return '\n'.join(filter(None, (self.command(c.strip()) for c in ' '.join(args).split(','))))
        else:
            raise ValueError(f'unknown command {op}')
        return ''


def serve(cue):
    emu = Emu(cue)
    if os.path.exists(SOCK):
        os.unlink(SOCK)
    srv = socket.socket(socket.AF_UNIX)
    srv.bind(SOCK)
    srv.listen(1)
    print('ready', flush=True)
    while True:
        conn, _ = srv.accept()
        line = conn.recv(65536).decode()
        if line.strip() == 'quit':
            conn.sendall(b'bye')
            conn.close()
            break
        try:
            reply = emu.command(line) or 'ok'
        except Exception as ex:  # report to the client, keep serving
            reply = f'error: {ex}'
        conn.sendall(reply.encode())
        conn.close()
    os.unlink(SOCK)


def send(line):
    s = socket.socket(socket.AF_UNIX)
    s.connect(SOCK)
    s.sendall(line.encode())
    out = b''
    while True:
        chunk = s.recv(65536)
        if not chunk:
            break
        out += chunk
    print(out.decode())


if __name__ == '__main__':
    if sys.argv[1] == 'serve':
        serve(sys.argv[2])
    else:
        send(' '.join(sys.argv[1:]))

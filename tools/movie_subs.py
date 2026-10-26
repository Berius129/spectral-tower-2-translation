"""Replace burned-in Japanese subtitles in STR videos with English ones.

Usage: python3 tools/movie_subs.py "path/to/disc.bin" [MOV03 ...]

Patches the given disc image IN PLACE (run it on the build copy, never on
the original). For each movies/<NAME>.json it:
  1. extracts the video frames with jPSXdec,
  2. erases the Japanese text and draws the English text (ffmpeg drawtext),
     following the original fade in/out (measured from the text brightness),
  3. writes jPSXdec's replace XML and re-encodes those frames into the disc.

Needs Java, jPSXdec and ffmpeg (paths below, override with env variables).
"""
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.join(os.path.dirname(__file__), '..')
MOVIES = os.path.join(ROOT, 'movies')
HOME = os.path.expanduser('~')
JAVA = os.environ.get('JAVA', f'{HOME}/.local/java/Contents/Home/bin/java')
JPSXDEC = os.environ.get('JPSXDEC', f'{HOME}/.local/jpsxdec/jpsxdec_v2.1-beta/jpsxdec.jar')
FFMPEG = os.environ.get('FFMPEG', f'{HOME}/.local/bin/ffmpeg')
FONT = os.environ.get('SUB_FONT', '/System/Library/Fonts/Helvetica.ttc')
FONT_SIZE = 12

W, H = 320, 240
CANVAS_H = 24
# Rows of the original Japanese text and of the strip we redraw, per area.
# Optional keys: "h" (strip height), "font_size", "cols" ([x0, x1], the part
# of the strip that is measured and erased, e.g. to keep a logo), "x" (drawtext
# x expression, centered by default) and "erase": "black" clears the strip
# (text on a black band), "inpaint" only removes the pixels of the Japanese
# text, keeping whatever is drawn around it (e.g. sparks), and "none" leaves
# the picture as is (English added over artwork text that stays) and draws
# the text with a black outline.
AREAS = {
    'bottom': {'text_rows': (211, 227), 'top': 207},
    'middle': {'text_rows': (111, 127), 'top': 107},
}
BLACK_LEVEL = 16
TOLERANCE = 8  # max per-pixel difference still treated as "unchanged" by partial-replace


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, **kw)


def jpsxdec(*args, cwd):
    out = run([JAVA, '-jar', JPSXDEC, *args], cwd=cwd)
    return out.stdout.decode('utf-8', 'replace') + out.stderr.decode('utf-8', 'replace')


def find_item(index_text, file):
    want = file.lstrip('/') + '[0]'
    for line in index_text.splitlines():
        m = re.match(r'#:(\d+)\|ID:([^|]+)\|.*Type:Video', line)
        if m and m.group(2) == want:
            return m.group(1)
    raise ValueError(f'{file}: video not found in index')


def read_frames(pattern, start, count):
    raw = run([FFMPEG, '-v', 'error', '-start_number', str(start), '-i', pattern,
               '-frames:v', str(count), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']).stdout
    size = W * H * 3
    return [bytearray(raw[i * size:(i + 1) * size]) for i in range(len(raw) // size)]


def text_mask(text, tmp, height, font_size, x='(w-tw)/2'):
    """Gray mask of the English text; "\n" starts a new line."""
    path = os.path.join(tmp, 'text.txt')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    vf = (f"drawtext=fontfile='{FONT}':textfile='{path}':fontsize={font_size}:text_align=C:"
          f"line_spacing=3:fontcolor=white:x={x}:y=(h-th)/2")
    return run([FFMPEG, '-v', 'error', '-f', 'lavfi', '-i', f'color=black:s={W}x{height}',
                '-vf', vf, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'gray', '-']).stdout


def text_peak(frame, rows, cols=(16, W - 16)):
    # the darkest channel: the text is white, colored sparks or fog don't count
    return max(min(frame[(y * W + x) * 3:(y * W + x) * 3 + 3]) for y in range(*rows) for x in range(*cols))


def outline(mask, height):
    """The mask grown by one pixel, for a black border around the letters."""
    out = bytearray(len(mask))
    for y in range(height):
        for x in range(W):
            out[y * W + x] = max(mask[yy * W + xx] for yy in range(max(0, y - 1), min(height, y + 2))
                                 for xx in range(max(0, x - 1), min(W, x + 2)))
    return out


def silhouette(frame, rows, threshold, cols=(0, W)):
    """Pixels of the white Japanese text, grown by one pixel."""
    jp = {(x, y) for y in range(*rows) for x in range(*cols)
          if min(frame[(y * W + x) * 3:(y * W + x) * 3 + 3]) > threshold}
    return {(x + dx, y + dy) for x, y in jp for dx in (-1, 0, 1) for dy in (-1, 0, 1)}


def inpaint(frame, pixels):
    """Fill `pixels` ((x, y) set) by interpolating vertically between the
    nearest untouched pixels above and below, column by column."""
    for x in sorted({x for x, _ in pixels}):
        ys = sorted(y for px, y in pixels if px == x)
        runs, start = [], ys[0]
        for a, b in zip(ys, ys[1:] + [None]):
            if b != a + 1:
                runs.append((start, a))
                start = b
        for y0, y1 in runs:
            above, below = max(y0 - 1, 0), min(y1 + 1, H - 1)
            for y in range(y0, y1 + 1):
                t = (y - above) / (below - above)
                for c in range(3):
                    va = frame[(above * W + x) * 3 + c]
                    vb = frame[(below * W + x) * 3 + c]
                    frame[(y * W + x) * 3 + c] = int(va + (vb - va) * t + 0.5)


def patch_movie(disc, name, tmp, index_text):
    cfg = json.load(open(os.path.join(MOVIES, name + '.json'), encoding='utf-8'))
    item = find_item(index_text, cfg['file'])
    frames_dir = os.path.join(tmp, name)
    os.makedirs(frames_dir, exist_ok=True)
    jpsxdec('-x', 'disc.idx', '-f', disc, '-i', item, '-dir', frames_dir, '-vf', 'png', '-noaud', cwd=tmp)
    pngs = sorted(os.path.join(dp, f) for dp, _, fs in os.walk(frames_dir) for f in fs if f.endswith('.png'))
    pattern = re.sub(r'\[(\d+)\]\.png$', lambda m: '[%0' + str(len(m.group(1))) + 'd].png', pngs[0])

    out_dir = os.path.join(tmp, name + '_out')
    os.makedirs(out_dir, exist_ok=True)
    replaced, edited = [], {}
    for sub in cfg['subtitles']:
        # a movie can move an area or add its own, e.g. {"areas": {"bottom": {"text_rows": [204, 220], "top": 200}}}
        area = {**AREAS.get(sub['area'], {}), **cfg.get('areas', {}).get(sub['area'], {})}
        top, height = area['top'], area.get('h', CANVAS_H)
        cols = area.get('cols', (0, W))
        mask = text_mask(sub['text'], tmp, height, area.get('font_size', FONT_SIZE), area.get('x', '(w-tw)/2'))
        erase = area.get('erase', 'black')
        border = outline(mask, height) if erase == 'none' else None
        bg = sub.get('background')
        last = sub['end']
        frames = read_frames(pattern, sub['start'], last - sub['start'] + 1)
        # subtitles may overlap (two lines appearing one after the other):
        # build on the frames already edited
        for k in range(len(frames)):
            if sub['start'] + k in edited:
                frames[k] = bytearray(edited[sub['start'] + k])
        # text opacity follows the brightness of the original Japanese text
        if 'fade' not in sub:
            alphas = [max(0.0, min(1.0, (text_peak(f, area['text_rows'], area.get('cols', (16, W - 16)))
                                         - BLACK_LEVEL) / (255 - BLACK_LEVEL))) for f in frames]
        # text added where the original has none (e.g. under artwork titles):
        # fixed fade in/out of the given number of frames
        if 'fade' in sub:
            fin, fout = sub['fade']
            alphas = [min(1.0, (k + 1) / (fin + 1), (len(frames) - k) / (fout + 1)) for k in range(len(frames))]
        # where the picture fades in behind the text, brightness can't be
        # measured: fade the text out linearly instead
        if bg:
            i0 = bg['from'] - sub['start']
            start_alpha = alphas[i0 - 1] if i0 > 0 else 1.0
            span = bg['fade_out_end'] - bg['from'] + 1
            for k in range(i0, len(frames)):
                alphas[k] = max(0.0, start_alpha * (1 - (k - i0 + 1) / span))
            # silhouette of the Japanese text, from a frame well before the
            # picture starts fading in (background still pure black), grown by one pixel
            jp = silhouette(frames[max(0, i0 - 10)], (top, top + height), 30)
        elif erase == 'inpaint':
            # the text doesn't move: take its shape from its brightest frame,
            # or from a given one (e.g. where the picture behind it is black)
            if 'silhouette_frame' in sub:
                ref = read_frames(pattern, sub['silhouette_frame'], 1)[0]
            else:
                ref = frames[max(range(len(frames)), key=alphas.__getitem__)]
            jp = silhouette(ref, area['text_rows'], 40, cols)

        for k, frame in enumerate(frames):
            n = sub['start'] + k
            a = alphas[k]
            behind = erase != 'black' or (bg and n >= bg['from'])
            if erase == 'inpaint' or (bg and n >= bg['from']):
                inpaint(frame, jp)
            for y in range(height):
                fy = top + y
                for x in range(W):
                    i = (fy * W + x) * 3
                    m = mask[y * W + x] / 255 * a
                    o = border[y * W + x] / 255 * a if border else 0
                    keep = behind or not cols[0] <= x < cols[1]
                    for c in range(3):
                        base = frame[i + c] * (1 - o) if keep else 0  # on black: clear the strip
                        frame[i + c] = int(base * (1 - m) + 255 * m + 0.5)
            path = os.path.join(out_dir, f'{n:04d}.png')
            run([FFMPEG, '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                 '-i', '-', path], input=bytes(frame))
            replaced.append((n, path, sub.get('encode') == 'full'))
            edited[n] = bytes(frame)

    xml = os.path.join(tmp, name + '.xml')
    with open(xml, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<str-replace version="0.3">\n')
        # partial-replace only re-encodes the macroblocks that differ from the
        # original frame, so the rest of the picture keeps its original data
        # "encode": "full" re-encodes the whole frame instead: needed where a
        # busy picture leaves no bits for new text (it shows as gray blocks)
        for n, (path, full) in sorted({n: (path, full) for n, path, full in replaced}.items()):
            if full:
                f.write(f'  <replace frame="{n}">{path}</replace>\n')
            else:
                f.write(f'  <partial-replace frame="{n}" tolerance="{TOLERANCE}">{path}</partial-replace>\n')
        f.write('</str-replace>\n')
    log = jpsxdec('-x', 'disc.idx', '-f', disc, '-i', item, '-replaceframes', xml, cwd=tmp)
    return len({n for n, _, _ in replaced}), log


def main(disc, names):
    names = names or sorted(f[:-5] for f in os.listdir(MOVIES) if f.endswith('.json'))
    with tempfile.TemporaryDirectory() as tmp:
        jpsxdec('-f', disc, '-x', 'disc.idx', cwd=tmp)
        index_text = open(os.path.join(tmp, 'disc.idx'), encoding='utf-8', errors='replace').read()
        for name in names:
            count, log = patch_movie(disc, name, tmp, index_text)
            print(f'{name}: {count} frames replaced')
            for line in log.splitlines():
                if re.search(r'(?i)error|warn|fail|exceed', line):
                    print('   ', line)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])

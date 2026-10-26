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
# Rows of the original Japanese text and of the strip we redraw, per area
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


def text_mask(text, tmp):
    path = os.path.join(tmp, 'text.txt')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    vf = (f"drawtext=fontfile='{FONT}':textfile='{path}':fontsize={FONT_SIZE}:"
          f"fontcolor=white:x=(w-tw)/2:y=(h-th)/2")
    return run([FFMPEG, '-v', 'error', '-f', 'lavfi', '-i', f'color=black:s={W}x{CANVAS_H}',
                '-vf', vf, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'gray', '-']).stdout


def text_peak(frame, rows):
    return max(max(frame[(y * W + x) * 3:(y * W + x) * 3 + 3]) for y in range(*rows) for x in range(16, W - 16))


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
    replaced = []
    for sub in cfg['subtitles']:
        # a movie can move an area, e.g. {"areas": {"bottom": {"text_rows": [204, 220], "top": 200}}}
        area = {**AREAS[sub['area']], **cfg.get('areas', {}).get(sub['area'], {})}
        top = area['top']
        mask = text_mask(sub['text'], tmp)
        bg = sub.get('background')
        last = sub['end']
        frames = read_frames(pattern, sub['start'], last - sub['start'] + 1)
        clean = read_frames(pattern, bg['clean_frame'], 1)[0] if bg else None
        # text opacity follows the brightness of the original Japanese text
        alphas = [max(0.0, min(1.0, (text_peak(f, area['text_rows']) - BLACK_LEVEL) / (255 - BLACK_LEVEL)))
                  for f in frames]
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
            ref = frames[max(0, i0 - 10)]
            jp = {(x, y) for y in range(top, top + CANVAS_H) for x in range(W)
                  if max(ref[(y * W + x) * 3:(y * W + x) * 3 + 3]) > 30}
            jp |= {(x + dx, y + dy) for x, y in jp for dx in (-1, 0, 1) for dy in (-1, 0, 1)}

        for k, frame in enumerate(frames):
            n = sub['start'] + k
            a = alphas[k]
            behind = bg and n >= bg['from']
            if behind:
                inpaint(frame, jp)
            for y in range(CANVAS_H):
                fy = top + y
                for x in range(W):
                    i = (fy * W + x) * 3
                    m = mask[y * W + x] / 255 * a
                    for c in range(3):
                        base = frame[i + c] if behind else 0  # on black: clear the strip
                        frame[i + c] = int(base * (1 - m) + 255 * m + 0.5)
            path = os.path.join(out_dir, f'{n:04d}.png')
            run([FFMPEG, '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                 '-i', '-', path], input=bytes(frame))
            replaced.append((n, path))

    xml = os.path.join(tmp, name + '.xml')
    with open(xml, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<str-replace version="0.3">\n')
        # partial-replace only re-encodes the macroblocks that differ from the
        # original frame, so the rest of the picture keeps its original data
        for n, path in replaced:
            f.write(f'  <partial-replace frame="{n}" tolerance="{TOLERANCE}">{path}</partial-replace>\n')
        f.write('</str-replace>\n')
    log = jpsxdec('-x', 'disc.idx', '-f', disc, '-i', item, '-replaceframes', xml, cwd=tmp)
    return len(replaced), log


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

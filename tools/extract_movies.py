"""Extract MOVIE/*.STR videos as raw 2352-byte sectors, the layout ffmpeg's
PlayStation STR demuxer reads (video in Form 1 sectors, XA audio in Form 2).

Usage: python3 tools/extract_movies.py "path/to/disc.bin" OUT_DIR [name ...]
Then, for example: ffmpeg -i OUT_DIR/MOV00.STR MOV00.mp4
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import psxiso


def main(bin_path, out_dir, names):
    img = psxiso.Image(bin_path)
    os.makedirs(out_dir, exist_ok=True)
    for path, (lba, size, *_) in sorted(img.files.items()):
        name = path.rsplit('/', 1)[1]
        if not path.startswith('/MOVIE/') or (names and name.split('.')[0] not in names):
            continue
        sectors = (size + psxiso.DATA - 1) // psxiso.DATA
        img.f.seek(lba * psxiso.SECTOR)
        with open(os.path.join(out_dir, name), 'wb') as out:
            out.write(img.f.read(sectors * psxiso.SECTOR))
        print(f'{name}: {sectors} sectors')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3:])

# Spectral Tower II — English Translation

Fan translation of *Spectral Tower II* (PlayStation, Idea Factory, 1998, SLPS-01179) from Japanese to English.

You need your own copy of the Japanese disc as `.bin/.cue` (one MODE2/2352 track). This repo never contains disc images.

## Requirements

- Python 3 (no extra packages)

## Workflow

1. **Extract the text** (only needed once, or after tool changes; existing translations are kept):
   ```
   python3 tools/dump_text.py "path/to/Spectral Tower II (Japan).bin"
   ```
2. **Translate**: edit the `en` field in the `script/**/*.json` files. Leave `en` empty to keep the Japanese line.
3. **Build** a translated copy (the original is not modified):
   ```
   python3 tools/build.py "path/to/Spectral Tower II (Japan).bin"
   ```
   Output: `build/Spectral Tower II (English).bin/.cue`. Add `--fullwidth` to convert English to full-width characters (ＡＢＣ) while the font question is open.
4. Test in an emulator (DuckStation recommended).

## Text format

Text files on the disc are Shift-JIS (cp932) with every byte XOR'd with `0xFF`, one entry per CRLF line. Control codes must be kept as-is:

| Code | Meaning |
|---|---|
| `￥ｎ` | line break |
| `(B)` | wait for button |
| `(E)` | end of message |
| `(9)`, other `(..)` | variables / effects (to be documented) |

Lines may start with a label such as `TALK0:`; keep it.

Translated files are patched in place, so each file must still fit in its original sectors. `build.py` reports any file that doesn't fit.

## Status

- [x] Disc reading/patching with EDC/ECC (`tools/psxiso.py`)
- [x] Extraction and reinsertion of text files (~2,800 lines, 351 files)
- [ ] Check if the font can display narrow ASCII, or add a variable-width font
- [ ] Strings inside the executable `SLPS_011.79` (~1,100 strings, plain Shift-JIS)
- [ ] Check for fixed-length fields in `ITEM` and `ROOTSDAT` files
- [ ] Graphics with text (`COMMON/*.TIM`: title, names, save screen)
- [ ] Videos (`MOVIE/*.STR`)
- [ ] Translation
- [ ] Distribute as an xdelta patch

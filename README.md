# Spectral Tower II — English Translation Patch (PS1)

English fan translation patch for *Spectral Tower II* (スペクトラルタワーII, PlayStation, Idea Factory, 1998, SLPS-01179), translated from Japanese to English: menus, items, skills, Roots, dialogue, events and the subtitled videos.

**Download:** [Releases page](https://github.com/Berius129/spectral-tower-2-translation/releases) (latest: v0.2.0 beta) — an xdelta patch for your own Japanese disc image, with instructions.

[![Donate with PayPal](https://img.shields.io/badge/Donate-PayPal-0070ba?logo=paypal&logoColor=white)](https://www.paypal.com/ncp/payment/SLW4WJCZ2HKF6)

If you enjoy the translation and want to support it, you can donate through PayPal. It's entirely optional.

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
   Output: `build/Spectral Tower II (English).bin/.cue`. English is encoded with DTE (see below); `--fullwidth` uses full-width characters (ＡＢＣ) instead.
4. Test in an emulator (DuckStation recommended).
5. **Make the patch** for distribution:
   ```
   python3 tools/make_patch.py "path/to/Spectral Tower II (Japan).bin" "build/Spectral Tower II (English).bin" "build/Spectral Tower II (English).xdelta"
   ```
   Writes an xdelta/VCDIFF patch (no external tools needed) with xdelta3's per-window Adler-32 checksums, and checks it by applying it. v0.2.0 was also verified with the official xdelta3 3.2.1, which rejects a wrong source image. Ship it with [docs/PATCH_README.txt](docs/PATCH_README.txt) (player instructions and disc checksums) and a `.cue` for the patched `.bin`.

## Status: v0.2.0 beta

All text is translated, but it has had little testing in game. Expect cut-off or untranslated text in places that haven't been seen yet.

Testing progress: **44%** — see [docs/TESTING.md](docs/TESTING.md) for what has been checked and what is pending.

## Root codes

[docs/ROOTS.md](docs/ROOTS.md) lists all 140 Roots with the code to enter at the Tree of Destiny, regenerated with `python3 tools/roots_table.py "<disc.bin>"`.

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

## Executable strings

Menus, battle and system messages are in `script/SLPS_011.79.json`. Each entry has the string's file `offset` and `max`, the number of bytes available (the original string plus its NUL padding). With DTE, two English letters take 2 bytes, the same as one Japanese character, so English can be roughly twice as long in letters as the Japanese is in characters. `%s` inserts a name or number; keep it. Entries marked `locked` share bytes with another string and can't be translated yet.

## Font and DTE

The game only draws 2-byte Shift-JIS characters, so plain ASCII shows garbage. Its font is in `SLPS_011.79`: 1bpp glyphs of 16×11 pixels, 22 bytes each, MSB = leftmost pixel.

| Table | RAM | File offset | Codes |
|---|---|---|---|
| Symbols, kana, full-width letters | `0x800B9AA4` | `0xAA2A4` | `0x8140`–`0x84BE` |
| Kanji (JIS level 1) | `0x800BC7AC` | `0xACFAC` | `0x889F`–`0x9872` |

Glyph lookup: `0x80021ACC`; code → index: `0x80021E48`.

`build.py` splits English text into letter pairs, gives each distinct pair a kanji code and draws the pair into that kanji's glyph using `tools/font_5x9.txt` (editable). Kanji still needed by untranslated Japanese text are used last. One character cell holds two letters, so a dialogue line fits about 32 letters; `build.py` warns when a line is longer than the window.

The pair → code assignments are kept in `tools/dte_table.json`, and `build.py` only adds new pairs to it. Pairs never change code, because the game saves the names of companions that join the party as these codes: a different table would garble them in existing save files. Commit the file after each build that adds pairs.

Line labels (`TALK0:`, `ALL,`, `30:0,`…), control codes (`(B)`, `(E)`, `(F1)`, `(ON030:1)`…), `￥ｎ` and choice markers (`=CP1,`) stay as ASCII. Avoid parentheses around letters/digits in English text, since `(word)` looks like a control code.

## Status

- [x] Disc reading/patching with EDC/ECC (`tools/psxiso.py`)
- [x] Extraction and reinsertion of text files (~2,800 lines, 351 files)
- [x] Font: DTE letter pairs (`tools/dte.py`, `tools/font_5x9.txt`)
- [ ] Confirm DTE spacing in the emulator; consider variable-width font later
- [x] Strings inside the executable (`tools/exestrings.py` → `script/SLPS_011.79.json`, 1,014 strings)
- [ ] 15 executable strings marked `locked` (another pointer points into them)
- [ ] Check for fixed-length fields in `ITEM` and `ROOTSDAT` files
- [ ] Graphics with text (`COMMON/*.TIM`: title, names, save screen)
- [x] Videos (`MOVIE/*.STR`): no voices, burned-in subtitles in MOV01, MOV03, MOV05, MOV09 (MOV08 credits are
      already English). Each video has a `movies/<NAME>.json` with frame ranges and English text;
      `tools/movie_subs.py` erases the Japanese, draws the English with the original fades and re-encodes
      only the changed macroblocks with jPSXdec (`partial-replace`). Big artwork text (kanji titles, the
      trailer's captions) stays and gets an English line with a black outline; those frames are re-encoded
      whole (`"encode": "full"`) so the new text doesn't turn into gray blocks. `build.py` runs it when
      Java, jPSXdec and ffmpeg are in `~/.local` (`--no-movies` skips it).
- [ ] Translation
- [x] Distribute as an xdelta patch (v0.2.0 beta, `tools/make_patch.py`)

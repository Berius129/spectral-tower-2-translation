Spectral Tower II - English fan translation
Version 1.0.0
===========================================

All of the game's text has been translated and played through in an
emulator: every event floor, the ending, menus, battles and all the
subtitled videos. If you find anything strange (cut-off text, odd
wording, a bug), please report it; a screenshot helps a lot.

Known issues:
- Not tested yet: the paralysis message in battle, fleeing (the Flee
  skill), and memory card formatting/error messages.
- The big artwork titles in the videos stay in Japanese; the English
  appears as a subtitle line.


What you need
-------------
Your own copy of the Japanese disc as a single-track BIN/CUE
(MODE2/2352), "Spectral Tower II (Japan)" (SLPS-01179):

  Size   557,191,152 bytes
  MD5    021e3e7b239c9313c7108db3b8dad886
  SHA-1  a05becd8c5ab36d0df3ec3e676359965a06ec1c0

No game data is included in this patch.


How to patch
------------
1. Apply "Spectral Tower II (English) v1.0.0.xdelta" to the Japanese
   .bin with any xdelta patcher, for example:
     - Rom Patcher JS (in the browser)
     - Delta Patcher or xdelta UI
     - command line: xdelta3 -d -s "Spectral Tower II (Japan).bin"
       "Spectral Tower II (English) v1.0.0.xdelta"
       "Spectral Tower II (English).bin"
2. Name the result "Spectral Tower II (English).bin" and put it next to
   the included "Spectral Tower II (English).cue".
3. Open the .cue in your emulator (tested in DuckStation).

The patched image should match:
  MD5    45f2edfa4cb6674734e4d93e5c3d8b91
  SHA-1  87cd75df65523cf337733c4ce96a5cea47a9ae8a


About the translation
---------------------
The game can only draw Japanese characters, so English letters are drawn
two at a time into unused kanji of the font (DTE). Menus, items, skills,
Roots, mail, dialogue, events and the subtitled videos are translated.


Changes
-------
1.0.0
- Name entry: letters centered in their cells, the 終 button now reads
  END, and the cursor above the name follows the letters you type.

0.3.0
- Choice menus: 44 menus had options wider than the original and the
  box could run off the screen (e.g. Dragonfolk Town); all shortened.
- Floor 4 (Battle Master's apprentice), floor 5500 (penguins) and one
  mail: words in parentheses showed as garbage; fixed.
- Ending: a line overflowed into other text; fixed.

0.2.0
- Battle: the element wheel labels no longer cover the orbs (Brwl, Swrd,
  Void, Pray...), shorter help text, "Wave acts" instead of "Wave's act".
- Settings: window brightness option and its "Current" value now match.
- New game: clearer prompt for renaming the adventurers.

0.1 beta
- First release: all text, the Roots/skills/item tables, menus, name
  entry, Belacus destinations and the four subtitled videos.

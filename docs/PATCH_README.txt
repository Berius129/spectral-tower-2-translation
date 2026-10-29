Spectral Tower II - English fan translation
Version 0.3.0 BETA
===========================================

THIS IS A BETA. All of the game's text has been translated and about
93% of the game has been tested, including every event floor, the
ending and all subtitled videos. Expect untranslated bits,
text cut off or overflowing its window, odd wording, and possibly bugs.
Keep backups of your saves, and please report anything strange (a
screenshot helps a lot).

Known issues:
- Not tested yet: shops, reading a mail, status effects (paralysis,
  sickness, curse), fleeing, renaming the adventurers, and memory
  card formatting/errors.
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
1. Apply "Spectral Tower II (English) v0.3.0 beta.xdelta" to the Japanese
   .bin with any xdelta patcher, for example:
     - Rom Patcher JS (in the browser)
     - Delta Patcher or xdelta UI
     - command line: xdelta3 -d -s "Spectral Tower II (Japan).bin"
       "Spectral Tower II (English) v0.3.0 beta.xdelta"
       "Spectral Tower II (English).bin"
2. Name the result "Spectral Tower II (English).bin" and put it next to
   the included "Spectral Tower II (English).cue".
3. Open the .cue in your emulator (tested in DuckStation).

The patched image should match:
  MD5    4e814914c2c4cc41807513a7c2be6df7
  SHA-1  ca4be5dce2eb14f878a22d45cc9acd49e8aa48a1


About the translation
---------------------
The game can only draw Japanese characters, so English letters are drawn
two at a time into unused kanji of the font (DTE). Menus, items, skills,
Roots, mail, dialogue, events and the subtitled videos are translated.


Changes
-------
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

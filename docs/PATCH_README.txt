Spectral Tower II - English fan translation
Version 0.1 BETA
===========================================

THIS IS A BETA. All of the game's text has been translated, but the
translation has had very little testing. Expect untranslated bits,
text cut off or overflowing its window, odd wording, and possibly bugs.
Keep backups of your saves, and please report anything strange (a
screenshot helps a lot).

Known issues:
- Not every screen, event or ending has been seen in game yet.
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
1. Apply "Spectral Tower II (English) v0.1 beta.xdelta" to the Japanese
   .bin with any xdelta patcher, for example:
     - Rom Patcher JS (in the browser)
     - Delta Patcher or xdelta UI
     - command line: xdelta3 -d -s "Spectral Tower II (Japan).bin"
       "Spectral Tower II (English) v0.1 beta.xdelta"
       "Spectral Tower II (English).bin"
2. Name the result "Spectral Tower II (English).bin" and put it next to
   the included "Spectral Tower II (English).cue".
3. Open the .cue in your emulator (tested in DuckStation).

The patched image should match:
  MD5    e187eeddcb42a667377de0d67448f55d
  SHA-1  446fc3bf486a856efb6787036f5db599ae0058a4


About the translation
---------------------
The game can only draw Japanese characters, so English letters are drawn
two at a time into unused kanji of the font (DTE). Menus, items, skills,
Roots, mail, dialogue, events and the subtitled videos are translated.

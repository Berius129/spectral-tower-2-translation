# Testing status

**94% tested** (70.5 of 75 checks; a partial check counts as half).

The translation is a beta: all text is translated, but most of it has not been seen in game yet.

✅ tested, fine · 🔧 issue found and fixed · 🟨 partly tested · ⬜ not tested

Tested by: **user** (playing in DuckStation), **auto** (screenshots from `tools/emu.py`), **frames** (video frames checked one by one).

Regenerate this file with `python3 tools/testing_status.py` after updating the list in it.

## System and menus (20.5/22)

| | Check | By | Notes |
|---|---|---|---|
| ✅ | Title screen and main menu | auto |  |
| 🔧 | Hero name entry (ABC/abc panels) | user, auto | display blocks and input tables now match |
| 🟨 | Rename the 5 male/female adventurers | auto | prompt fixed; the renaming itself not tried |
| ✅ | Memory card: load | auto |  |
| 🟨 | Memory card: save, format, errors | auto | save and overwrite seen; format/errors not |
| ✅ | Item list and descriptions | user, auto |  |
| 🔧 | Item actions: use, equip, eat, drop | user, auto | drop/eat prompts restructured; eating bread, herb, wand, rusty armor, Abyss Blade checked |
| ✅ | Status page | auto |  |
| ✅ | Roots Discovered list | auto |  |
| 🔧 | Mastered Root Skills | user, auto | skill type, target and requirement tables |
| ✅ | Root details page | auto |  |
| 🔧 | Companion page | user, auto | DTE table pinned so saved names keep working |
| 🔧 | Settings and submenus | user, auto |  |
| 🔧 | Belacus destinations | user, auto |  |
| 🔧 | Chest screen | user |  |
| 🔧 | Floor clear bonus | user |  |
| 🔧 | Tree of Destiny: menu, heal, Root code entry | user, auto |  |
| ✅ | Mail notice | auto |  |
| 🟨 | Reading mail | auto | only 'There is no mail for you.' seen |
| ✅ | Shops (merchants met in the tower) | user | the only shops in the game; Junk Town trading checked with floor 501 |
| ✅ | Saving the game | auto | Tree of Destiny: save, overwrite prompt |
| ✅ | Death / game over | auto | Out of HP..., Game Over |

## Battle (5/8)

| | Check | By | Notes |
|---|---|---|---|
| 🔧 | Element wheel and help text | user, auto | labels now fit 2 cells like the original |
| ✅ | Skill list, descriptions, cost | auto | compared with the original disc |
| 🔧 | Turn and hit messages, victory | auto | 'acts' |
| ✅ | Sickness and curse (affect end-of-floor points) | user |  |
| ⬜ | Paralysis in battle |  |  |
| 🟨 | Stat gains, training messages | user |  |
| ⬜ | Fleeing |  |  |
| 🟨 | Adventurers asking to join | user |  |

## Videos (4/4)

| | Check | By | Notes |
|---|---|---|---|
| ✅ | MOV01 opening narration | frames, auto | seen in game |
| ✅ | MOV03 goblin scene (floor 6) | frames, user |  |
| ✅ | MOV05 rival scene | frames, user |  |
| ✅ | MOV09 trailer (title screen demo) | frames, user |  |

## Story (3/3)

| | Check | By | Notes |
|---|---|---|---|
| 🔧 | Intro scene after the opening video | user |  |
| ✅ | Destiny Town dialogue | user, auto |  |
| 🔧 | Choosing the first Root | user |  |

## Event floors (38/38)

| | Check | By | Notes |
|---|---|---|---|
| ✅ | Floor 1 | user | training master |
| 🔧 | Floor 4 | user | stats expert |
| ✅ | Floor 6 | user | dwarf murder, rival |
| ✅ | Floor 10 | user | rescued adventurer |
| ✅ | Floor 16 | user | tourists |
| ✅ | Floor 22 | user | stood-up woman |
| ✅ | Floor 30 | user | rescued adventurer |
| ✅ | Floor 40 | user | father and son |
| ✅ | Floor 60 | user | Devil Mansion |
| ✅ | Floor 101 | user | Tranquil Town |
| ✅ | Floor 150 | user | zombie |
| ✅ | Floor 200 | user | Chile |
| ✅ | Floor 290 | user | toll house |
| ✅ | Floor 298 | user | Gambling Town |
| ✅ | Floor 399 | user | widow |
| ✅ | Floor 450 | user | Mute Temple |
| ✅ | Floor 501 | user | Junk Town |
| ✅ | Floor 650 | user | staring |
| ✅ | Floor 770 | user | bridge guard |
| ✅ | Floor 1000 | user | rival, Emperor Dragon |
| ✅ | Floor 1001 | user | after the Emperor Dragon |
| ✅ | Floor 1105 | user | rival |
| ✅ | Floor 1200 | user | dragon |
| ✅ | Floor 1500 | user | dragon |
| ✅ | Floor 1900 | user | dragon |
| ✅ | Floor 2500 | user | dragon |
| ✅ | Floor 3200 | user | dragon |
| ✅ | Floor 4000 | user | dragon |
| ✅ | Floor 5000 | user | dragon |
| ✅ | Floor 5500 | user | penguin family |
| ✅ | Floor 6200 | user | old foe |
| ✅ | Floor 6500 | user | rival |
| ✅ | Floor 6900 | user | old foe |
| ✅ | Floor 7500 | user | old foe |
| ✅ | Floor 8200 | user | guardian |
| ✅ | Floor 9000 | user | guardian |
| 🔧 | Floor 9999 | user | Dragonfolk Town |
| 🔧 | Floor 10000 | user | ending |

## Pending

- Event floors not marked above, including the story from floor 1000 and the ending.
- Reading an actual mail, paralysis in battle, fleeing.

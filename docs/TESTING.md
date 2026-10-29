# Testing status

**64% tested** (47.5 of 74 checks; a partial check counts as half).

The translation is a beta: all text is translated, but most of it has not been seen in game yet.

✅ tested, fine · 🔧 issue found and fixed · 🟨 partly tested · ⬜ not tested

Tested by: **user** (playing in DuckStation), **auto** (screenshots from `tools/emu.py`), **frames** (video frames checked one by one).

Regenerate this file with `python3 tools/testing_status.py` after updating the list in it.

## System and menus (19.5/22)

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
| ⬜ | Shops |  |  |
| ✅ | Saving the game | auto | Tree of Destiny: save, overwrite prompt |
| ✅ | Death / game over | auto | Out of HP..., Game Over |

## Battle (4/7)

| | Check | By | Notes |
|---|---|---|---|
| 🔧 | Element wheel and help text | user, auto | labels now fit 2 cells like the original |
| ✅ | Skill list, descriptions, cost | auto | compared with the original disc |
| 🔧 | Turn and hit messages, victory | auto | 'acts' |
| ⬜ | Status effects (paralysis, sickness, curse) |  |  |
| 🟨 | Stat gains, training messages | user |  |
| ⬜ | Fleeing |  |  |
| 🟨 | Adventurers asking to join | user |  |

## Videos (4/4)

| | Check | By | Notes |
|---|---|---|---|
| ✅ | MOV01 opening narration | frames, auto | seen in game |
| ✅ | MOV03 goblin scene (floor 6) | frames, user |  |
| ✅ | MOV05 rival scene | frames | not yet seen in game |
| ✅ | MOV09 trailer (title screen demo) | frames | not yet seen in game |

## Story (3/3)

| | Check | By | Notes |
|---|---|---|---|
| 🔧 | Intro scene after the opening video | user |  |
| ✅ | Destiny Town dialogue | user, auto |  |
| 🔧 | Choosing the first Root | user |  |

## Event floors (17/38)

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
| ⬜ | Floor 650 |  | staring |
| ⬜ | Floor 770 |  | bridge guard |
| ⬜ | Floor 1000 |  | rival, Emperor Dragon |
| ⬜ | Floor 1001 |  | after the Emperor Dragon |
| ⬜ | Floor 1105 |  | rival |
| ⬜ | Floor 1200 |  | dragon |
| ⬜ | Floor 1500 |  | dragon |
| ⬜ | Floor 1900 |  | dragon |
| ⬜ | Floor 2500 |  | dragon |
| ⬜ | Floor 3200 |  | dragon |
| ⬜ | Floor 4000 |  | dragon |
| ⬜ | Floor 5000 |  | dragon |
| ⬜ | Floor 5500 |  | penguin family |
| ⬜ | Floor 6200 |  | old foe |
| ⬜ | Floor 6500 |  | rival |
| ⬜ | Floor 6900 |  | old foe |
| ⬜ | Floor 7500 |  | old foe |
| ⬜ | Floor 8200 |  | guardian |
| ⬜ | Floor 9000 |  | guardian |
| ⬜ | Floor 9999 |  | Dragonfolk Town |
| ⬜ | Floor 10000 |  | ending |

## Pending

- Event floors not marked above, including the story from floor 1000 and the ending.
- Shops, reading an actual mail, status effects, fleeing.
- MOV05 and MOV09 inside the game.

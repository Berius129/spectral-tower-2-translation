"""Write docs/TESTING.md from the checklist below and print the progress.

Status: 'ok' tested and fine, 'fixed' an issue was found and fixed (and
re-checked), 'partial' only part of it was seen, 'todo' not tested yet.
By: 'user' (played in DuckStation), 'auto' (tools/emu.py screenshots),
'frames' (video frames checked one by one).
"""
import os

# event floors checked in game by the user, and those where an issue was fixed
USER_FLOORS = {1, 4, 6, 10, 16, 22, 30, 40, 60, 101, 150, 200, 290, 298, 399, 450, 501, 650, 770, 1000, 1001, 1105}
FIXED_FLOORS = {4}

CHECKS = [
    ('System and menus', [
        ('Title screen and main menu', 'ok', 'auto', ''),
        ('Hero name entry (ABC/abc panels)', 'fixed', 'user, auto', 'display blocks and input tables now match'),
        ('Rename the 5 male/female adventurers', 'partial', 'auto', 'prompt fixed; the renaming itself not tried'),
        ('Memory card: load', 'ok', 'auto', ''),
        ('Memory card: save, format, errors', 'partial', 'auto', 'save and overwrite seen; format/errors not'),
        ('Item list and descriptions', 'ok', 'user, auto', ''),
        ('Item actions: use, equip, eat, drop', 'fixed', 'user, auto', 'drop/eat prompts restructured; eating bread, herb, wand, rusty armor, Abyss Blade checked'),
        ('Status page', 'ok', 'auto', ''),
        ('Roots Discovered list', 'ok', 'auto', ''),
        ('Mastered Root Skills', 'fixed', 'user, auto', 'skill type, target and requirement tables'),
        ('Root details page', 'ok', 'auto', ''),
        ('Companion page', 'fixed', 'user, auto', 'DTE table pinned so saved names keep working'),
        ('Settings and submenus', 'fixed', 'user, auto', ''),
        ('Belacus destinations', 'fixed', 'user, auto', ''),
        ('Chest screen', 'fixed', 'user', ''),
        ('Floor clear bonus', 'fixed', 'user', ''),
        ('Tree of Destiny: menu, heal, Root code entry', 'fixed', 'user, auto', ''),
        ('Mail notice', 'ok', 'auto', ''),
        ('Reading mail', 'partial', 'auto', "only 'There is no mail for you.' seen"),
        ('Shops', 'todo', '', ''),
        ('Saving the game', 'ok', 'auto', 'Tree of Destiny: save, overwrite prompt'),
        ('Death / game over', 'ok', 'auto', 'Out of HP..., Game Over'),
    ]),
    ('Battle', [
        ('Element wheel and help text', 'fixed', 'user, auto', 'labels now fit 2 cells like the original'),
        ('Skill list, descriptions, cost', 'ok', 'auto', 'compared with the original disc'),
        ('Turn and hit messages, victory', 'fixed', 'auto', "'acts'"),
        ('Status effects (paralysis, sickness, curse)', 'todo', '', ''),
        ('Stat gains, training messages', 'partial', 'user', ''),
        ('Fleeing', 'todo', '', ''),
        ('Adventurers asking to join', 'partial', 'user', ''),
    ]),
    ('Videos', [
        ('MOV01 opening narration', 'ok', 'frames, auto', 'seen in game'),
        ('MOV03 goblin scene (floor 6)', 'ok', 'frames, user', ''),
        ('MOV05 rival scene', 'ok', 'frames', 'not yet seen in game'),
        ('MOV09 trailer (title screen demo)', 'ok', 'frames', 'not yet seen in game'),
    ]),
    ('Story', [
        ('Intro scene after the opening video', 'fixed', 'user', ''),
        ('Destiny Town dialogue', 'ok', 'user, auto', ''),
        ('Choosing the first Root', 'fixed', 'user', ''),
    ]),
    ('Event floors', [(f'Floor {f}', 'fixed' if f in FIXED_FLOORS else 'ok' if f in USER_FLOORS else 'todo', 'user' if f in USER_FLOORS else '', note) for f, note in [
        (1, 'training master'), (4, 'stats expert'), (6, 'dwarf murder, rival'), (10, 'rescued adventurer'),
        (16, 'tourists'), (22, 'stood-up woman'), (30, 'rescued adventurer'), (40, 'father and son'),
        (60, 'Devil Mansion'), (101, 'Tranquil Town'), (150, 'zombie'), (200, 'Chile'), (290, 'toll house'),
        (298, 'Gambling Town'), (399, 'widow'), (450, 'Mute Temple'), (501, 'Junk Town'), (650, 'staring'),
        (770, 'bridge guard'), (1000, 'rival, Emperor Dragon'), (1001, 'after the Emperor Dragon'),
        (1105, 'rival'), (1200, 'dragon'), (1500, 'dragon'), (1900, 'dragon'), (2500, 'dragon'),
        (3200, 'dragon'), (4000, 'dragon'), (5000, 'dragon'), (5500, 'penguin family'), (6200, 'old foe'),
        (6500, 'rival'), (6900, 'old foe'), (7500, 'old foe'), (8200, 'guardian'), (9000, 'guardian'),
        (9999, 'Dragonfolk Town'), (10000, 'ending')]]),
]

MARK = {'ok': '✅', 'fixed': '🔧', 'partial': '🟨', 'todo': '⬜'}
DONE = {'ok': 1, 'fixed': 1, 'partial': 0.5, 'todo': 0}


def progress():
    items = [c for _, group in CHECKS for c in group]
    return sum(DONE[c[1]] for c in items), len(items)


def main():
    done, total = progress()
    pct = round(100 * done / total)
    out = ['# Testing status', '',
           f'**{pct}% tested** ({done:g} of {total} checks; a partial check counts as half).', '',
           'The translation is a beta: all text is translated, but most of it has not been seen in game yet.', '',
           '✅ tested, fine · 🔧 issue found and fixed · 🟨 partly tested · ⬜ not tested', '',
           'Tested by: **user** (playing in DuckStation), **auto** (screenshots from `tools/emu.py`), '
           '**frames** (video frames checked one by one).', '',
           'Regenerate this file with `python3 tools/testing_status.py` after updating the list in it.', '']
    for title, group in CHECKS:
        d = sum(DONE[c[1]] for c in group)
        out += [f'## {title} ({d:g}/{len(group)})', '', '| | Check | By | Notes |', '|---|---|---|---|']
        out += [f'| {MARK[s]} | {name} | {by} | {note} |' for name, s, by, note in group]
        out.append('')
    out += ['## Pending', '',
            '- Event floors not marked above, including the story from floor 1000 and the ending.',
            '- Shops, reading an actual mail, status effects, fleeing.',
            '- MOV05 and MOV09 inside the game.', '']
    path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'TESTING.md')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))
    print(f'{pct}% ({done:g}/{total})')


if __name__ == '__main__':
    main()

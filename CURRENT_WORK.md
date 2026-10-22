# Current work

## The one rule
There is ONE game file: PokemonWarAndMurder.gba at the repo root (plus its PokemonWarAndMurder.ips, built from the Outlaw original).
Never build from, restore, or copy any older ROM. Never create another .gba in the repo. The older ROMs were deleted from the repo and purged from git history on 2026-10-22.
The owner's rule, verbatim: "We cannot under any circumstances revert to older builds for new edits, and thats a hard rule."
Only the Outlaw original (roms/outlaw-2015-09-05 ..., CRC 0x5e460b23) may sit beside it. It is only the base for the IPS.

## The file now
- PokemonWarAndMurder.gba, CRC32 in ROM_LOG.txt (last line). Yellow bedroom. Lineage: the owner's personal build (0x2f906b52) plus the approved features below.
- Every change goes through one command: `tools/patch.sh tools/STAGE.py`. It patches the root ROM in place, rebuilds the IPS, logs the CRC in ROM_LOG.txt, and runs the guard.
- Guard: `tools/check_single_rom.sh` fails on any extra .gba, any save state other than saves/ported/new_game_empty_party.raw, a CRC that does not match ROM_LOG.txt, or an IPS that does not rebuild the ROM. It also runs as a git pre-commit hook.
- Stages are idempotent-by-convention only where noted (fix_sandshrew_learnset.py is). Do not re-run a stage that already ran.

## Testing
- tools/mk_test_rom.sh /abs/path/outside/repo/test.gba makes a scratch copy of the ROM plus tools/test_stage.py (door-tile test script; switches TEST_FOE, TEST_TRAINER, TEST_GIVE, TEST_LEAF, TEST_PLAYABLE, TEST_ITEM, TEST_AFTER, TEST_WARP). Never run test_stage through patch.sh.
- Tests start from saves/ported/new_game_empty_party.raw, a save state made from a fresh boot of the current ROM. Tests must run from this version or newer. Never use an older save state (they carry the old brown bedroom graphics). If a change touches the bedroom or maps, remake the state from the root ROM first.
- Harness: tools/harness_new (mGBA). Key masks are HEX (A=1 B=2 Select=4 Start=8 Right=10 Left=20 Up=40 Down=80).

## Approved features in the ROM
Opening and bedroom, Oak robbed, LEAF protagonist with the Hitmonchan-based stand-in, splatter order, JRA bases (Pallet, Viridian), Mason, Anne, Max, Shinigami/Yveltal/Nero storyline, double battles and partner AI, run mode and death rule, afterlife beats, task data, SHACKLE (item 89, captains, liberty), Eirika and Kestrel, FE8 allies, Sand Grave (move 358), Sand Rocks, UNSTABLE GROUND (move 359, Sandshrew at level 8), death effects (gunshot or cry, red fade, "mauled" line).
Details of each are in docs/history/ (old notes, history only).

## Open items
See the dated list at the bottom of this file.

## Log
- 2026-10-22: single-file workflow created; old ROMs and old save states purged from git history; Sandshrew's learnset end marker fixed (the allocator in tools/inc.py now keeps new data off a trailing 0xFF terminator).

## Open items (2026-10-22)
- Tests that still use old chain-only switches (VIRI_FORCE, VIRI_POKE, VIRI_FLAGS, MASON_TEST_LV and similar: tools/viri_test.py, mason_ko_test.py, splatter_sheet.py, layer_test.py) now build through mk_test_rom.sh but those switches are not ported to tools/test_stage.py yet.
- Sand Grave, Unstable Ground, partner-move fix, SHACKLE capture, death gunshot: not yet tested on this ROM.
- Death message clipping, missing red fade, heaven-vs-center choice, Viridian arrest red flash: see the dated notes below as they are resolved.

## Emulator runners
tools/emu_runs/{battle,death,shackle}.py TAG: build a scratch test ROM (TEST_* env switches, see tools/test_stage.py), run the harness from the current-ROM state, write sheets to /tmp/emu_out. Example: `TEST_PLAYABLE=1 TEST_LEAF=1 TEST_FOE=143,70 python3 tools/emu_runs/death.py t1`.

## 2026-10-22 fixes
- death_fade.py: the red fade on death now shows (the game refused it while the battle fade was still running; the death script retries until it starts). The "mauled" line breaks after "death" so it fits the box. Checked in the emulator from the current-ROM state: red screen, two-line text, Heaven.
- viridian_red_fade.py: the Viridian arrest loss shows the red screen again before the afterlife. Checked by running the helper script directly through test_stage (TEST_GOTO), not through the full arrest fight.
- Heaven vs Pokemon Center: with the stand-in LEAF, a lost battle in a PLAYABLE run goes to the Pokemon Center. Only a fainted permanent LEAF goes to Heaven. docs/SPEC_ARREST_AND_PARTY.md says PLAYABLE means any lost battle is death. Owner decision needed. Not changed.

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
Opening and bedroom, Oak robbed, LEAF protagonist with the Hitmonchan-based stand-in, splatter order, JRA bases (Pallet, Viridian), Mason, Anne, Max, Shinigami/Yveltal/Nero storyline, double battles and partner AI, run mode and death rule, afterlife beats, task data, SHACKLE (item 89, captains, liberty), Eirika and Kestrel, FE8 allies, Sand Grave (move 358), Sand Rocks, UNSTABLE GROUND (move 359, Sandshrew at level 8; final behavior is commit bc36755, not the earlier passes below), accuracy stages −1..−6 at 80/60/40/30/20/10, Dragonfly (move 360, Gyarados at 20, base Sp. Atk 125), Xatwo (species 430, commit 4c49e84), death effects (gunshot or cry, red fade, "mauled" line), Liberty mart (tools/liberty.py: bless/threaten locks, captain-or-Nero shackle, town third option LIBERTY).
Details of each are in docs/history/ (old notes, history only).

## Open items
See the dated list at the bottom of this file.

## Log
- 2026-10-22: single-file workflow created; old ROMs and old save states purged from git history; Sandshrew's learnset end marker fixed (the allocator in tools/inc.py now keeps new data off a trailing 0xFF terminator).

## Open items (2026-10-22, after Liberty)
- Accuracy stage table: bytes checked, hit rate never measured. Not retried; the harness cannot hold a battle stat and the RNG repeats from a savestate.
- Move sounds (Earthquake, stat change, Fly): not isolated from the harness. Fly's dive was seen; no waveform.

## 2026-10-22 Dragonfly field check, corrected
The note below this one ("fail on the warp") is stale. On the same scratch setup (Gyarados 20, no badges, Route 1), the Fly map cursor is: start ROUTE 1, Up = VIRIDIAN CITY, Down = ROUTE 1, Down = PALLET TOWN. One Down from the start skips Pallet and lands on Route 21. Up, Down, Down, A, A warps to Pallet. No ROM change. Party menu still offers DRAGONFLY with a clear Thunder Badge flag.

## 2026-10-22 Liberty mart (tools/liberty.py)
Applied on top of the Xatwo ROM. Town marts are BUY / SELL / LIBERTY / SEE YA. LIBERTY opens SELL POKéMON / BUY LIBERTY / CANCEL. BUY LIBERTY (and the old Celadon vitamin counter) opens the liberty goods directly: BLESS TAG, GLOCK, 9MM ROUND, SHACKLE BALL, HP UP, PROTEIN, IRON, CALCIUM, ZINC, CARBOS, RARE CANDY. Those items left the town lists; PHYS MUTAGEN and SPEC MUTAGEN stayed. Prices while that flag is set follow the liberty count (0 = 100%, each point above is 1% off, floor 1, each point below is 1% more). Other counters stay on reputation.

The 4-way shop menu is the engine's pokemart command, so a nested pokemart looked identical to "A did nothing." The shop task's first instructions now jump to a hook: if special var 0x800F is 0x4C42 (set by shop_lib_on, cleared by the hook, shop_lib_off, and map load), it calls the Buy handler instead of waiting. A normal mart never sets that value; the Viridian 4-way menu still waits for a choice. Checked in mGBA from the empty-party state, warped to the Viridian mart with the clerk scene var at 4: submenu on BUY LIBERTY, then the item list with BLESS TAG at $1000 (liberty 0) and the bless-charm description. Bless, threaten, shoot, and shackle were not played through in the emulator.

Skipped, same reasons as before: accuracy hit-rate sampling, and naming individual sound effects.

## Tests
All current tests are in tools/tests/ (see its README.md): they build a scratch ROM with tools/mk_test_rom.sh, start from saves/ported/new_game_empty_party.raw and write to /tmp/emu_out. Old scripts that needed retired ROMs, states or switches are in tools/archive/old_tests/ (do not run). The owner is testing the rest by hand; the test pass below is closed.

## 2026-10-22 fixes
- death_fade.py: the red fade on death now shows (the game refused it while the battle fade was still running; the death script retries until it starts). The "mauled" line breaks after "death" so it fits the box. Checked in the emulator from the current-ROM state: red screen, two-line text, Heaven.
- viridian_red_fade.py: the Viridian arrest loss shows the red screen again before the afterlife. Checked by running the helper script directly through test_stage (TEST_GOTO), not through the full arrest fight.
- Heaven vs Pokemon Center (owner decided): in a PLAYABLE run, if the player is in the party as a playable POKeMON (a real LEAF, or the stand-in that joins when the party is empty) when everything faints, she dies and goes to Heaven or Hell by reputation. If she is not in the party, the normal Pokemon Center respawn. A normal run is unchanged. standin_death.py: the stand-in is noted when the battle starts (the battle-end callback deletes her before the white-out script runs) in script scratch word 0x800A; the white-out check reads it. Checked in the emulator: playable plus stand-in goes to Heaven; not playable plus stand-in goes to the Pokemon Center; playable with a real POKeMON and no LEAF goes to the Pokemon Center.
- Lesson: the save block (script variables, flags) moves in RAM between the battle start and the white-out, so a value stored in a script variable at battle start was gone at the white-out. Use the script scratch words (0x8000 to 0x800F) or RAM outside the save block for that.

## 2026-10-22 test pass (emulator only, from the current-ROM state; every stage above was checked on a scratch copy first)
- UNSTABLE GROUND: foe accuracy and evasion each -2 (Rattata 4,4); a Keen Eye foe (Pidgey) only loses evasion; a Ground-type foe (Diglett) is skipped; the user is unaffected; no damage. Pass.
- SAND GRAVE: Sandgrave (Lv 40) learns it, rocks fall, red X, 10 PP, Ground type, KOs a Rattata. Pass.
- SHACKLE: real battle with JRA captain LARACHEL (trainer 15), Yes at the prompt: she joins the party, captain flag 0x871 set, liberty +5. Pass. Not tested: the +10 liberty when a captain is shot, the No answer, a second attempt.
- Partner fix: Viridian arrest double battle, MAX's Pikachu used Thunder Wave, Tail Whip and Thundershock on the foes (not itself). Pass.
- Death: LEAF dead goes to Heaven with a red fade. Wild killer: "mauled" line plus the cry. JRA soldier killer: no "mauled" line (death_class_fix.py; the class saved at battle start was always 0 for trainer battles). The gunshot sound itself was not checked, only that its branch is taken (no way to isolate one sound effect from the harness audio).
- Owner rule: when the player is shot, the gunshot plays, the screen flashes red, and the text says "The world goes red." Done in the white-out death, the Viridian arrest loss, and the Pallet base shooting (shot_red_pallet.py). The two other copies of the line (0xF62902, 0xF62AAF) are old death scripts that nothing points to (checked: no pointer to either script start in the ROM), so they never run and were left alone.
- Earlier note, superseded for the Pallet base: the "The world goes white." line now reads "The world goes red." in the white-out death script and the Viridian loss (death_text_red.py). Three more copies of the line (Pallet base 0xF31A11, story blob 0xF62902 and 0xF62AAF) still say white and have no red fade. Owner decision needed.
- Still open: Heaven vs Pokemon Center for the stand-in (see above).

## 2026-10-22 church tower walk-behind (church_walkbehind.py)
Pallet Town church: tiles (7,10) and (8,10) are unblocked, and the cross and tower top (tiles (7,9) (8,9) (7,10) (8,10), metatiles 729 to 732) are drawn over the player (layer type COVERED to NORMAL). The row below (6..9,11) stays blocked. Checked in the emulator: the player walks up behind the tower and is covered by it, and stops at the roof row. The owner listed "7/9, 7/10, 7/10, 8/10"; I took the repeated 7/10 to mean 8/9.

## 2026-10-22 Sandshrew line ability (sand_rough_skin.py)
SANDSHREW, SANDSLASH and SANDGRAVE now have ROUGH SKIN (ability id 24) in slot 1, slot 2 empty, replacing SAND VEIL. The ability is read from the species data, so existing Pokemon in a save get it. Checked in the emulator: a lv 30 Rattata that hit a lv 12 Sandshrew lost 3 of 63 HP (1/16); on the unchanged ROM it lost none.

## 2026-10-22 UNSTABLE effects (unstable_effects.py)
UNSTABLE (move 359) now plays Earthquake's animation and sound (the effect script had no attackanimation, so nothing played), prints "The ground became unstable!" once per use (new battle string, id 367: the 355-entry strings table was copied with one more entry and its 24 references repointed; the message is skipped on later targets via animTargetsHit), and shows the stat animation and messages ("RATTATA's accuracy harshly fell!", "evasiveness harshly fell!"), which the old script changed silently. Checked in the emulator on a Rattata: used-line, message, shake, both stat messages, foe accuracy and evasion at -2. The sound itself was not isolated from the harness audio.

## 2026-10-22 UNSTABLE v2 (unstable_drastic.py)
UNSTABLE no longer touches evasion. It now raises the user's own accuracy by 3 stages (first target only) and lowers the foe's accuracy by 3 stages (GROUND-type targets skipped), with the message "The ground became unstable!", Earthquake's animation and sound, and two new battle strings (this ROM's engine prints plain "rose!"/"fell!" for 3 stages, so the lines are custom): "SANDSHREW's accuracy drastically rose!" and "Wild RATTATA's accuracy drastically fell!". Move description: "Drastically lowers the foe's accuracy and raises your own." The owner's wording was "drastically decrease opponent's accuracy and drastically increase its own"; I read "its own" as the user's accuracy and "drastically" as 3 stages. Checked in the emulator on a Rattata: user accuracy +3, foe accuracy -3, evasion untouched.

## UNSTABLE message order (tools/unstable_order.py), applied 2026-10-22
Owner asked for this order: Earthquake animation and sound, "The ground became unstable!", the foe's accuracy line and debuff animation, then the user's accuracy line and buff animation. tools/unstable_order.py builds it and was checked on a scratch copy, and is applied to the ROM (see ROM_LOG.txt). Checked in the emulator on the root ROM: used line, ground message, foe line, user line, in that order; user accuracy +3, foe accuracy -3. The owner also asked whether UNSTABLE really moves accuracy 3 stages each way: the stages read 9 and 3 after one use and 12 and 0 after five (game memory), but a hit-rate measurement was not completed (UNSTABLE has 5 PP, the game RNG repeats from a saved state, so repeated runs are not independent samples).

## 2026-10-22 accuracy stage table (accuracy_table.py)
Lowered accuracy now cuts the hit chance to -1: 80%, -2: 60%, -3: 40%, -4: 30%, -5: 20%, -6: 10% of the move's accuracy (vanilla 75, 60, 50, 43, 36, 33; raised stages unchanged). Table gAccuracyStageRatios at 0x082504FC. It is applied to the net stage (attacker accuracy stage minus target evasion stage), so it also covers evasion boosts and applies to every battler, the player included. Verified by reading the table back and by disassembling the accuracycheck command (it indexes this table, entries of 4 bytes, and this is the only reference to it). NOT verified by a hit-rate measurement in the emulator: the harness `poke` command writes relative to the save block, so it cannot hold a battle stat, and the RNG repeats from a saved state. tools/tests/hitrate.py is a failed attempt (it measured a normal foe). Not retried on 2026-10-22.

## 2026-10-22 after pulling Xatwo (do not trust the UNSTABLE sections above)
Pulled origin/main before editing. HEAD 4c49e84, root ROM CRC 0x7ccc297f (xatwo_stage.py on top of dragonfly.py 0x50048f76). The UNSTABLE notes above are the earlier passes. The ROM's behavior is commits 32fa75d and bc36755: Earthquake first, user accuracy +3 once, every other non-Ground battler accuracy −3, with a line and arrows each. A missing goto opcode had been skipping that script in doubles; bc36755 put it back.

Dragonfly is still in this ROM. Gyarados base Sp. Atk byte is 125. Learnset at 20 is Bite (44) then Dragonfly (360), no Bubblebeam. Live field list (pointer at 0x122A7C) is the old moves plus 360 before the 0x000C sentinel. The compare at 0x124670 is 0x0B. Dragonfly's jump-table entry is Fly's handler 0x0812474C.

## 2026-10-22 Dragonfly field check (pass on the menu, fail on the warp)
Scratch ROM only: `TEST_GIVE=130,20 TEST_WARP=3,19,10,20 tools/mk_test_rom.sh /tmp/emu_out/dfly_field.gba`, state `saves/ported/new_game_empty_party.raw`, harness `tools/harness_new` with `LD_LIBRARY_PATH=/tmp/mgba/build`. Four runs, then stopped.

- The givemon is Gyarados, level 20, species 130, moves Thrash / Bite / Dragonfly (37, 44, 360), Dragonfly PP 15. Sp. Atk stat 52 fits base 125 with a Sp. Atk-lowering nature, not base 60.
- No badges. Save block 1 was 0x02025584. The badge flag byte (flags 0x820–0x827, block + 0xFE4) was 0x00, so FLAG_BADGE03_GET (Thunder Badge, the vanilla Fly gate) is clear. Only FLAG_WORLD_MAP_PALLET_TOWN was set among the town-map flags.
- Start → POKEMON → GYARADOS opens SUMMARY / DRAGONFLY / ITEM / CANCEL. The move is offered with no badge.
- A on DRAGONFLY opens the Fly region map. The cursor starts on ROUTE 1, which is not a destination, so A does nothing. One Down steps to ROUTE 21 and skips Pallet. A still does nothing. Coords stayed x=10, y=20, map (3, 19).
- The town warp was not completed.

Skipped on purpose (more than a few tries, or the harness cannot answer them): a battle hit-rate for the new accuracy curve, and naming the Earthquake / stat / Fly sound effects. The untracked liberty sources were not applied.

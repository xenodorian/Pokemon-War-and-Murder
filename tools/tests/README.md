Current tests. Run from the repo root. Each builds a scratch copy of the one ROM with tools/mk_test_rom.sh (TEST_* switches, see tools/test_stage.py),
starts from saves/ported/new_game_empty_party.raw (made from the current ROM) and writes output to /tmp/emu_out. Never use an older ROM or state.
- moves.py TAG        generic runner: KEYS="frame hexmask [hold];..." AUTO_TO END SHOT_FROM SHOT_STEP RAMS="addr count;..."; then sheet.py TAG
- start_menu.py [ROM]   start menu rows, REPORT text and flash sector, REMAP vars and keys seen by the game, hook transparency (prints PASS/FAIL, contact sheets in /tmp/emu_out/startmenu_*.png)
- death.py, shackle.py, battle.py   older fixed-timing runners (death.py also takes SHOTS="f,f,...")
- anim_test.py, anim_test2.py, damage_test.py, warp_test.py, battle_test.py, walk_test.py   older scripted checks, same rules
- newgame_test.py ROM.gba, opening_test.py ROM.gba   cold boot checks, no state
Example: TEST_FOE=19,20 TEST_GIVE=27,12 KEYS="1310 10;1360 1" AUTO_TO=1300 END=2300 python3 tools/tests/moves.py t1
Known facts: harness key masks are hex (A=1 B=2 Select=4 Start=8 Right=10 Left=20 Up=40 Down=80); the script file must be in frame order;
the save block moves between battle start and end (do not keep state in script variables across a battle); a loaded state carries its own graphics.

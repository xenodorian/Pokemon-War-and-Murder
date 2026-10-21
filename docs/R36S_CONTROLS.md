# R36S controls: X and Y acting as A and B (investigation 2026-10-21, NOT resolved)

Symptom (owner): on the R36S the A button is fine, Y acts like B, and in menus only X acts like A. It follows whichever game entry the updater (GitROMs) last updated. A renamed copy with a fresh controller layout was fine until the updater ran, then the problem moved to it. The RetroArch Controls screen has always shown X and Y as Turbo A and Turbo B for the affected game.

What is established
- Turbo labels on X and Y exist in the gpSP core (libretro/gpsp: JOYPAD_X "Turbo A", JOYPAD_Y "Turbo B"). The mGBA core (mgba-emu/mgba, src/platform/libretro/libretro.c) does not map X or Y. So an entry whose Controls screen shows Turbo A and Turbo B is running gpSP. Whether the entry that "works normally" runs a different core is NOT known; the owner has not compared the two screens.
- A GBA has no X or Y. The ROM cannot make them act as A or B. The ROM's own BUTTON MODE (HELP, LR, L=A, SWAP) only exchanges L, A and B.
- Emulator test (mGBA harness, 2026-10-21, current PokemonWarAndMurder.gba): in the game, A as a 4-frame tap, a 40-frame hold, and a 2-on/2-off pulse (turbo-like) all open the POKEMON menu from the Start menu. The ROM does not ignore held or pulsed A. The ROM does not explain the symptom on mGBA.
- Not tested: gpSP (not installed here) and the console itself.

What is not known
- Which core each entry launches, and whether it changed after an update.
- What GitROMs writes besides the ROM (web search found nothing about it). It could replace or re-create files, or touch per-game files that sit next to the ROM (.srm, .state, .cfg, .rmp, .opt) or the game list.
- What the physical B (south) button does in the affected entry. The owner reports Y acting as B; if B itself does nothing, that points at a remap, not the ROM.

What would settle it (on the console)
1. For BOTH entries: Quick Menu, Information, Core Information (core name), and Quick Menu, Controls (are X and Y labelled Turbo?). Compare.
2. For the affected entry: Quick Menu, Controls, and test each of the four face buttons and note what each does in the overworld and in a menu.
3. Before and after an update, list the files next to the ROM (names and modified times) and the per-game override and remap folders. A new or changed file points at the updater.
4. If both entries run the same core and have the same labels, the difference is in a file the updater touches, not the core.

Possible fixes once the cause is known: set the GBA system default to mGBA (system settings); set the per-game Alternative emulator; or unbind X and Y in gpSP and save a core remap (Quick Menu, Controls). Do not apply these blind.

## Update 2026-10-21 (later): B does not go back, Y does; only this game
- Owner: in this game pressing the physical B does not go back, Y does; no other game on the R36S behaves this way.
- Emulator test (mGBA harness): B closes the Start menu as a 4-frame tap, a 40-frame hold and a 2-on/2-off pulse, on the current ROM and on the older 0x32dfc7de build. The ROM does not drop B. The two builds behave the same.
- The repo contains no RetroArch remap, override or core-option files, so the updater is not delivering any from here.
- That leaves something on the console that is specific to this game's name or entry: a per-game remap or override that sends the south button somewhere else, a different core for that entry, or an entry that the updater re-creates. tools/r36s_diag.sh (read-only) lists the per-game files, remaps, game-list entries and the last RetroArch log for the game so the cause can be read off instead of guessed.

## Leading hypothesis (2026-10-21): a content-directory remap on the updater's folder (not confirmed)
- Y (gpSP Turbo B) works, so the game reads the GBA B bit. Only the steady physical B fails, and only in this game. A remap of the south button explains that. A ROM fault would hit both buttons alike, and the ROM passes the B test.
- The fault follows the copy the updater last wrote, and a fresh name was fine until updated. A per-game remap would not follow a rename. A per-core remap would break every GBA game. A content-directory remap (RetroArch saves it under the folder's name) applies to every ROM in one folder and nothing else. If the updater writes into its own folder and a remap was ever saved there (for example while trying fixes), every updated copy inherits it.
- Check on the console: in the affected game, Quick Menu, Controls, Manage Remap Files. A loaded remap, or a "Delete Content Directory Remap" option, means this is it. Delete it and retest B. Also check Quick Menu, Overrides for a content-directory override.
- tools/r36s_diag.sh now also lists every gpSP/mGBA remap and override (any name) and the folder each copy of the game sits in. The first version only searched for files named after the game and would have missed a directory remap.

## Bypass in the game (2026-10-21): START menu, CONTROLS
- Open the START menu, choose CONTROLS. The game names each button ("Press A."). Press the physical button you want for it. It shows which signal that press arrived as, or "No button pressed" after 5 seconds.
- Hold START + SELECT + UP together at any time to go back to the normal layout.
- The mapping is saved with the game, so updating the ROM keeps it.
- If a physical button shows "No button pressed", the emulator is not sending anything for it; the game cannot see it.

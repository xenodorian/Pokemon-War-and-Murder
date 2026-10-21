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

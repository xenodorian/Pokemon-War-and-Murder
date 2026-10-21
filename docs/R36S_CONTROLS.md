# R36S controls: why X and Y act as A and B (finding 2026-10-21)

Symptom (owner): on the R36S the A button is fine, but Y acts like B, and X acts like A in menus. It follows whichever game entry the updater (GitROMs) last updated. A renamed copy with a fresh controller layout was fine until the updater ran, then the problem moved to it.

Finding: this is the gpSP core's turbo buttons, not the ROM.
- gpSP (libretro) maps RetroPad X to "Turbo A" and RetroPad Y to "Turbo B" (libretro/gpsp, libretro.c: input descriptors for JOYPAD_Y "Turbo B" and JOYPAD_X "Turbo A"; input.c turbo_a/turbo_b).
- mGBA (libretro) has no mapping for X or Y (mgba-emu/mgba, src/platform/libretro/libretro.c: only A and B plus the d-pad, Select, Start, L, R).
- A GBA has no X or Y buttons. Nothing in the ROM can make them act as A or B. The ROM's own BUTTON MODE (HELP, LR, L=A, SWAP) only exchanges L, A and B.
- So the entry that "has the weird controls" is being launched with gpSP, and the entry that "works normally" is being launched with mGBA. The ROM files are the same build.

Likely mechanism (not verified on a device): the updater replaces or re-creates the game file or its entry, and the per-game emulator choice (the "alternative emulator" for that game in EmulationStation) is lost. The game then falls back to the system default core, which on many R36S firmwares is gpSP. A rename does not help because the new entry starts on the default core too.

How to confirm on the console: load the game, open the RetroArch menu, Quick Menu, Controls. If X and Y are listed as "Turbo A" and "Turbo B", the core is gpSP. (Quick Menu, Information, Core Information also names the core.)

Fixes, in order of how permanent they are:
1. Set the system default GBA emulator to mGBA in EmulationStation (system settings for Game Boy Advance). Every game and every update then uses mGBA.
2. Set the per-game emulator: highlight the game, Edit this game's metadata, Alternative emulator, mGBA. Re-check it after each update, since the updater may reset it.
3. If the game must stay on gpSP: Quick Menu, Controls, set X and Y to None, then Save Core Remap File. Turbo goes away for every gpSP game.

mGBA is the intended core. The repo's .state files are mGBA save states made on the R36S, and the ROM was tested in mGBA. A .state made in one core does not load in the other.

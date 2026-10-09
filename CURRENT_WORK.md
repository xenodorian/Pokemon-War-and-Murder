# Current work (2026-10-09)

Branch: claude/lucid-edison-b1ri7h. Source of truth: tools/ and gun/. Full rebuild: tools/build_full.sh PREFIX.

## Not in the repo (and why)
- ROMs and states (*.gba, *.state): gitignored (copyrighted, large). The unpatched base ROM f4046af2-outlaw-2015-09-05.gba (16,777,240 bytes) is required; tools expect out/c3.gba (an intermediate build, not stored).
- All built outputs in out/ (533 ROM builds, 8.4 GB) and test screenshots in shots/.
- The user's uploaded saves and states (00b1f3bc .sav, 19c47a6d .sgm, 453db1b1 .sav, f676643d .srm, several .state): live only in the session upload folder. Needed for the pending VBA-to-mGBA port.
- Delivered artifacts (.ips etc. from earlier turns) that are not already in the repo root.

## State
Done but only partly tested: see HANDOFF_pokemon_outlaw.txt, section STATUS UPDATE 2026-10-09.
Edge tiles (2026-10-09, patched into roms/m_final_latest_build.gba, source updated to match):
- extend_right no longer alternates the last two columns. A tree pair still alternates. A one-tile lip (path edge, cliff lip) is moved to the new eastern edge and the tile just west of it fills the gap. A trailing run of blank metatiles (0 or 1) is not copied outward.
- Checked on the patched ROM, map renders only: Celadon, Vermilion and Lavender east edges; Cerulean water east of the base; Seven Island east edge; Cinnabar inserted beach rows (sand, east border kept, house left in place). Original blank holes west of the extension were not rewritten.
- learn_lawn ignores metatiles 0 and 1, so a later rebuild will not paint those holes onto cut lawn.
- Not a full rebuild. Church warps, interiors, shooting, police teams and the grey house were not retested.
Open order of work:
1. In-game tests: church/base warps, custom interiors, story officer shooting, police Gen 1 teams, KARMA label, priest text, grey house tile glitch. Walk the east edges above and confirm the rock still blocks.
2. Port the user's VBA .sav and .sgm to R36S mGBA .srm and .state (not started; use an existing .state as template).

## Uploaded binaries (added 2026-10-09)
roms/: original hack ROM, c3_build_base.gba (input of tools/build_full.sh as out/c3.gba), m_final_latest_build.gba (latest build; east-edge comb/seam and Cinnabar beach stripes patched in place 2026-10-09).
saves/user_uploads/: current user files only: 00b1f3bc .sav and 19c47a6d .sgm (VBA, to be ported), f676643d .srm and 56898276/3a41f949/319d9027 states (R36S mGBA templates).
saves/delivered/: last delivered sav, sgm8, ini, Spirits Splatter state.
shots/: screenshots from 2026-10-09 only. ref_uploads/: FireRed reference zip and earlier handoff bundle.
Left out as outdated: 530 older ROM builds, older states/saves (453db1b1 .sav, be23eecc .state), shots before 2026-10-09.

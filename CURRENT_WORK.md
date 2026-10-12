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

## Lawn and fence rules, verified 2026-10-12 (user confirmed the scratch renders)
See tools/lawn_rules.py. A dark-lawn region (blocks 8/9/16/17, trees on top) in a pale lawn (662) gets its border from the 4 cardinal neighbours (654/670/663/686, concave 678/655/671/679) and diagonal neighbours (convex 711/710/703/702). Pairings come from Pallet's own map: 661 with 710/702, 686 with 652 below. All 15 fence blocks are drawn on dark lawn, so fences must not be drawn on pale lawn; the user said to draw no fences.
Reference scratch layout (not applied to any map): grey house on a pale yard, forest belt of whole trees on the back and sides, no fence.
Next: replace retree.learn_lawn/apply_lawn with these rules (the old table is learned from Pallet only and leaves corners unfilled), rebuild Vermilion's forest, re-render all extended towns.

## Vermilion base fix (2026-10-12, patched in place into roms/m_final_latest_build.gba, 70 bytes changed, Vermilion map only)
Cells changed (x,y): (48..57,11) tree bottom row 0x24|0x25; (48..57,12..13) lawn; (48,49,55,56,57 at y=14,15) lawn. Lawn = the town's own pattern: odd x 1, even x 8 (even y) or 16 (odd y). The house (x=50..54,y=14..17), the fences (row 17 and others) and every other town are untouched.
Cause in source, not yet fixed in tools/army_sites.py extend_row/retree: the stack at x=48..57 was left with a wrong-variant bottom row, orphan right halves at y=12..13, and the roof blocks of the old row copy at x=55..57.
The .state files are paired to the old ROM CRC and must be re-paired after the next full rebuild.

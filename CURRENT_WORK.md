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
Vermilion side edges (2026-10-12): trees whose side now faces lawn use the edge variants. (47,12..15) right halves 0x1d,0x15,0x1d,0x25 -> 0x1f,0x17,0x1f,0x27; (58,12..15) left halves 0x1c,0x14,0x1c,0x24 -> 0x1e,0x16,0x1e,0x26. 8 cells.

## Rock rules (2026-10-12)
See tools/rock_rules.py. Route 23 (3,42) mound logic: two nested rings around 113; concave corners 179 (left) and 178 (right). Verified by render: a 3x3 and a T-shaped mound. Lavender's rock should be rebuilt with these rules, not by repeating column pairs.

## Lavender rock comb fix (2026-10-12, patched into roms/m_final_latest_build.gba, Lavender map only)
Rows 0..5 x=23..36 = 113 (flat); row 6 x=22..35 = 121 (outer bottom face) and (36,6) = 179 (concave corner under the right wall); row 19 x=23..35 = 105 (top edge) and (36,19) = 187. Rock bits copied from (37,0). The yard, house, fences and the 112/113 right wall are untouched. Source (army_sites.extend_row) still produces the comb on a full rebuild: apply tools/rock_rules.py logic there.

## Lavender Tower fence runs (2026-10-12, ROM patch, Lavender map only, 11 cells)
The vertical runs used the horizontal fence block 231. Now x=15 rows 7..11 = 244 (pole on the block's left), x=21 rows 8..11 = 245 (pole on the right), corners (15,12) = 252 and (21,12) = 253 (post rising to meet the pole). The horizontal row 12 and every other fence are untouched. Vertical fence blocks use tile 0x202f, which the first fence scan missed.

## Comb scan (2026-10-12), tools/comb_scan.py
Finds blocks repeated along one axis, or alternated as A B A B, for longer than the original game ever does, only where the patched ROM differs from the original. Candidates still open in roms/m_final_latest_build.gba: Seven Island (3,18) lawn columns x=23..37 rows 14..19 (199/9/17 stripes) and its ledge rows 19..21; Cerulean (3,3) row 16 x=57..61 (block 244, a vertical-pole fence block, repeated horizontally). Lavender and Vermilion were fixed above. Tree and plain-grass alternation is expected and filtered out.

## Rock comb scan (2026-10-12), tools/rock_comb_scan.py
Flags rock side faces repeated across their edge, top/bottom faces repeated vertically, corner blocks repeated in a line, and rock blocks alternated A B A B, in patched cells only, over every map. Current ROM: 0 hits. The pre-fix ROM (commit 15edbff) shows hits in Lavender (117/113, 125/113, 179/113, 187/113 alternated, x=22..37) and Vermilion's water island (113/114 and 124/122 alternated, x=46..59), which confirms the scanner works. Cave and interior rock tilesets use other block ids and are not covered.

## Comb fixes (2026-10-12, ROM patch, 78 bytes)
Seven Island (3,18): pale-rim stripes 199/207 at x=23..37 rows 14..19 replaced by the dark lawn pattern (9 on even rows, 17 on odd); row 13 pale-band bottom rim 206 across x=23..36; ledge posts 230 continue along row 21 to x=36, tall end post 232/243 at x=37, grass above. Cerulean (3,3): row 16 x=57..61 was 244 (vertical pole) repeated; now corner 252 at x=57 and horizontal fence 231 at x=58..61. Scanners report no remaining candidates of the listed kinds.

## Viridian orphans and tree variants (2026-10-12, ROM patch)
Viridian (3,1): town side x<=41 restored to the original (road top 358 at (40,17), road right edge 367 at (41,18..22), fence row 231 at (39..41,15) and the grass cells); the orphan rock 114 at (41,14), (53,14), (41,21..22), the sand-coloured 228 row at (43..52,21), the road lip 358 row at (43..52,14) and the 367 column at x=53 became plain yard grass (9); north tree band bottom row now interior variants (26|25 at the left end only, 24|25 inside); east tree column x=54 rows 14..21 uses left-edge variants.
Tree variants by rule (left half edge iff its left neighbour is not a tree, right half likewise) normalised in changed regions of Pallet, Cerulean, Celadon, Saffron and Seven Island: 61 bytes. The rule holds for 97% of the original town maps (142 of 4316 exceptions, mostly at the map edge).
tools/orphan_scan.py lists orphaned road, rock and tree-variant cells in patched regions. Left: Pallet (5,16) block 106 over 122 (the small rock cave, probably fine) and Vermilion (59,28) block 122 next to 124 (probably the island's own corner). Found by eye, not fixed: Pallet base house has a dark grass strip above its roof and a dark patch at the east tree column (the graft's ground tiles); the Pewter house graft uses dark grass ground on pale lawn.

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

## Pallet base lawn and house ground (2026-10-12, ROM patch)
Pallet (3,0) lawn rim cells re-set by tools/lawn_rules.py: (35,12)=655, (35,15)=663, (35,16)=703, (37,16)=655, (24,16)=652, (21,15)=663, (21,16)=703. The grafted house metatiles 1008..1023 had Pewter dark grass as their ground layer; those entries now use the pale lawn tiles (Tileset.commit rewrote the Pallet tileset, so about 11 KB of the ROM differs). Image 1 of the review (Pallet rock hut at (5,16) and the pond) is vanilla art, also in the original ROM; the user wants its corners reviewed. Vermilion island corner (59,28) is vanilla.

## Pallet pond corners (2026-10-12, ROM patch, 2 cells)
(7,17) 721 -> 288 and (10,17) 722 -> 289: the original corner blocks leave grass-coloured notches in the rock rim; 288 and 289 are the primary tileset's rock-rimmed deep water corners and line up with the 298/300 sides and the 291 top.

## Pond corners, corrected (2026-10-12)
Original ROM logic for rock-rimmed water corners: the corner block follows what lies outside the corner. Square corners (288/289, 419/420, 582/583, 616/617) are used when the outside is rock or cliff (Cerulean (4,2): rock 124/117/178 around; Vermilion's rocky pond). Rounded corners show lawn: 290/292 and 421/423 have dark-grass pixels (115,205,164) in the corner, used where grass 1/8/9/16/17 lies outside (Vermilion, Celadon, Viridian); 721/722 are Pallet's own versions with pale-lawn pixels (189,238,213), used where pale lawn 662 lies outside. Pallet's pond sits on pale lawn, so 721/722 were already right; the earlier change to 288/289 was reverted. Bottom corners exist only as the rounded variants 548/550 (and 784/786 in some tilesets).

## War and Murder ROM updated (2026-10-13)
roms/Pokemon War and Murder.gba (CRC32 0cf5c687) is the previous War and Murder ROM (the m_final of commit 5952868 plus its own 29-byte patch) with the 11,915 bytes of ROM changes from the 16 commits since 9004b1d applied: Vermilion, Lavender, Seven Island, Cerulean, Viridian, tree variants, Pallet lawn, house ground and tileset. It does not contain the CryMon cottage opening port, which is in the old m_final of commit 9004b1d. Checked: every changed byte sat on bytes that were identical in War and Murder and in that base; the rest differs from the old m_final only by the 7,381-byte CryMon port and War and Murder's own 29 bytes; scanners give the same results as for the old m_final; the smoke harness rendered Pallet, Vermilion, Lavender and Seven Island.

## Other ROMs removed (2026-10-13)
Deleted from the working tree: Aladdin Sane.gba, c3_build_base.gba, m_final_latest_build.gba and the original hack ROM. They are still in git history (for example at commit 48c9829's parent, 982aa3c). tools/build_full.sh and tools/cry_open.py read c3_build_base.gba, m_final_latest_build.gba and the original ROM, so they need those files restored from history before they can run.

## Single patch (2026-10-13)
All 34 old .ips patches were deleted (still in git history). "Pokemon War and Murder.ips" is the one patch: apply it to the original hack ROM (outlaw-2015-09-05, 16,777,240 bytes, CRC32 5e460b23, header title POKEMON FIRE, code BPRE) to get "Pokemon War and Murder.gba" (CRC32 0cf5c687, md5 7893fd07458ccd658a833d99b8b7594b). It has 473 records, 546,937 bytes, and was checked by applying it to the original and comparing byte for byte. Regenerate it whenever the ROM changes.

## Pair scan of the War and Murder ROM (2026-10-13), tools/pair_scan.py
Flags adjacent block pairs that the original ROM never has, only where a cell differs from the original (python3 tools/pair_scan.py ROM ORIGINAL). Town exteriors (group 3): 0 to 16 unseen pairs per town; most are legitimate new combinations (tree rows meeting rims, road corners beside grass). Real candidates found by looking at renders, not yet fixed: Cinnabar (3,8) rows 15..24 x=0..7 sand meets water with no shore blocks, and its grafted house has dark-grass ground on sand; Cerulean (3,3) (61,17) a lone horizontal fence block under the fence row; Lavender (3,4) (22,19) block 187 is an orphan corner in the middle of the bottom rock strip (should be 105); Celadon (3,6) (68,12) sign block with grass ground sits in the road edge (minor). Custom interiors (2,60..81) are new layouts and cannot be judged against the original's pairs; the base interior, church and Hall of Justice look consistent; Heaven (2,80) shows scattered black cells in the static render, unverified in game.

## Coast, path, plant fixes (2026-10-13)
roms/Pokemon War and Murder.gba is now CRC32 08249a95, md5 48cd6cbd4b9247381dac2818764ae0e6; Pokemon War and Murder.ips regenerated (558,207 bytes, 476 records, verified byte for byte against the original ROM). Changes (11,371 bytes): Cinnabar (3,8) rows 15..24 x=0..6 water 299 and x=7 rock rim 300 instead of sand, and the grafted house ground uses the sand tile (Cinnabar's tileset was rewritten); Fuchsia (3,7) (40,20..22) = 211/219/227, the left edge of the right-hand sand path; church (2,67) (1,2) and (7,2) block 71 (bush) -> 79 (potted plant); the 58 bush blocks 847 in the base interiors (2,69..79) -> 854 (potted plant on the same lane floor). Heaven (2,80): the black squares seen in the static map render do not appear in game (smoke harness screenshots at three positions); they come from the static renderer, which treats some palette-7/8 tiles as black. Still open from the pair scan: Cerulean (61,17) stray fence block, Lavender (22,19) orphan 187, Celadon (68,12) sign ground.

## Collision audit and plant, rock fixes (2026-10-13), tools/collision_scan.py
ROM CRC32 1af8c29e, md5 695df1fc56aa5adf22d078dd26dc64cb; Pokemon War and Murder.ips regenerated (581,550 bytes, 476 records, verified by applying to the original).
Collision scan (changed cells vs how the original uses each block) found and fixed: Cerulean fence cells (57,13..16) and (58..61,16) had no collision (walk-through; the (57,16) corner too) and now have collision 1; Cerulean grass (45..47,17) and (58..60,17) and 25 Fuchsia grass cells around the base yard (x 30..42, y 9..19) carried leftover collision from removed fences (invisible walls) and are walkable now. Left as they are: tree tip blocks 14/15 in Pallet row 19 x=22..37 and Viridian row 22 x=42..53 are solid here although the original often leaves tips walkable (they are visible trees at a map edge); Lavender (18,6) block 783 is walkable in the first custom build (c3) already and is the Tower entrance.
Verified solid (collision 1): all 58 potted plants and their leaf tops in the 11 base interiors, the 2 church plants and tops, Cinnabar sea rocks, Lavender fences and the rock mass and face, Vermilion tree rows. Not verified by walking in game.
Plants: the potted plant is two blocks, leaves above the pot. Pot blocks 854 (base) and 79 (church) stay; a new leaf-top block (wall behind plus leaf tiles) sits above each: base tileset block 1000 (over 824) with 1001 and 1002 (over posters 870 and 871), church tileset block 1000 (over wall 40). The base tileset (shared by maps 2,69..79) was rewritten and all 11 layouts repointed.
Cinnabar (3,8): rock pairs completed, (1,15)=280, (2,15)=281, (1,24)=272, (2,24)=273. The 10-row water gap between the rocks comes from the inserted base rows and is intentional.

## Collision walk test in the emulator harness (2026-10-13), tools/walk_test.py
Each case warps the player next to an obstacle, holds a direction for 64 frames and reads the player's map position from RAM (control case: open grass, moved 4 tiles). Results on the current ROM (CRC32 1af8c29e): Cerulean fence run (59,16), fence pole (57,14) and corner (57,16): blocked; Lavender vertical fences (15,9) and (21,9): blocked; Lavender rock face (25,6): blocked; Vermilion tree row: walked one tile, then blocked; base interior pot (17,2): blocked at (17,3); church pot (1,2): blocked at (1,3). Former invisible walls at Cerulean (46,17) and Fuchsia (36,19): now walkable (moved 2 and 3 tiles). Not walk-tested: Cinnabar sea rocks (need Surf; collision bits checked in the data only).

## Source tools now carry the edge rules (2026-10-13)
- tools/edge_rules.py: rock comb rules (which blocks may repeat on which axis), lip_fill (what a rock lip becomes when a town is extended east: 117/125 keep the wall and fill 113, 179 fills 121, 187 fills 105, 112 fills flat lawn 8, the corner or wall moves to the new east edge), and validate() (rock comb, half trees, A B A B rock stretches).
- army_sites.extend_row calls lip_fill first, so a rebuild of Lavender reproduces the verified fix instead of repeating wall blocks.
- retree.apply_lawn: unseen tree neighbourhoods now resolve through their cardinal part, else are collected in apply_lawn.unresolved; army_tail asserts none remain, and runs edge_rules.validate on each town against its pre-edit map before commit. army.py regenerated (head + tail).
- tools/edge_rules_test.py: regression tests (Lavender rows reproduce the approved result). Passes.
- Not exercised: a full rebuild (needs the deleted ROMs from git history). Corners and edges outside Lavender's lip cases are guarded by validate(), not generated by new rules.

## Edge rules extended (2026-10-13)
- edge_rules.py now also holds: lawn_border() generator (wraps lawn_rules.border_block, incl. the verified 652-below-686 case), fence_run() and fence_findings() (231 horizontal, 244/245 vertical, 252/253 posts; flags vertical fence blocks in a horizontal run, 231 in a vertical run, fences touching pale lawn), pond_corner_top() and pond_findings() (square 288/289 outside rock, 290/292 outside dark lawn, 721/722 outside pale lawn), lawn_edge_findings() (edge block whose dark side is pale or pale side is dark). validate() runs all of them. Against the original ROM, the current ROM has no new findings of any kind (lawn 39 -> 33, pond 24 -> 14, fence 0 -> 0).
- ROM: Lavender (22,19) orphan corner 187 -> 105 (the rule's result; its east neighbour is now rim 105). ROM CRC32 769c4dab, md5 74d0756314c467b62c6b999bcd63e141. Pokemon War and Murder.ips regenerated (583,902 bytes, 1442 records, verified byte for byte against the original ROM).
- Not covered by generators: pond bottom corners and sides beyond the top corners (only checked for top corners), water-to-sand shores, road edges.

## Edge rules for every tileset (2026-10-13)
- tools/edge_learn.py learns, from the original hack's maps, a vocabulary for all 60 (primary, secondary) tilesets (tools/edge_vocab.json.gz, 496 KB): which block pairs touch, and which block the original puts between each north/south/east/west neighbour set. This covers water and shores, roads, sea rocks, plants, indoor floors and every other family without a hand table. Between 85% and 100% of the neighbour keys per tileset are decided unanimously (python3 tools/edge_learn.py coverage). Rebuild with: edge_learn.py build ORIGINAL.gba.
- tools/edge_check.py ROM [ORIGINAL]: unseen pairs and cells the original decides otherwise, per map (with the original: only changed cells). Needs no original ROM to check, only to restrict to changed cells.
- army_tail now prints this check for each town edit (warn only; new buildings legitimately make new pairs). edge_rules.vocab_report is the hook.
- Hand-written families remain: rock mound, lawn border, fences, pond top corners (edge_rules.py). The vocabulary is a checker and a unanimous-only repair, not a full generator for shapes the original never draws.
- Current ROM against the original, town maps: 3 to 27 unseen pairs each (mostly the grafted house and fences meeting lawn). Cells the original is unanimous about otherwise: Pallet (19,14) 662 vs 654, Viridian-side (46,17) 9 vs 8, a Lavender-side cell (22,16) 8 vs 1. Not examined or changed; candidates for the next review. Custom interiors (2,60..80) are whole new floors and are not meaningful here.

## Review of the three vocabulary candidates (2026-10-13)
Rendered original vs current for Pallet (19,14), Cerulean (46,17) and Lavender (22,16). None is a defect: Pallet's cell is plain pale lawn beside the house (the suggested 654 would add a dark edge that is not there); Cerulean and Lavender cells are dark-lawn variants (9 vs 8, 8 vs 1), and the original's own 8/9/16/17 parity is irregular (about 30% of its lawn cells follow any single parity), so they are interchangeable. No map changes. edge_learn.Vocab.repair now ignores swaps between lawn variants 1/8/9/16/17.

## Pallet (19,14) fixed (2026-10-13)
My earlier review dismissed this cell wrongly. The original has 654 (dark north edge) at (19,14), which closes the dark fringe under the house; an earlier edit left plain pale 662 there, leaving a notch at the fringe's right end. Set to 654 (collision bits unchanged, walkable). ROM CRC32 a4b2616e, md5 a97efb54b9eed8f2524625b6297eb2b0; Pokemon War and Murder.ips regenerated and verified. The vocabulary check had flagged it correctly.

## Cerulean fence connected (2026-10-13)
The west fence (row 17, x=42..44) stopped short of the base-lot pole (245 at x=48, rows 13..15). Now (45..47,17)=231, (48,16)=245 and (48,17)=253 (bottom-right corner: pole above, rail to the left), so the fence runs unbroken from the x=41 pole to the lot pole, as in the original. The pole cells (48,13..16) had no collision (walkable, raw>>10 = 12); all fence cells now collide (raw>>10 = 1). The east piece ((57,13..16), (58..61,16)) and the stray 231 at (61,17) are unchanged. Not walk-tested. ROM CRC32 3be71115, md5 e0a5e8f06f397956ff37b106c60642b3; patch regenerated and verified.
Lavender (22,16): false alarm (lawn variant 8 vs 1, former cliff column); no change.

## Cerulean fence end caps (2026-10-13)
Pole tops (48,12)=238 (cap of the 245 pole) and (57,12)=239 (cap of the 244 pole, same block the x=41 pole uses at (41,11)), solid. The lone 231 at (61,17) is left as is (user: not wrong). ROM CRC32 d15a7735, md5 56c67ab1391602826e638a736be8ae01; patch regenerated and verified.

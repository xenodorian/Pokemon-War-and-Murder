New agents: read docs/FOR_NEW_AGENTS.md first.

# Current work (2026-10-16)

Branch: main (work is pushed straight to main). Source of truth: tools/ and gun/. Full rebuild: tools/build_full.sh PREFIX. Scripts use /home/claude/work, which is a symlink to this repo (created 2026-10-16); out/ is gitignored.

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

## ROMs restored (2026-10-16)
Aladdin Sane.gba, c3_build_base.gba, m_final_latest_build.gba and the original hack ROM (outlaw-2015-09-05, 16,777,240 bytes, CRC32 5e460b23) are back in roms/, restored from commit 81fcf55's parent by reverting 81fcf55. Tools that read them can run again.

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

## Cerulean stray fence removed (2026-10-13)
(61,17) 231 -> 9 (same value and walkable collision as (60,17)). ROM CRC32 f6051223, md5 ae8e02e83333f467462454c15d32ed47; patch regenerated and verified.

## New opening, Oak robbed, no naming screens, splatter order, base 1 paintings (2026-10-13)
ROM CRC32 fe132372, md5 dbfea86fd50f55baaa478321cd7b93e1 (superseded f46186eb; see the paintings note at the end); Pokemon War and Murder.ips regenerated and verified. All built by scripts in tools/, applied in this order to the previous ROM: cry_open.py, splat_order.py, base1_paintings.py, base_paintings_clipped.py (each IN OUT).
- cry_open.py (ported from the old m_final build, now on this ROM; the house tiles are baked into tools/cry_house_tiles.json because the CryMon repo is gone):
  - New games start in the player's house 1F (4,5), not the Slums. The Slums are gone from play: Pallet's rock hut (3..5,16..17) is dark lawn, its warp (id 3) is parked at (0,0) so the other warp ids keep their numbers. Map (1,88) is still in the ROM, unreachable.
  - No naming screens. The two DoNamingScreen calls in the new-game task (0x1303B4) go to a stub (0x3B4D84) that writes MAX into the save and returns through the screen's own return callback; the "Are you sure" Yes/No answers Yes by itself. The rival is MASON: rival preset 0 (table 0x463124) and every trainer entry that was named TERRY (13) now say MASON.
  - House 1F: CryMon wood tiles, father in the bed (2..3,3..4), empty bed, shelf (8,3) gives SANDSHREW lv3, crate (10,5) gives a POTION, the door (4,8) is locked until the shelf is used (coord events at (4,7),(5,7)).
  - Pallet: ultra-ball man hidden, the first-exit tourist trigger removed, Mason (Gary sprite, PIKACHU lv3, trainer 743) fights at (5..7,8), the script continues after the fight (battle type 2, type 0 ended the script), Anne (Lass sprite) gives 5 POKé BALLS. Oak's lab: no starters, Oak says he was robbed.
  - Flags moved to 0x4EF..0x4F6 (the old port used 0x4E6..0x4ED, which collide with the spirit quests' hide flags 0x4E5..0x4EE and made the shelf read as already used). VAR 0x406D = opening progress.
  - Quest log text (first entry, in place at 0xA00000) no longer mentions the Slums or the tourist.
- splat_order.py: the blood splatter (gfx 0x98/0x99/0xA1, one image table) gets subpriority 0xFF whenever SetObjectSubpriorityByElevation sets it (hook at 0x6832E, stub at 0x3AE340). Always over the ground, always under the player and NPCs. Checked in the harness walking over Pallet (11,12) from both sides, before and after.
- base1_paintings.py: first base interior (2,69) loses only the two pictures a plant clips (x=4 and x=18..19); the pictures at x=10 and x=14 stay (superseded the earlier 'all four').
- Tests: tools/newgame_test.py (names and start position from a cold boot), tools/opening_test.py (whole opening, plus 'lab' mode for Oak), tools/splat_test.py, tools/walk_test.py (WALK_ROM env var; the Cerulean row 17 case now expects the connected fence to block). All passed on this ROM.
- Not done / open: the Vallejo surname and the CryMon dialogue text. The CryMon repo is deleted, so the dialogue is the earlier port's adaptation, not verbatim CryMon text.

## Base paintings clipped by plants (2026-10-13)
Rule (user): a painting is removed only where a plant's leaf top (1000/1001/1002) is in one of its cells or directly beside it in the same row; unclipped paintings stay. A review agent checked bases 2,69..2,79 and I re-checked its list with my own scan (same result). Removed: 2,69 (4) and (18..19); 2,70 (7..8) and (19..20); 2,71 (9) and (19..20); 2,74 (18..19); 2,77 (9..10) and (16..17). Bases 72, 73, 75, 76, 78, 79 have no clipped painting and are unchanged. Leaf tops and pots are untouched. tools/base_paintings_clipped.py makes the 22 cell edits for 2,70..2,77 (old ids asserted). Disembodied plant parts: none in any base (every leaf top has a pot below it, every pot a leaf top above). ROM CRC32 fe132372, md5 dbfea86fd50f55baaa478321cd7b93e1; patch regenerated and verified. Walk tests (pots, control) and the new-game name test pass on it.

## Clearing the board, step 1 (2026-10-13)
ROM CRC32 0xdbe235f4, md5 054ab2d97b0be82bc517f8db278b9780; patch regenerated and verified. New scripts, applied in this order after the earlier ones: door_anim.py, priest_text.py.
- Base door animation (task: normal door animation). The base house door (metatile 1011 in every base town's tileset) had no entry in the door graphics table, so the doors never moved. Also, the door animation draws with tile numbers 1008..1023 and the house graft had put its tiles there (that is what made the roof flicker when I first added the entry). tools/door_anim.py moves those tiles to free slots in the 11 base towns, adds table entries that reuse Pewter's grey house door animation recoloured to the graft palette (slot 7 everywhere, slot 12 in Pallet, where the door cell becomes metatile 1007, a copy of 1011), and repoints the table. Checked in the harness in Pallet and Viridian: the door opens when the player walks in and closes behind. All 11 town renders are pixel identical before and after; walk tests and the new-game test pass. Arrival one tile outside after leaving a base is confirmed (Pallet: out at (29,17)). Church door: not animated, deliberately. It is a double door (two metatiles 750 and 751 with behaviour 0x67) and the game has no half-door frames; stepping onto it walks in. The arrival tiles (7,16),(8,16) in front of the church are warp events but do not trigger when walked over (checked).
- Priest (task: only state the current cost). Investigated: the priest's own dialogue already states only the current price (inserted at runtime) and has no formula; the formula "1,000 per kill, 9,999 at most" was only in the CONFESSION quest log entry (three copies in the ROM). priest_text.py rewrites all three: "names a price for your kills", no amounts.
- Lavender (18,6): confirmed (read-only check) as a real door tile with a warp to map (2,60); it is reachable through the graveyard fence gap at (18,12). Not a defect.
- Tree tips: in the original game the tip blocks 0x0e/0x0f are walkable about 98% of the time at the top of a stack, so the walkable tips are right. Decided: no change.
- Cinnabar sea rocks: the collision of every rock and rim cell matches what the original uses for the same block; water is collision 0 as in the original. Data check only, no Surf walk. The patch does remove some original rocks (x 2..9, y 16..19), which is the earlier inserted-base reshaping.
- Celadon sign (68,12): looked at again. The sign stands on the same pavement tone as the road around it; changing the block to the lawn variant (a review agent tried) draws green corners in a road row and is worse. Left as is.
- Town edge check: every flagged cell is a sign on pavement (block 2, the sign-on-road tile), plus one rule artifact; no real defects found. (edge_check.py skips town maps whose grid equals another map's; note kept.)

## Clearing the board, step 2 (2026-10-13)
- In-game checks run in the harness on the current ROM (CRC32 dbe235f4):
  - Story officer shooting: Pallet officer at (11,14): "Shoot the officer? This uses one 9MM ROUND." YES/NO, then "The officer goes down." and a splatter. Works.
  - KARMA menu entry: present in the start menu with its help text ("See your kills, blessings and karma."). Works.
  - Police Gen 1 teams (trainers 55..78, data read from the ROM): all 24 teams are Gen 1 species (1..151), no duplicate species in a team, levels 2 or more, team sizes within each town's leader party size. No battle was played.
  - Custom base interiors 2,69..2,79: all 11 load, the player arrives at the exit, tiles render, soldiers and furniture show. Exit arrow warps and the arrival one tile outside the door work (Pallet). Pot collision walk tests pass. Story fights inside the bases were not played.
  - Grey house tile glitch: all 11 base houses render clean in every town; the only glitch seen was the roof flicker when the door animation overwrote tile slots 1008..1023, fixed by door_anim.py.
  - Church warps: the church door warps work; arrival tiles in front of it do not re-trigger when walked over.
- Save port (VBA to R36S mGBA). The user's VBA .sav is the raw 128 KB SRAM, identical to an mGBA .srm, so saves/ported/Pokemon War and Murder.srm is that file renamed. It loads on the current ROM (Continue works; the game resumes in front of the Cinnabar gym). The .state was made by booting the ROM with that .sav in the harness, pressing Continue, saving the raw mGBA state, and wrapping it in a RetroArch RZIP using an R36S template state (tools/make_state.py). The VBA .sgm was not converted: a VBA state holds the old ROM's RAM and is not meaningful for a changed ROM; the .sav is the last in-game save. Re-pair the state with tools/repair_state.py whenever the ROM changes again.
- Build chain: tools/apply_all.sh rebuilds the current ROM byte for byte from the ROM at commit 16adfb2 (checked: CRC32 dbe235f4).
- tools/field_test.py, opening_test.py, newgame_test.py, splat_test.py, walk_test.py are the harness tests; they need /home/claude/work (harness, state out/user_new.raw).

## Clearing the board, step 3 (2026-10-13)
ROM CRC32 229fb33e, md5 37dfe10e347c2e4b5038f6106edf4dd0 (supersedes dbe235f4); patch regenerated and verified; saves/ported/Pokemon War and Murder.state re-made on this ROM (the .srm is unchanged).
- Slums (user decision: Pallet only). The other towns' Slums signs, NPC lines and the Viridian cave quest stay. The three lines that sent the player "back to PALLET SLUMS" are reworded (slums_text.py). Found and fixed a miss: the FIRST POKéMON quest log entry exists four times in the ROM, not once; cry_open.update_quest_text now rewrites all four (before this the quest log could still say "Leave the SLUMS"). Checked: no copy of the old text is left.
- tools/apply_all.sh now includes slums_text.py and rebuilds the current ROM byte for byte from commit 16adfb2.
- Mason fight lost: only partly tested (a lv60 Pikachu build; the fight was still running when the test ended). By the script logic a loss ends the scene: no flag is set, Mason stays and talking to him or stepping on the trigger tiles starts it again.

## Clearing the board, step 4 (2026-10-13)
- Cinnabar sea rocks walk-tested (the saved game starts the player surfing, so warping onto water works): from (1,16) up is blocked by the rock at (1,15); from (3,15) left is blocked by (2,15); from (3,24) left is blocked by (2,24); the player moves freely along the open water row 16. Solid in game.
- Pond bottoms and sides, shores and roads: there is no hand generator for these. edge_learn.Vocab (suggest / repair, learned from every original map) is the rule source for them, and edge_check.py is the check. That is the stopping point; a drawn-from-scratch pond would still need a human look at the render.

## Shinigami / Yveltal / Nero storyline (unattended build, 2026-10-13)
Plan and decisions: docs/STORY_PLAN.md. Ids: tools/story_ids.py. Text: story_assets/text/story_text.json (via tools/story_text.py). Rebuild everything with `sh tools/release.sh` (apply_all.sh chain, then roms/ and the IPS).
- Step 1 done (tools/story_species.py): species 254 YVELTAL (Dark/Flying, data from story_assets/yveltal/yveltal.json, PokeAPI sprite art) and 255 MAX (Caterpie stats, only TACKLE, CryMon art). Both checked in the harness as wild battles.
- Step 2 done (tools/story_base1.py): Shinigami is locked up in Pewter base 1 (2,69) at (21,4). Before the Captain falls (flag 0x4C0) he only pleads; after it, talking to him gives the scroll flag, SPELL TAG, MASTER BALL, NUGGET, TM30, he leaves, F_FREED set, HIDE_STORY cleared, Lavender plaza scene armed (VAR_SCENE 0), VAR_STORY 2. A one-time init in the home map's transition (VAR_STORY 0 -> 1) hides the crime scenes (bodies, feathers, cops beside them, 16 objects, flag 0x4F8), the Tower-top Shinigami fight object (flag 0x4FF) and holds the Lavender scene (VAR_SCENE 5). The League line now says "You freed me".
- Step 3 done (tools/story_anne.py, tools/story_party.py): leaving base 1 with VAR_STORY 2, Anne stands outside Pewter's base door (frame script) and tells Max her father died; YES wakes Father (VAR_CHOICE 1, F_FATHER_ALIVE), NO calls YVELTAL (VAR_CHOICE 2); VAR_STORY becomes 3. DECISION: the party stays 6 slots; Father's second team (SANDSLASH, NIDOKING, ARCANINE, PERSIAN, RHYDON, ALAKAZAM at the player's average party level, min 10, OT = player) lives in PC box 14 (renamed FATHER). The quest menu (Start) has a new entry FATHER'S TEAM that swaps the party with box 14 (native code, checked: a round trip restores both teams; mons arrive at full HP). Native code is Thumb-1 only (no .w instructions on the GBA CPU; the builder asserts it).
- Step 4 done (tools/story_yveltal.py): stepping on the grave (tower (2,66) tile (11,6), where the old Shinigami fight object was) with VAR_CHOICE 2 and VAR_YV 0 wakes YVELTAL (Lv = highest party level + 5, min 45, max 100; native yv_setup calls the setwildbattle routine). Caught = VAR_YV 2 (tamed), knocked out = 3 (Godslayer), ran = 1 (grave works again), VAR_STORY 4 on tamed or beaten. VAR_YV is 4 during the fight and the global white-out script (literal at 0x7f5ec) is hooked: a blackout with VAR_YV 4 plays the Bloody ending (text, title card, soft reset to the title; the last save is kept). Father path sets VAR_YV 9 so the grave stays quiet. Checked: Yveltal appears at Lv45 from the grave; the Bloody path plays and resets. Not run by hand: the caught and knocked-out branches (they use GetBattleOutcome = special 0xB4, copied from the game's Snorlax script).
- Step 5 done (tools/story_nero.py): trainer 530 GORE is now NERO with the picture from story_assets/chars/nero_pic.png (class stays JRA GENERAL). His camp script (map 2,79): intro (nero_spot), battle, nero_defeated, then two yes/no boxes: ARREST (YES), else EXECUTE (YES), else be CROWNED. VAR_NERO 1/2/3, reputation +20/-30/-10 (VAR_REP, 100 neutral, clamped 0..200). Then the epilogue subroutine: war card, trial/crowned card, Father reaction (only when he was revived: proud if arrested and reputation >= 100, sacrifice if arrested with lower reputation, monster if executed or crowned: Father leaves and F_FATHER_ALIVE is cleared; his team stays in box 14), Yveltal card (tamed / Godslayer / none), one title card (Godslayer, Kingslayer = executed or crowned, Max The Bloody = reputation <= 40, Max The Kind = reputation >= 130), THE END, F_ENDED, and the old warp to the Hall of Justice (post game). Checked end to end with a test build (NERO_TEST=1 makes his team one level 2 CATERPIE; never in the release ROM): arrest path with Father shows the proud ending and the Hall of Justice follows.
- Step 6 done (tools/story_native.py, story/story_native.c compiled with clang like leg2): REPUTATION = clamp(100 + blessings - kills + story adjustment, 0..200), VAR_REP; the story adjustment is VAR_REPADJ (0x40E9, stored as 1000 + adjustment, set at new game; Nero's choices move it: arrest +20, execute -30, crowned -10). Shop prices (item price getter hook at 0x9a916, trampoline in free padding 0x3b2450) are scaled +1% per point below 100 and -1% per point above (minimum 1), applies to buy and sell; at reputation 0 the pokemart script command (table entry 0x86) is replaced and the shopkeeper refuses ("No. Not for you."). Checked with a test script: price 935 / 335, refusal at -100. The rep_expensive / rep_discount / rep_free texts are not used (silent scaling, the KARMA menu shows kills and blessings).
  MAX FIGHTS AS HERSELF: hook at the CreateTask call of the battle start task (0x7f6a2, trampoline 0x3b2480). If the party has no usable POKeMON (all fainted or empty) and fewer than 6 mons, MAX (species 255, Lv 1, Caterpie stats, TACKLE, CryMon art) joins at the end of the party and fights ("Go! MAX!"); once a usable POKeMON exists she is removed at the next battle start, and the white-out script removes her too. Checked: with 3 fainted mons a wild battle sends out MAX (11 HP). With a full party of six fainted mons nothing is added (no slot; the normal loss applies). The free-padding trampolines used are 0x3b2450, 0x3b2480.
- Step 7 (tools/story_nero.py, tools/story_base1.py): every text that named GENERAL GORE (quest log JRA: GENERAL and HALL OF JUSTICE entries, Hall of Justice lines, the old camp lines) now says NERO (in place, same length; 19 hits, GOREBYSS untouched). The Pewter base Captain opens with the story's lines about the cell ('captain_defeat_intro'). ROM CRC32 3bd1dc87, md5 24c66c74824c4285ac48603f7bd53c50; IPS regenerated and verified; saves/ported state re-paired. Old saves (VAR_STORY 0, no init) behave as before: crime scenes visible, no story hooks except the shop and MAX native code.
- FIX (variable collision): gun.c keeps the Hall of Justice team record in vars 0x40EC..0x40EE (and rob.c uses 0x40E4/0x40E5, gun.c 0x40E8), which the story had taken for VAR_STORY / VAR_REP / VAR_NERO. They are now VAR_STORY 0x40E6, VAR_REP 0x40E7, VAR_NERO 0x40EA (VAR_REPADJ 0x40E9, VAR_YV 0x40EF, VAR_CHOICE 0x40F0 unchanged). Checked from a cold boot: STORY 1, REP 100, REPADJ 1000 after the first frames, Hall vars untouched. ROM CRC32 c7ae4a5d, md5 a191d0a82e04df3d6ddb149ec0cc3ced. release.sh now stops if the build fails (an earlier run silently kept the old ROM).
- CHANGE (MAX stand-in, supersedes the Step 6 description): MAX is now used ONLY when the party is completely empty (count 0; all-fainted parties are left alone) and only for the length of that one battle. The battle-start hook (max_prepare) creates her, and wraps gMain.savedCallback (the battle's end callback, kept in vars 0x40EB / 0x40F1) with max_after, which removes her on the first frame back in the overworld and then runs the real callback. She is therefore never visible in the party menu on the field, and the moment the player owns a Pokemon she cannot be added (the party is not empty). Without the hook an empty party sends out the game's own placeholder: a Lv 0 species-0 mon with a "?" sprite and 0/0 HP. Checked on the ROM: empty party + wild Lv 2 CATERPIE: Go! MAX!, she wins and levels up, party count 0 and the party memory all zero afterwards; empty party + wild Lv 50 PIDGEY: she loses, white-out to the Pokemon Center, party count 0. ROM CRC32 b4bab249, md5 12ec4f59cf55c251c8d976d56783cff2.
- CHANGE (MAX): her HP and max HP are 1 for the battle (SetMonData 0x39 / 0x3a after CreateMon). When she falls the game takes the same road as being shot: after the white-out the Pokemon Center scripts start with a check; an empty party (native party_empty, GSV 0x8007) means MAX died, so the player goes to HEAVEN (2,80 at 8,25) with reputation 100 or more, HELL (2,68 at 11,23) below (rep_calc), with the same two lines as gun.py ('Something warm lifts you up' / 'Flames rise to meet you'). Checked: empty party, wild Lv 50 PIDGEY: reputation below 100 lands in HELL with Giratina, with the reputation raised (VAR_REPADJ 1400) in HEAVEN.
- FIX (earlier Step 4 bug): the Bloody ending hook had been put on the wrong literal (0x7f5ec, only one of the two after-white-out scripts) and was only ever tested by calling it directly. Both literals (0x7f5cc -> 0x081a8d97 and 0x7f5ec -> 0x081a8dd8, the two scripts that run after the player wakes in the Pokemon Center) now start with the story checks. Checked end to end: VAR_YV 4 and a real blackout plays the Bloody cards, THE END and the soft reset. ROM CRC32 1d47da69, md5 765d573da7dc5f114c1c21cff3a1fdf7.

## Rebuild check (2026-10-16)
`sh tools/apply_all.sh OUT.gba` (run with the /home/claude/work symlink in place, ~20 s) rebuilds `roms/Pokemon War and Murder.gba` byte for byte: CRC32 1d47da69, 16,777,240 bytes, 0 differing bytes. The build chain works from this repo.

## Protagonist is LEAF; stand-in is Hitmonchan-based (2026-10-16)
- Save name: LEAF (tools/cry_open.py). The rival stays MASON. Checked in the harness on a cold boot: player LEAF, rival MASON, start (4,5).
- Story text: every MAX/Max speaker label and narration line is LEAF/Leaf (story_assets/text/story_text.json, strings only). Code comments updated.
- Stand-in species 255 is named LEAF with Hitmonchan's base stats and types (Fighting, from the ROM's species 107), art story_assets/chars/leaf_front.png (pret trainers/front_pics/leaf_front_pic.png) and leaf_back.png (the top 64x64 frame of pret trainers/back_pics/leaf_back_pic.png). Learnset is still TACKLE only: the Hitmonchan list needs the new move slots below.
- Not done: Hitmonchan learnset, new moves Bitch Slap, Ball Throw and Hyperpunch (needs extended move tables: MOVES_COUNT 355 is a sentinel in several engine routines), throw animations.
- ROM CRC32 f2862d89. IPS regenerated from the outlaw base (roms/outlaw-2015-09-05 ..., CRC32 5e460b23) and verified byte for byte.
- The MAX art files (chars/max_front.png, max_back.png) are no longer used by the build.

## Three new move slots and the Hitmonchan learnset (2026-10-16), tools/moves_extend.py
- Move count 355 -> 358: 355 BITCH SLAP (power 30, accuracy 100, Fighting, 20 PP), 356 BALL THROW (power 50, accuracy 100, Fighting, 15 PP), 357 HYPERPUNCH (Hyper Beam's recharge record: power 150, accuracy 100, Fighting, 5 PP). Their battle animation is TACKLE's for now.
- Moved tables: move data, names, descriptions and the battle-animation table now live in free space at the end of the ROM. Every 4-aligned pointer to the old tables was repointed (137, 32, 2, 1). No unaligned matches.
- Sentinel: the two code literals holding the move count (0x40238, 0x933e8) are 358. The other literal-pool 355 words (0x1666d4, 0x237e28, 0x3b8500, 0x46b5fc) are flag or data values (0x163 is FLAG_HIDE_ROUTE25_TM43), left alone.
- Learnsets for Hitmonchan (107) and LEAF (255): Lv1 Bitch Slap, 7 Mach Punch, 10 Ball Throw, 13 Pursuit, 15 Barrage, 18 Spike Cannon, 20 Revenge, 21 Swift, 23 Ice Punch, 24 Thunderpunch, 25 Fire Punch, 27 Sky Uppercut, 30 Shadow Ball, 33 Mega Punch, 35 Sludge Bomb, 37 Counter, 40 Egg Bomb, 45 Hyperpunch. Detect is removed.
- Checked: move records, names, descriptions, animation entries and learnsets read back from the built ROM. The boot test (newgame_test) passes: player LEAF, rival MASON, start (4,5).
- Not checked yet: a battle using the new moves (needs a scripted encounter or encrypted party edit in the harness). Throw animations for Ball Throw and Shadow Ball are not wired in.
- ROM CRC32 37988abc. IPS regenerated and verified against the outlaw base.

## CryMon reference and Anne (2026-10-16)
- CryMon source: github.com/xenodorian/CryMon, cloned read-only to /home/user/xenodorian/crymon (commit c63dda5). Dialogue is in content/dialogue.json (talk.* keys). The cottage, Mason and Anne extract is docs/crymon_reference/dialogue_cottage.txt.
- Anne is a little girl (pret OBJ_EVENT_GFX_LITTLE_GIRL = 17) in Pallet and in the story Anne outside base 1. Her gift is six POKé BALLS and a POTION (CryMon wording; the potion line comes after the balls).
- ROM CRC32 0340bba9 (computed as 0x0340bba9 from the build log).
- Not done: Mason's dialogue still uses the earlier adaptation (CryMon text is in the reference file). Max NPC, Viridian arrest cutscene, double battles with Max, soldier 1 and 2 battles and outcomes, XP Share and gun pickup, Arceus/Giratina death system driven by reputation, PC-or-withdraw prompt, throw animations, and the battle test are all still open.

## Mason's CryMon dialogue (2026-10-16)
- The Pallet intro and the after-battle lines are CryMon's masonFight and masonAfter/masonWin lines (tools/cry_open.py mason_intro, mason_after). CryMon "CryMon" is "POKéMON" here and "crystal" is "ball". Calder, the Weeping Army and the Prison are kept as in CryMon.
- The CryMon tip line after Mason's win ("Tall grass hides CryMon. Wren has salve...") is not used; it names characters this game does not have.
- The battle is not triggered by a test yet: see the battle test note below.
- ROM CRC32 4b9023d6.

## Battle test (2026-10-16): passes
- tools/battle_test.py builds a TEST ROM where stepping onto the house door starts a wild Pidgey battle (cry_open.py, gated on TEST_BATTLE=1; release builds are unaffected and verified byte-identical).
- Result: wild PIDGEY appears, LEAF (stand-in, Lv 1, 1 HP) goes out, the move menu shows BITCH SLAP 1/20 PP TYPE/FIGHT. LEAF faints to Tackle and the white-out runs without a crash. Damage from Bitch Slap was not read from RAM.

## Progress status (2026-10-16)
Done and pushed to main:
- Repo: outlaw base ROM restored; Aladdin Sane removed. c3_build_base and m_final_latest_build are still in the repo (their removal was blocked; not deleted). /home/claude/work symlink to the repo; out/ and shots/*.ppm ignored.
- Build: tools/apply_all.sh rebuilds the release ROM byte for byte (`roms/Pokemon War and Murder.gba`, CRC32 4b9023d6), and the IPS patch reproduces it from the outlaw base.
- Protagonist is LEAF (save name, story text). Stand-in species 255 is LEAF: Hitmonchan stats and Fighting type, Leaf art.
- Three new move slots: 355 BITCH SLAP, 356 BALL THROW, 357 HYPERPUNCH (tools/moves_extend.py). Hitmonchan (107) and LEAF (255) learnsets set to the spec list.
- Anne: little girl sprite, six Poke Balls and a Potion, CryMon wording.
- Mason: Pallet intro and after-battle text are CryMon's lines.
- Battle test: passes (tools/battle_test.py, TEST_BATTLE hook on the house door). Wild Pidgey battle, LEAF stand-in out, BITCH SLAP shown with 1/20 PP, TYPE/FIGHT.

Not done:
- Throw animations (Ball Throw first, then the other seven reference moves). Only the reference notes in leaf_throw_anims/ exist.
- Bitch Slap / Ball Throw / Hyperpunch use TACKLE's battle animation. Damage not yet read from RAM.
- Max as an NPC (child sprite), the Viridian arrest cutscene, double battles with Max's Pikachu and then Raichu, the soldier fights and outcomes, the XP Share and gun pickup.
- Reputation-based death (Arceus or Giratina), PC-or-withdraw prompt for a full party, normal white-out.
- Hyperpunch type: Fighting (resolved 2026-10-16, matches the other punches).
- Leaf back art is the top frame of pret's back sheet; revisit later.

## Environment setup on the cloud box (2026-10-16)
- Box rebuilt: python3.13 with keystone-engine, capstone (needed by tools/story_party.py, not listed before), Pillow, numpy, scipy, scikit-image (pip --break-system-packages); clang/lld/llvm-objcopy 19.1.7, arm-none-eabi-gcc; libmgba0.10t64 (apt) so tools/harness_ls and harness_new run. /home/claude/work symlinks to /workspace/Pokemon-War-and-Murder; /tmp/claude-0 must exist for the test drivers.
- Rebuild check: `sh tools/apply_all.sh out/rebuild.gba` gives 16,777,240 bytes, CRC32 7c536327, not 4b9023d6. Only 5 bytes differ from roms/Pokemon War and Murder.gba, at 0xf62a67 and 0xf62ab0..b3, inside the clang-compiled thumb code (signed vs unsigned branch, push/pop vs mov); this is the compiler version (clang 19.1.7 here), not a source change. roms/ was not replaced. newgame_test passes on both ROMs (LEAF, MASON, start 4,5). The 5 bytes were not analysed for behaviour.

## Step 2 and 6: move damage and PP read from RAM; two bugs fixed (2026-10-16)
- Bug 1: the three new moves started a battle with 1 PP (shown 1/20). Cause: eight code literals point at the old move table plus 4 (the pp field) and were not repointed. tools/moves_extend.py now repoints them. Checked: Bitch Slap shows 19/20 after one use, then 18/20.
- Bug 2: the battle text said "a FIGHTING move" instead of the name. Cause: three compares in the battle message code (0xd75fc, 0xd7e96, 0xd7eae) used the old limit 354. They now compare below 358. Checked: BITCH SLAP!, HYPERPUNCH! print. Metronome's own limit is left alone, so the new moves cannot be picked by it.
- tools/damage_test.py (new) builds a test ROM (cry_open.py env TEST_GIVE=species,level and TEST_FOE=species,level, test builds only), starts the battle at the house door, uses one move slot and prints player and enemy HP from gBattleMons. It needs out/user_new.raw (a new-game state: harness_new with SAVEAT=1499 SAVEOUT=out/user_new.raw on a cold boot, keys as in newgame_test; out/ is ignored by git, so recreate it).
- Results (Hitmonchan stand-in species 107 given at the level shown; foe Magikarp, which only Splashes):
  - Bitch Slap (power 30), Lv12 vs Lv30 Magikarp (54 HP): 5 damage.
  - Ball Throw (power 50), same fight: 8 damage.
  - Hyperpunch (power 150), Lv45 vs Lv70 Magikarp (123 HP): 89 damage, then "must recharge!". Menu shows PP 5/5, TYPE/FIGHT.
- Step 6 confirmed: Hyperpunch type is Fighting (menu TYPE/FIGHT and move record). Bitch Slap and Ball Throw also show TYPE/FIGHT.
- Release ROM updated: the repo ROM plus only the 30 bytes this fix changes (the 5-byte compiler difference from a fresh build is not mixed in). CRC32 a5920d7c. IPS regenerated from the outlaw base and verified. saves/ported state re-paired. newgame_test passes (LEAF, MASON, 4,5). Verified in the emulator only.
- Push status: the GitHub connector only writes text, so the rebuilt ROM, IPS and ported state (CRC32 a5920d7c) are NOT on GitHub yet; the repo copies are still CRC32 4b9023d6. Rebuild with `sh tools/apply_all.sh` then apply the 30-byte diff, or push the binaries once a git credential exists.
- Next: Ball Throw animation, then the other throw moves.

## Step 1: Leaf throw animations (2026-10-16), tools/anim_throw.py
- Symbols: pret/pokefirered built as FireRed 1.0 (sha1 matches) gives the full symbol map; see docs/ANIMATION_NOTES.md. This is the way to find any engine function or table address.
- New battle animation sprites: Leaf's five throw frames (tag 10289) and the Poke Ball (10290). The pic and palette tables were moved to free space with two more entries and every reference repointed.
- BALL THROW (356): attacker hidden, Leaf throws, the ball flies t=26..44 (18 frames, 34 px arc), then the Tackle hit (hit splat, target shake). BITCH SLAP (355): Leaf throw, Tackle hit at t=32.
- Swift, Barrage, Egg Bomb, Spike Cannon, Sludge Bomb and Shadow Ball: Leaf's frames are added in front of the original animation (effect at t=26; Shadow Ball: Leaf starts when the ball appears), only when the attacker is Hitmonchan or LEAF. A native check task (thumb, in free space) sets a flag read by jumpargeq. Checked: Staryu's Swift still shows the original animation.
- Checked in the harness (screenshot sheets, Magikarp foe): Ball Throw, Bitch Slap, Swift, Barrage, Spike Cannon, Shadow Ball, Egg Bomb, Sludge Bomb all play, Hitmonchan returns afterwards, no hang. Timing and positions are close to leaf_throw_anims/TIMING.md but were judged by eye from screenshots, not frame-measured. Hyperpunch has no reference animation and still uses Tackle's.
- Release ROM rebuilt as repo ROM plus the build diff: CRC32 60efbd76. IPS regenerated and verified; saves/ported state re-paired. newgame_test passes. These binaries are not on GitHub (connector is text only).
- Next: Step 2, the Max NPC and the Viridian arrest cutscene.

## Handoff open item: null script pointers (2026-10-16), tools/mtmoon_fix.py
- Scanned allmaps.txt (decoded from the ROM) for trainer-type objects whose script is missing or not a trainerbattle. Only two exist: Route 11 JASPER (already fixed) and Mt. Moon B2F local id 6, the Rocket at (35,12). The other entries in the handoff list (Cerulean 10, Celadon 13, Five Island 3, Route 4 7, Route 7 1, Route 15 14, Sevault Canyon 7) are vanilla "clone" objects (border trees and guards copied from the neighbouring map), not broken scripts.
- The Mt. Moon Rocket's template has script pointer 0x08000000 in the Outlaw base ROM too (vanilla points to 0x08160829). The original script is intact in the ROM, so the pointer is restored. Without it, talking to him would run the ROM header as a script.
- Not confirmed in the emulator: after a TEST_WARP (new test hook in cry_open.py, tools/warp_test.py) the player would not move in my test state, so the fight could not be walked into. Checked from ROM data only (template and script bytes). The 0x81be11d Seafoam / Victory Road script was not looked at.
- ROM CRC32 bbe90f02 (repo ROM plus the 3-byte change on top of the previous build diff). IPS regenerated and verified; ported state re-paired. Not on GitHub (binary).

## Standing orders from the owner (as stated in the session, 2026-10-16)
- Work only on `main`.
- The owner reversed the old rules: upload anything to the repos, including ROMs and art (`git add -f` for ignored types).
- Decisions are delegated: use best judgement, record the choice, keep going.
- Install any tool needed; use the owner's ROMs and any repo data freely.

## Blocked: steps 2 to 4 need a spec (2026-10-16)
- Max NPC, the Viridian arrest cutscene, the double battles with Max's Pikachu and Raichu, soldier 1 and 2 fights and outcomes, XP Share and gun pickup, the full-party death outcome and the PC-or-withdraw prompt have no written spec in this repo, CryMon, or the handoff (only the one-line mentions above). The handoff rule is to confirm before editing when a request is unclear. Needed: who Max is in this ROM (the Leaf stand-in is species 255, so is Max a separate child NPC?), the arrest scene beats and location, what the soldiers' fights award, and when the PC-or-withdraw prompt shows.

## Repo sync and release ROM (2026-10-16)
- Merged origin/main (fc883bb) into local main with no conflicts. A fresh build from the merged tree (apply_all.sh with no TEST_* variables) gives CRC32 bbe90f02, which matches the latest release CRC in the notes above.
- roms/Pokemon War and Murder.gba and Pokemon War and Murder.ips updated to that build; the IPS reproduces the ROM from the outlaw base.
- Local state added to the repo: saves/ported/new_game_empty_party.raw (empty-party new-game state, used by tools/battle_test.py). Ignored by .gitignore only as a rule for the file itself: it is tracked; see .gitignore.
- docs/handoff/grok_handoff.txt: handoff text for Grok (answers to the four spec questions). Its ROM CRC line is out of date; use bbe90f02.
- Not in the repo: the re-paired saves/ported/Pokemon War and Murder.state that the notes above say was re-paired on another machine. This session does not have it. Upload it to the repo or send the file to re-create it.

## Written spec for steps 2 to 4 (2026-10-16)
- docs/SPEC_ARREST_AND_PARTY.md: Max as a girl NPC, the Viridian arrest, the double battle (LEAF + Max Pikachu Lv10 vs Totodile/Cyndaquil/Chikorita Lv5 and Squirtle/Charmander/Bulbasaur Lv5), win and loss outcomes, XP Share, gun pickup, run mode (NORMAL or PLAYABLE), LEAF as a permanent party member, and the PC-or-withdraw prompt.
- Ambiguities decided with defaults and listed in section 12 of the spec (soldier 2's line, Max's sprite, run-mode choice point, LEAF's party status, the arrest stop tile). Confirm these; the build proceeds on the defaults.
- The spec unblocks steps 2 to 4. Build order: step 2 (Max NPC and arrest), then step 3 (double battle and outcomes), then step 4 (PC prompt and death rules).

## Open items resolved (2026-10-16)
- Hyperpunch type: Fighting. Resolved.
- c3_build_base.gba and m_final_latest_build.gba: KEEP in roms/. They are not deleted; the user asked for them to stay. Not awaiting any action.
- Mason's CryMon names (Calder, Weeping Army, Prison): kept, per the user.
- Spec decisions: docs/SPEC_ARREST_AND_PARTY.md section 12, all resolved.
- Push method for binary files: the GitHub connector is text-only. Binaries (ROM, IPS, states) are pushed with git from the cloud box (git push origin main), which works.

## Steps 1 to 3: Max, the Viridian arrest, the double battle and both outcomes (2026-10-16)
- New: tools/story_viridian.py (from the stopped worker's scratch file, finished: it needed ids, native helpers and a working trigger), tools/story_viri_native.py + story/viri_native.c (viri_prepare, viri_cleanup), ids in tools/story_ids.py (flags 0x840..0x849, VAR_VIRI 0x4090, vanilla unused). Added to tools/apply_all.sh before story_nero.
- Max is a separate child NPC (pret LITTLE_GIRL 17), two JRA soldiers (gfx 60) escort her. Trigger: a coord event on the road into Viridian City (map 3,1, tiles 22..25 at y=36, from Route 1), one time (VAR_VIRI). They walk in from the east along y=33 and stop at (22,33) soldier 1, (23,33) Max, (24,33) soldier 2. Max says "Let me go! PIKACHU, I choose you!". Talking to any of the three starts the fight. The coord event needed a real var as trigger: with trigger 0 the engine runs the script immediately (no lock), which did nothing.
- Double battle (trainer 744, class JRA SOLDIER, name ESCORT, one record with both soldiers' teams interleaved so each leads): Totodile, Cyndaquil, Chikorita and Squirtle, Charmander, Bulbasaur, all Lv 5. MAX's PIKACHU (Lv 10, marked by OT id MAX!) joins LEAF's party for the fight and is removed after it. Battle command is trainerbattle mode 9 (early rival, HEAL_AFTER): a loss does not white out, the script carries on. Trainers cannot be escaped in this engine (RUN fails).
- Limits (decisions): this is a normal double battle where the player controls both Pikachus' side (FireRed has no AI partner battles). If the party already has 6 Pokemon Max's Pikachu is not added. With an empty party Pikachu fights alone (the LEAF stand-in is dropped, because it is only used with an empty party).
- Win: MAX "A traitor and a coward..." and SOLDIER 2 line, shot, splatter, SOLDIER 1 line and walks off, MAX line, EXP. SHARE given, MAX walks off. The GLOCK drops on the tile beside the splatter (25,33) as a pickup ball; one time (F_GUNTAKEN). Loss: same two lines, two shots, MAX is a splatter for good (F_VLOST, shown on every map load), then HEAVEN or HELL by VAR_REP like being shot. Map load restores each state from flags.
- Not done yet: MAX's soul returning once in the afterlife, and the NORMAL/PLAYABLE run rule for this loss (step 4: until then the loss always sends LEAF to heaven or hell).
- Verified in the emulator only (tools/viri_test.py, tools/viri_ram.py; sheets in shots/viri_*.png): the arrest walk and line; a real double battle won with a strong test mon (win branch, EXP. SHARE obtained, flags correct); a real battle lost with soldiers at Lv 70 (VIRI_LEVEL, test only: no white-out, MAX splatter, heaven); the gun pickup; the branches also with the VIRI_FORCE=win|lose test switch (test only). newgame_test and battle_test pass.
- Release ROM regenerated as repo ROM plus this build's diff (the 5 compiler bytes stay as in the repo): CRC32 ce76c32e (was bbe90f02); IPS regenerated and verified from the outlaw base. The re-paired saves/ported state was not regenerated (not on this machine).

## Step 4a: run mode and the death rule (2026-10-16)
- The run mode is asked once at the house door, after the Sandshrew is taken and before LEAF leaves (tools/cry_open.py, door script): "Play as a POKeMON? A lost battle means death." YES sets F_PLAYABLE (0x84A), NO leaves it clear; F_MODEASKED (0x84B) stops the question repeating. Checked in the harness: YES gives flags 0x84A=1,0x84B=1, NO gives 0x84A=0,0x84B=1.
- Death rule (tools/story_yveltal.py, both after-white-out scripts): PLAYABLE (flag set) means any lost battle is death, HEAVEN with VAR_REP >= 100, HELL below, same as being shot. NORMAL means the usual white-out. Before this, an empty-party stand-in loss always went to the afterlife; now it depends on the mode.
- Viridian loss (tools/story_viridian.py): shots, MAX splatter for good, then PLAYABLE goes to heaven or hell; NORMAL does the usual white-out (special 200) and wakes in the Pokemon Center. Simplification: in a NORMAL run the afterlife visit is skipped.
- Checked (emulator only): NORMAL Viridian loss runs the hack's own black-out joke screen and wakes in the Pokemon Center ("Let's pretend like that didn't happen"); PLAYABLE Viridian loss reaches HEAVEN; PLAYABLE wild-battle loss reaches the sky afterlife. newgame_test passes.
- Release ROM CRC32 bf0b2c02 (now identical to a fresh apply_all.sh build; the cry_open change shifted the layout so the old 5 compiler bytes no longer differ). IPS regenerated and verified. saves state not regenerated.
- Next: LEAF as a permanent party member and the PC-or-withdraw prompt (step 4b).

## Step 4b: LEAF as a real party member and the PC-or-withdraw prompt (2026-10-16)
- Decision: the full option, not the smaller one. LEAF (species 255, Lv 5, her own OT id, normal HP and moves) joins the party the moment the shelf script gives the Sandshrew (cry_open calls story_native leaf_join through a trampoline at 0x3b24b0). The empty-party stand-in is unchanged but now carries an OT marker (STND), so max_remove only drops the stand-in and a real LEAF is never removed.
- Prompt (story/story_native.c, tools/story_native.py): max_prepare records at battle start whether the party was full (6) and held the real LEAF (VAR 0x4091). The battle-end wrapper max_after, on outcome CAUGHT, queues a script and returns through CB2_ReturnToFieldContinueScript. FireRed already sent the new POKeMON to the PC, so the prompt is: "Your party is full. Send X to the PC?" YES leaves it there. NO asks "Remove LEAF from combat?": YES swaps (LEAF takes the PC slot, the new POKeMON takes her party slot, "LEAF waits in the PC. X joins you."), NO returns to the first question.
- Bug fixed: viri_prepare used OT type 2 (random) instead of 1 (preset), so Max's Pikachu was never found for removal. Now checked: after a real won Viridian fight the party is back to 1 mon.
- Checked (emulator only): shelf gives party of 2 (Sandshrew + LEAF); a Master Ball catch with a full party (4 Pidgey, 1 Machamp-class test mon, LEAF) shows the prompt; NO then YES swaps and the party stays at 6 with the new mon in LEAF's slot; YES-to-PC path shows "sent to the PC". The loop on NO at the second question is by script construction, not run. battle_test (stand-in) and newgame_test pass. tools/viri_test.py gained B, VIRI_NODOWN, VIRI_WARP=none; cry_open test hooks TEST_GIVE_MORE, TEST_MASTER, TEST_LEAF (test only).
- Limitation: LEAF is not removed when a catch happens with fewer than 6 mons; the prompt only runs for a full party that contains her. A '?' or '!' at the very end of a field message box looks clipped in the screenshots; this is the existing font box, not checked further.
- Release ROM CRC32 1bcc3073 (identical to a fresh apply_all.sh build); IPS regenerated and verified.

## Partner AI for Max's Pikachu (2026-10-16)
- Source: pokeemerald PlayerPartnerHandleChooseAction / PlayerPartnerHandleChooseMove, ported to FireRed in story/viri_native.c (partner_choose_action, partner_choose_move). The Outlaw ROM matches pret layout, so sPlayerBufferCommands (0x0825089c) entries 18 (CHOOSEACTION) and 20 (CHOOSEMOVE) are repointed by tools/story_viri_native.py to wrappers. They run only for battler 2 while VAR 0x4092 = 1 (set by viri_prepare, cleared by viri_cleanup); otherwise they call the original handlers. The move choice uses FireRed's BattleAI_SetupAIData / BattleAI_ChooseMoveOrAction and the same target fixups as the opponent controller, then emits action 10 (exec script) like Emerald.
- viri_prepare now inserts Pikachu at party slot 1 so it is the second player-side battler. Not added if the party is empty or full (then LEAF fights alone, as before).
- Deviations, decided: AI_TrySwitchOrUseItem is skipped (FireRed shares one party, so it could switch Pikachu for the player's reserves; it emits plain "use move" instead). Choose-Pokemon after a faint stays the player's menu. No Max back sprite or partner trainer pic (Pikachu is sent out as a normal mon). AI flags are the escort trainer's.
- Verified in the emulator only: with Sandshrew Lv20 + LEAF, the player gets a menu only for battler 0; "PIKACHU used TAIL WHIP / GROWL" and Static paralysis happen with no input; full battle won, win flags set, party back to 2 (Pikachu removed), partner var cleared. newgame_test and battle_test run OK. Loss path unchanged (cleanup shared) but not re-run.
- Release ROM and IPS regenerated: CRC32 0xe9f07b78 (was 1bcc3073). IPS re-verified from the Outlaw base.
- Still to do: step 5 items (Raichu later battles, Hyperpunch animation, Mt. Moon check, afterlife beats).

## Step 5.1: Max's later Raichu double battles (2026-10-16)
- Check first: after the story_gen.h revert a fresh apply_all.sh build matched the release ROM (CRC32 e9f07b78).
- New tools/story_ambush.py (in apply_all.sh before story_nero). The spec only says "placed at the story points listed in CURRENT_WORK" and none were listed, so decided: A Cerulean City road (coord trigger x 28, y 21..23; soldiers Lv 22 with Growlithe/Pidgeotto and Raticate/Arbok; Raichu Lv 24) and B Vermilion City road (trigger x 30, y 18..21; soldiers Lv 30 with Arcanine/Dodrio and Rhydon/Exeggutor; Raichu Lv 32). Each plays once, only after the Viridian fight was won (F_VWON, so MAX is alive).
- Flow: MAX and two JRA soldiers appear, MAX shouts, the double battle starts at once (trainerbattle mode 9, new trainer records 745 and 746) with MAX's RAICHU as the AI partner (same viri_prepare/viri_cleanup and partner AI; viri_prepare now reads VAR 0x4093/0x4094 for species/level and falls back to Pikachu Lv 10, cleanup resets them). Win: soldiers retreat, MAX gives a RARE CANDY and leaves. Loss: heal and carry on, soldiers leave, MAX survives (only the Viridian loss kills her). Actors are hidden on every map load. New ids in story_ids.py: flags 0x84C..0x853, vars 0x4095, 0x4096.
- Edge case (as in Viridian): if MAX's Raichu faints the player gets the normal choose-a-Pokemon prompt for that slot and can send in a reserve.
- Verified in the emulator only (Cerulean, tools/viri_test.py with VIRI_FLAGS=0x847 and TEST_GIVE; AMB_LV=5 is a test-only switch that lowers the soldiers' level): scene and line, Raichu acts alone (Tail Whip, Quick Attack, Growl with no input), win branch text, RARE CANDY obtained, actors gone, flags 0x84C..0x84F set, party back to 2. Not run: the loss branch and the Vermilion site (same code, other coordinates). newgame_test and battle_test run OK.
- Release ROM and IPS regenerated: CRC32 0x24664883 (was e9f07b78); IPS re-verified from the Outlaw base.
- Next: Hyperpunch animation, Mt. Moon check, afterlife beats.

## Step 5.2: Hyperpunch's own animation (2026-10-16)
- New tools/anim_hyperpunch.py (in apply_all.sh after anim_throw.py). Hyperpunch (357) no longer uses Tackle's animation: its script is the original Mega Punch body (charged fist, white flash on the target, impact background, heavy shake) followed by the original Dynamic Punch body (second fist, shake, five explosions on the target). Both are copied command by command from the ROM's own scripts (pret data/battle_anim_scripts.s), so no new sprites are needed; the first body's closing end is dropped so they run back to back.
- Decision: not wrapped with Leaf's throw frames (those are for the throw moves; anim_throw.py's Leaf-first rule applies only to the moves it lists). Limits: it is a longer animation (about 2.5 s); the damage and 150 power recharge effect are unchanged.
- Verified in the emulator only: tools/anim_test.py 60 3 16 20 (Hitmonchan Lv 60 uses HYPERPUNCH on a Pidgey): fist charge, impact flash, second fist and explosions, then the faint. newgame_test and battle_test run OK.
- Release ROM and IPS regenerated: CRC32 0xa43eaf21 (was 24664883); IPS applied to the Outlaw base reproduces the ROM (checked by CRC).
- Next: Mt. Moon check, afterlife beats.

## Step 5.3: Mt. Moon B2F Rocket in-game check (2026-10-16)
- Result: the fix works in the emulator. Talking to the grunt at (35,12) shows his line ("You look like a pussy or a snitch. Are you a POLICE intern or something?"), then the battle transition and "TEAM ROCKET GRUNT would like to battle!", he sends out RATTATA Lv 13, the command menu comes up. No crash. Screens: shots/mtmoon_talk.png, shots/mtmoon_battle.png. Emulator only.
- Why it looked frozen before: the player was not frozen. Two things hid the grunt: he is hidden by FLAG_HIDE_MISC_KANTO_ROCKETS (0xAD, set in a new game), and his movement type is "face down" with sight 4, so he only sees a player standing south of him in his column. The earlier test warped to a spot where he was not spawned and nothing was in his line. tools/viri_test.py gained the test-only env VIRI_CLEAR=0xad (pokes the flag byte to zero before the door warp so the object spawns). Command used: VIRI_WARP=1,3,40,12 VIRI_CLEAR=0xad TEST_GIVE=27,30 TEST_LEAF=1 viri_test.py "W100 L2 D1 L3 W200 U1 A3 W100 A3 W400 A3 W400".
- Limit: the walk-into-sight trigger did not fire in this run (player stood at (35,13) directly below him, but only after arriving by walking; I then pressed U and A to talk). The fight starts by talking, which is what the restored pointer fixes. Not investigated further, the sight check is vanilla engine behavior and he is a vanilla object.
- 0x081be11d (the Seafoam/Victory Road script): the bytes decode as an ordinary script (special, compare, goto_if with valid pointers), nothing broken; not run in game.
- No code changed, so the release ROM and IPS stay as they were (CRC32 a43eaf21).
- Next: afterlife beats.

## Step 5.4: the afterlife beats (2026-10-16)
- Spec reading (section 5b): after the Viridian loss "LEAF and MAX both die ... afterlife rule decides heaven or hell ... MAX also goes to heaven or hell, comes back to the screen once, and then STAYS DEAD ... In a normal run she is then taken to the Pokemon Center as a white-out would. In a playable run she dies permanently." So both run modes now visit the afterlife first (this reverses my earlier decision that the NORMAL loss skips the visit).
- New tools/story_afterlife.py (apply_all.sh after story_viridian). tools/story_viridian.py: the loss sets VAR_SOUL (0x4097) = 1 and always goes to heaven or hell by reputation (the NORMAL white-out branch was removed there). In heaven (2,80) and hell (2,68) MAX's soul is a hidden girl-sprite object (flags 0x854/0x855, shown only while VAR_SOUL == 1, set by a new on-transition map script). The first steps away from the arrival tile (coord events heaven y 24, hell y 22) show her, she speaks (one line pair per place), she fades, VAR_SOUL = 2 so she never returns. NORMAL run (F_PLAYABLE clear): then "A hand pulls you back toward the living" and special 200 (the same white-out as any lost battle: Pokemon Center). PLAYABLE run: LEAF stays dead; hell keeps its existing Giratina soul-sale prompt. Other deaths (shot elsewhere) never set VAR_SOUL, so no soul.
- Limit: the scene starts when the player steps off the arrival tile, not automatically on arrival (a warp ends the script; no new frame hook was added). MAX's splatter in Viridian stays for the rest of the game (F_VLOST, unchanged).
- Verified in the emulator only (VIRI_FORCE=lose skips the battle; the real lost battle was verified in 4a): NORMAL run, heaven: loss lines, heaven, soul appears and speaks, "A hand pulls you back", white-out, Pokemon Center with the nurse. PLAYABLE run, hell (reputation forced low with the test poke VIRI_POKE=0x11d2=0xb6,0x11d3=3): soul appears beside LEAF, speaks, fades, Giratina's prompt, back in Viridian with the splatter. Not run: PLAYABLE heaven end to end and the "never twice" second death (by construction VAR_SOUL = 2). New test-only env VIRI_POKE in tools/viri_test.py. newgame_test and battle_test run OK.
- Release ROM and IPS regenerated: CRC32 0x16ba9580 (was a43eaf21); the IPS applied to the Outlaw base reproduces the ROM (CRC checked).

## Build pass 1: soul scene starts automatically on arrival (2026-10-16)
- Owner priority change: build first, run the full test pass after everything is built. Gaps still open from the testing list (Vermilion Raichu site, Raichu loss branch, PLAYABLE heaven end to end, Mt. Moon sight trigger, 0x81be11d) stay open until that pass.
- tools/story_afterlife.py now also adds an on-frame map script table (map script type 2: VAR_SOUL == 1) to heaven and hell, so MAX's soul scene starts by itself on arrival; the coord events stay as a fallback. Boot-checked only: hell, PLAYABLE, no key pressed after the warp: soul appears, speaks, fades.
- Release ROM and IPS regenerated: CRC32 0x3d86d910 (was 16ba9580); IPS applied to the Outlaw base reproduces the ROM.

## Build pass 1 follow-up: what is still not built (2026-10-16)
- Review of STORY_PLAN, the spec, the handoff and CURRENT_WORK: everything they describe is built except the items below. Remaining "Not done" lines in older sections (Throw animations, Bitch Slap animation, PC prompt, reputation death, Max NPC and fights) were built in later steps; they are stale.
- NOT BUILT: Max's back sprite and partner trainer pic in the double-battle intro. FireRed draws a second player-side trainer pic only for BATTLE_TYPE_MULTI (link) battles; the multi flag also changes switch-in text, party summaries and link waits, and there is no FireRed code path for an in-game partner pic (Emerald's BATTLE_TYPE_INGAME_PARTNER and gPartnerTrainerId are new there). Doing it means new intro/slide/ball-throw handlers for battler 2 plus a Max back sheet (FireRed's trainer back pic table has only the player pics). Left as a cosmetic gap: Pikachu/Raichu is sent out as a normal mon after "Go! LEAF's mon and PIKACHU!". Not attempted because a wrong hook can hang every double battle.
- NOT BUILT: CryMon verbatim dialogue and Mason's Vallejo surname (the CryMon repo is gone), Leaf back art beyond the top frame of the pret sheet (needs new art).
- Boot checks only after pass 1: newgame_test and battle_test pass on 3d86d910. The Vermilion Raichu scene was reached and the double battle started (Raichu Lv 32 vs Arcanine/Rhydon Lv 70, F_BDONE set); the loss branch and win branch of Vermilion and the Mt. Moon / 0x81be11d / PLAYABLE-heaven checks are still open for the full test pass.

## Leaf art audit and full test pass (2026-10-16)
- Leaf battle-art rules found: leaf_throw_anims/README.md and TIMING.md (frames 0..4 from leaf_throw_anims/frames, timings 20/6/6/24/1, Poke Ball sprite only for Ball Throw, Shadow Ball keeps its own particle effect with no ball, other throw moves plain, no Cormag art), docs/ANIMATION_NOTES.md (Leaf frames only for Hitmonchan 107 or LEAF 255 on the wrapped moves; Hyperpunch not Leaf-wrapped). Owner order: no new Leaf sprites.
- Audit: tools/anim_throw.py uses only those frames and timings; the ball sprite is created only in the Ball Throw script; story_assets/chars/leaf_back.png is byte-identical to leaf_throw_anims/frames/leaf_frame0.png and leaf_front.png is the pret front pic, unchanged since its first commit. No deviation found, no change made. No Leaf art was painted.
- Mason has no surname (owner): none added. CryMon dialogue already applied earlier where the spec calls for it.
- Test pass on release ROM 3d86d910 (rebuilt from apply_all.sh, same CRC). Emulator only:
  - Raichu loss at Cerulean: pass (no white-out, soldiers leave, Raichu removed, party 2, F_ADONE set).
  - Raichu loss at Vermilion: pass (same).
  - Vermilion win: pass (soldiers retreat line, party back to 2, F_BDONE set).
  - PLAYABLE heaven end to end: pass (arrest, loss, heaven, MAX soul speaks once and fades, LEAF stays in heaven).
  - Second death: pass (VAR_SOUL=1 shows the soul, VAR_SOUL=2 after a second death shows no soul).
  - Script 0x081be11d: bytes are the stock Strength boulder script (special 0x187, badge 4 check); not run in game.
  - Mt. Moon sight trigger: grunt template is correct (trainer type 1, sight 4, script 0x08160829); not reproduced because a TEST_WARP leaves the player at the wrong elevation (blocked on ledges, no sight match). Talking to him works (step 5.3).
  - newgame_test and battle_test pass.
- Test lesson: with tools/viri_test.py the Viridian arrest only talks; walk to the soldiers and press A for the fight. A coord trigger needs a step onto the tile, not a warp onto it.
- No ROM or IPS change this step.

## Leaf throw animations vs reference GIFs (2026-10-16)
- Owner order: leaf_throw_anims/gifs/*.gif are the reference for how each move looks in game. Spike Cannon looked wrong (late volley, Leaf vanished, repeated round).
- Causes: (1) the original Spike Cannon script runs an attacker wind-up lunge and waits for it before the needles, about 28 frames late; (2) Leaf's throw sprite is destroyed when its animation ends (t=57) while the attacker battler stays hidden until the script ends; (3) the engine replays the animation for each multi-hit hit.
- Fixes in tools/anim_throw.py: lunge, its wait and the slide-back sprite removed for Spike Cannon (volley at t=26 from Leaf's hand); show-attacker task at t=57 for all Leaf scripts (Ball Throw, Bitch Slap, Swift, Barrage, Egg Bomb, Spike Cannon, Sludge Bomb, Shadow Ball); hits 2+ of Spike Cannon and Barrage play no animation; Shadow Ball hides the attacker only when the throw starts.
- Checked in the emulator only (Leaf vs Magikarp, harness screenshots, compared by eye to the GIFs): Spike Cannon, Barrage, Swift, Egg Bomb, Sludge Bomb, Shadow Ball, Ball Throw, Bitch Slap all keep Leaf visible and launch effects at the arm-extended frame (Ball Throw at ball landing, Bitch Slap at t=32). Timing is by eye, not frame-measured. newgame_test and battle_test run OK.
- Release ROM and IPS regenerated: CRC32 0x6ff443be (was 3d86d910); IPS applied to the Outlaw base reproduces the ROM.

## Build pass 2: MAX's back picture in the double-battle intro (2026-10-16)
- Built the item left open in build pass 1. No Emerald partner code path is needed: a follower sprite (story/viri_native.c, partner_draw_pic and max_follow) is added next to LEAF's trainer pic while VAR_PARTNER = 1. The DRAWTRAINERPIC entry (7) of sPlayerBufferCommands (0x0825089c) is repointed by tools/story_viri_native.py to a wrapper that calls the original handler and then creates the sprite from story_assets/chars/max_back.png (existing art, 64x64, converted at build time; palette in OBJ slot 2, which battler 2's mon only uses after the trainers are gone).
- Safety: the follower never changes battle state. Each frame it copies LEAF's pic position (slide in, ball throw, slide out) and destroys itself when LEAF's pic sprite is not in use, its slot holds another graphic, or after 600 frames. It is only created when the partner var is 1, so every other battle is untouched.
- Checked in the emulator only (Viridian arrest fight with a test Sandshrew): Max appears left of LEAF during "would like to battle", "sent out" and "Go!", leaves with the throw, the battle then plays normally (menus, Pikachu acting by itself). newgame_test and battle_test run OK.
- Release ROM and IPS regenerated: CRC32 0x32dfc7de (was 0x6ff443be); IPS applied to the Outlaw base reproduces the ROM.
- Still not built: Leaf art beyond the approved frames (owner: no new Leaf sprites), CryMon verbatim text that does not exist in the repos, Mt. Moon sight trigger reproduction and script 0x081be11d in-game run (test gaps, not build gaps).

## Test pass on CRC 0x32dfc7de (emulator-only, copies)
- Pass: Cerulean/Vermilion Raichu fights (win+loss, Max back pic, partner), PLAYABLE heaven, second death, newgame_test, battle_test.
- Mt. Moon grunt: movement type 7 is FACE_UP, so he sees only the tile column north of him. Walking in from the north (35,8 down) triggers dialogue and battle; approaching from the south never triggers (correct, not a bug). Earlier failed test approached from the south.
- Not run this pass: script 0x081be11d, full 8-move re-check, full-chain smoke, CryMon dialogue diff.

## Test pass part 2 on CRC 0x32dfc7de (emulator-only, copies)
- Script 0x081be11d: pass. It is the boulder script used by the Seafoam boulders (map 1,105, boulder at (12,5)); interacting without Strength shows "It's a big boulder, but a POKEMON may be able to push it aside." The push branch (badge plus field move) was not exercised.
- Eight GIF moves (Barrage, Swift, Egg Bomb, Sludge Bomb, Shadow Ball, Spike Cannon, Ball Throw, Bitch Slap, Leaf vs Magikarp, sheets /workspace/shots/final_*.png): pass by eye. Leaf stays visible, effects launch at the arm-extended frame, Ball Throw shows the ball only for itself, Shadow Ball keeps its own particle. Timing not frame-measured. Added tools/_anim_test2.py (anim_test.py with CHOOSE=frame env); slots: Barrage lv15, Spike lv18, Swift lv21, Shadow lv30, Sludge lv35, Egg lv40 are slot 3, Ball lv10 slot 2, Slap lv12 slot 0.
- Full chain: pass. opening_test (house, shelf Sandshrew, crate, door, Pallet, Mason's Pikachu battle) and Viridian arrest trigger (Max line, soldiers) run; end state Pallet, party 2.
- battle_test sheet: house, wild Pidgey Lv5 vs LEAF Lv1 (1 HP), menu shows BITCH SLAP 20/20, Pidgey Tackle, LEAF faints, white out.
- CryMon dialogue.json diff: 1152 talk, intro and mercy lines; only 91 (about 8 percent) appear in the repo text or ROM by first-28-character match. The ROM carries the Pokemon-adapted story (Leaf, Mason, Shinigami), the CryMon file is a different cast and setting, so the rest is not ported. No code bug; no change.
- No ROM or IPS change.

## Reconciliation audit (2026-10-16, against the live repo at 4f46de8)
Built and checked in the repo (code and notes): LEAF protagonist; Hitmonchan-based LEAF stand-in with Leaf front art and the pret back-sheet top frame (verified equal); moves 355 to 357 with the spec stats; Hitmonchan and LEAF learnset per spec (Mach Punch Lv7, Revenge Lv20, Ball Throw Lv10, Hyperpunch Lv45, Detect removed); Hyperpunch recharge; eight throw animations (Ball Throw alone shows the ball); Anne (little girl, six Poke Balls, potion); Mason's CryMon lines; Max NPC (sprite 17), Viridian arrest, LEAF+Max double battle with partner AI, win and loss branches, traitor line, XP Share, gun pickup, Cerulean and Vermilion Raichu battles, run mode (NORMAL or PLAYABLE), afterlife by reputation, LEAF as a party member, PC-or-withdraw prompt; battle test passes.
Partial or open:
- Agent permission allowlist (.claude/settings.json): NOT created. The write was denied earlier; needs the owner to approve it.
- CryMon dialogue: only the cottage, Mason and Anne lines and the spec lines are ported. The rest of CryMon's dialogue.json is not in the game (a different cast and setting, per the notes). The CryMon repo is NOT gone: it is at github.com/xenodorian/CryMon. The older note saying it is gone is wrong.
- Test gaps (not build gaps): Mt. Moon sight trigger not reproduced in the emulator; the push branch of script 0x081be11d not exercised; animation timing checked by eye only.
- Stale "Not done" lines in older sections (throw animations, Bitch Slap animation, PC prompt, reputation death, Max NPC and fights) are superseded by the built items above.
- docs/handoff/grok_handoff.txt is out of date (its CRC, not-done list and the save-state wording). Use this file and the notes above instead.
## Part A: MASON as the rival everywhere (2026-10-16, tools/story_mason.py)
- Enumerated the rival encounters actually present in this ROM from the trainer records and map scripts (the base hack rewrote many): Pallet Mason fight (743, already done), SS Anne (426), Pokemon Tower (429), Route 22 early (332, mode 9) and late (435), Cerulean (333) and Silph Co (432) (these two were LEAF girlfriend records in the base hack: now MASON records, class RIVAL, Gary picture, parties kept), Oak's lab scenes, the Sevii talk and the Route 22 talk. The League champion in this ROM is CJ, not the rival (champion rematch records 740/741 are named MASON but no script references them).
- All their intro, after and defeat lines are replaced (49 text pointers) with MASON trying to stop LEAF from marching on the Johto army and bring her home safe. No surname.
- Loss rule (story/story_native.c max_after, MASON_KO_SCRIPT in story_native.py): a lost or drawn trainer battle against a MASON record (ids 326..334, 426, 429, 432, 435, 740, 741, 743) skips the white-out, the afterlife and the PLAYABLE death rule in both run modes: dialog (Mason knocked her out and carried her home), party healed (special 0), warp to the Pallet house (map 4,0 at 5,7). No money loss.
- Test-only switches: MASON_TEST_LV and MASON_TEST_SPECIES (raise MASON's parties), TEST_TRAINER=id (cry_open test door starts that trainer), tools/mason_ko_test.py, OPENING_B and OPENING_SW in opening_test.py.
- Verified in the emulator only (tools/mason_ko_test.py: MASON Lv 80 Machamp beats the stand-in LEAF): "Player lost against RIVAL MASON", then the knock-out boxes, fade, and LEAF stands in her house, party healed, no white-out text. The PLAYABLE variant was not run separately (the hook runs before any run mode check).

## 2026-10-16 Part B: MAX recurring, silent, executed on loss; final-base sniper; combined release
- MAX never speaks now (Viridian, afterlife, ambush sites all use silent narration).
- Double-battle sites (all gated on F_VWON and not F_MAXDEAD): Viridian (3,1), Cerulean A, Vermilion B, Pewter C (3,2) trig x36 y14..16, Lavender D (3,4) x30, Celadon E (3,6) x24, Fuchsia F (3,7) x29 y23..25. Loss at any site: soldiers shoot her, a splatter object stays (hide flags 0x866..0x86B), F_MAXDEAD 0x86C.
- Sniper (tools/story_sniper.py, map (2,79) final camp): entering row y15 with MAX alive makes her wait, a sniper shoots her (splatter, F_MAXDEAD), box explains, LEAF walks to the sniper at (3,10), says "child murderer", fight vs trainer 751 SNIPER (JRA, Lv 45..48, Scizor/Aerodactyl/Sneasel/Tyranitar). Flags F_SNIPEDONE 0x86D, HIDE_SNIPER 0x86E, HIDE_SMAX 0x86F, HIDE_SSPL 0x870, VAR_SNIPE 0x409C.
- Emulator-only checks: shots/snipe2.png (scene to the insult), shots/pew.png and shots/maxdie.png (Pewter site and loss splatter), shots/mk_final.png (Mason KO home), newgame_test and battle_test run. The sniper fight itself was not played to the end.
- Combined release at repo root: PokemonWarAndMurder.ips (Outlaw base to final, 1953 records) and PokemonWarAndMurder.gba, CRC32 0x11c68318 = apply_all output. Existing roms/ files untouched.

## 2026-10-17 Remaining checks (emulator-only) and fixes
- Pass: Lavender, Celadon (reached from the road at x24, y16 going up; the east side of the gym yard is fenced), Fuchsia site triggers; Max-loss execution splatter at Fuchsia and Pewter; sniper fight won (test: 4 mons at Lv1 vs Machamp Lv80), then the sniper flees and is removed; PLAYABLE-mode loss to the sniper enters the death flow ("The world goes white."); NORMAL loss is the stock white-out; PLAYABLE-mode Mason knock-out lands LEAF in her house with no afterlife; battle_test frames as expected; newgame_test gives LEAF/MASON.
- Bug fixed: the sniper defeat line lacked its trailing space and showed a stray glyph.
- Test-only env added: SNIPER_SPECIES, SNIPER_LV (never set for release).
- Regenerated PokemonWarAndMurder.ips (1953 records) and PokemonWarAndMurder.gba from the single IPS on the Outlaw base: CRC32 0x9f877c68 = apply_all output. roms/ files untouched.

## 2026-10-17 Decal layering and collision audit (emulator-only)
- Bugs found and fixed (new final stage tools/decal_layer.py, last in apply_all.sh):
  1. The splat sort hook (tools/splat_order.py, subpriority 0xFF) only matched the splatter image table. The black feather (graphics 155, a 16x16 object) was not covered, so it sorted 8 pixels nearer than the 16x32 player and could be drawn over the head. The hook now forces 0xFF for the splatter table (0x98, 0x99, 0xA1 alias) and the feather table.
  2. The collision exemption stub (army.py, 0x3B2300) exempted only 0x98, 0x99 and the army splatter alias, so feathers blocked LEAF. Graphics 155 is exempt now.
- Verified by reading gSprites RAM (base 0x0202063C, tools/sprite_ram_report.py, harness VIRI_RAM) in 12 cases: every splatter/feather sprite has subpriority 0xFF and the same OAM priority as the player (2), the player/NPCs are 0x7A..0x92, so decals are under them; exit code 0 in all.
- Visual walk tests (tools/layer_test.py): LEAF walks over each decal from W, E, S and N: Pewter, Lavender, Celadon, Fuchsia, Cerulean A, Vermilion B Max splatters, Viridian arrest splatter, final camp sniper splatter, feathers in Pallet, Viridian, Pewter, Cerulean, Vermilion. Sheets: shots/layering_*.png, RAM report shots/layering_ram_report.txt.
- Collision: tools/decal_scan.py (all 79 decal objects on collision-0 tiles), tools/collision_diff.py (Outlaw base vs final), tools/collision_report.py (sheets shots/collision_*.png, outliers shots/collision_outliers.txt). Max site spots/triggers and the sniper walk path (row y15, x23 column, row y10) are all walkable. Outlier tiles are Viridian (9,4), Cerulean (42..43,11), Fuchsia (26,17..18, same as base): all trees/hedge/fence, blocked as intended (shots/collision_walk_into_trees_rocks.png). Observation only: a soldier object stands on a blocked house tile at Fuchsia (35,15), and Celadon has an object at (-7,21) off the map (both predate this work).
- Test-only: VIRI_RAM in viri_test.py. CRC32 of the combined IPS applied to the Outlaw base = apply_all output = 0x27808271.

## 2026-10-17 Splatter decal visual audit (emulator-only, no ROM change)
- tools/splatter_sheet.py walks LEAF to every decal in the final ROM (27 cases: 8 Max/story splatters, Viridian x2, 8 Lavender bodies, 5 other bodies, 6 feathers, plus the army alias 0xA1 test on the Pewter site) and saves native crops at 3x: shots/splatter_crops/*_{inplace,standing_on,walking_over}.png and shots/splatter_all_sheet.png (+ _splatters and _bodies_feathers).
- Result: all decals sit on the ground tile, correct crimson/black palettes, drawn over ground and plaza tiles and under LEAF and NPCs, no clipping, no float. No bug found, so ROM/IPS unchanged (CRC32 0x27808271).
- Lavender bodies are only visible after the plaza scene (VAR_SCENE 1, test poke 0x11E4=1). Heaven and Hell maps contain no decal objects. Runtime-spawned kill and army splatters (pool objects) share the same graphics tables and were checked via the 0xA1 alias; a real kill spawn was not triggered.

## 2026-10-17 Player showed Red (male avatar): fixed
- Cause (real bug, not only the harness): the hack skips the Oak speech, so playerGender (SaveBlock2 + 8) stayed 0 = male, and FireRed draws the male avatar (Red) in the overworld. newgame_test printed gender 0. The graphics tables for Red/Leaf are unchanged from the Outlaw base (checked ids 0..5), so no sprite was altered.
- Fix: the naming-skip stub in tools/cry_open.py now also writes playerGender = 1 (LEAF is female per docs/SPEC_ARREST_AND_PARTY.md). A cold new game now gives gender 1 and the vanilla Leaf overworld sprite; no sprite art was added or painted.
- Existing saves keep their stored gender. Harness: out/user_new.raw is an old state with gender 0, so viri_test.py now pokes gender 1 at frame 5 (VIRI_MALE=1 disables) and the map load refreshes the avatar to Leaf. battle_test.py and other tools that load that state without viri_test still show Red until the state is regenerated.
- shots: player_newgame_native.png (before, Red), player_newgame_native_fixed.png (after, Leaf), player_red_vs_leaf_side_by_side.png, leaf_test_warp.png; splatter_all_sheet*.png and splatter_crops redone with Leaf. Older layering_*/collision_* sheets from earlier today still show Red (layering behaviour unaffected).
- Rebuilt combined IPS applied to the Outlaw base = apply_all output.

## 2026-10-17 Release GBA now in the repo
- PokemonWarAndMurder.gba at the repo root was never pushed: the `*.gba` rule in .gitignore skipped it, so GitHub only had the IPS and the stale roms/Pokemon War and Murder.gba (CRC32 0x32dfc7de, four builds old). Added it with `git add -f`.
- Checked: PokemonWarAndMurder.ips applied to the Outlaw base gives a byte-identical file, 16,777,240 bytes, CRC32 0x873b6735 (includes the decal layering/collision fixes and the female LEAF avatar fix). roms/ files untouched.

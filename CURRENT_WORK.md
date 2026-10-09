# Current work (2026-10-09)

Branch: claude/lucid-edison-b1ri7h. Source of truth: tools/ and gun/. Full rebuild: tools/build_full.sh PREFIX.

## Not in the repo (and why)
- ROMs and states (*.gba, *.state): gitignored (copyrighted, large). The unpatched base ROM f4046af2-outlaw-2015-09-05.gba (16,777,240 bytes) is required; tools expect out/c3.gba (an intermediate build, not stored).
- All built outputs in out/ (533 ROM builds, 8.4 GB) and test screenshots in shots/.
- The user's uploaded saves and states (00b1f3bc .sav, 19c47a6d .sgm, 453db1b1 .sav, f676643d .srm, several .state): live only in the session upload folder. Needed for the pending VBA-to-mGBA port.
- Delivered artifacts (.ips etc. from earlier turns) that are not already in the repo root.

## State
Done but only partly tested: see HANDOFF_pokemon_outlaw.txt, section STATUS UPDATE 2026-10-09.
Open order of work:
1. Rebuild with the new tools/army_sites.py extend_right rule (flat run + edge block, rock face, period-2 trees). Render Celadon, Lavender, Vermilion, Cerulean east edges; check collision on rock; fall back to plain lawn if wrong.
2. Check the remaining tiling: paved slab paths must use middle blocks with the edge block only at the end; user reported seams in a paving screenshot.
3. In-game tests: church/base warps, custom interiors, story officer shooting, police Gen 1 teams, KARMA label, priest text, grey house tile glitch.
4. Port the user's VBA .sav and .sgm to R36S mGBA .srm and .state (not started; use an existing .state as template).

## Uploaded binaries (added 2026-10-09)
roms/: original hack ROM, c3_build_base.gba (input of tools/build_full.sh as out/c3.gba), m_final_latest_build.gba (latest build; still has the old extend_right comb/seam bug).
saves/user_uploads/: current user files only: 00b1f3bc .sav and 19c47a6d .sgm (VBA, to be ported), f676643d .srm and 56898276/3a41f949/319d9027 states (R36S mGBA templates).
saves/delivered/: last delivered sav, sgm8, ini, Spirits Splatter state.
shots/: screenshots from 2026-10-09 only. ref_uploads/: FireRed reference zip and earlier handoff bundle.
Left out as outdated: 530 older ROM builds, older states/saves (453db1b1 .sav, be23eecc .state), shots before 2026-10-09.

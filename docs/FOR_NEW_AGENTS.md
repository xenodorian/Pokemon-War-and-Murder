# For new agents

Read /CURRENT_WORK.md first. It has the one rule and the one workflow.

## Quick start
- Repos: xenodorian/Pokemon-War-and-Murder (this one, push straight to main, never create branches), xenodorian/CryMon, pret/pokefirered, pret/pokeemerald (reference only).
- The game is ONE file, PokemonWarAndMurder.gba at the repo root. Change it only with `tools/patch.sh tools/STAGE.py`. The older ROMs (c3_build_base.gba, m_final_latest_build.gba and all earlier builds) were deleted and purged from history. They must never come back.
- The archived chain scripts are in tools/archive/old_chain/. Do not run them. They rebuild an old lineage and would reintroduce the old bedroom.
- Never use an older save state or ROM to test. Tests run from saves/ported/new_game_empty_party.raw (made from the current ROM) or newer.

## Environment setup that worked
- pip: keystone-engine capstone Pillow numpy scipy scikit-image
- apt: clang lld llvm (llvm-objcopy), and libmgba0.10t64 so tools/harness_new runs.
- Scripts expect /home/claude/work: ln -s <repo path> /home/claude/work. Also mkdir /tmp/claude-0.

## Pitfalls
- Push with git to main. Fetch and rebase before any commit.
- Coord event trigger 0 runs immediately, so use a var as the trigger.
- Test-only switches live in tools/test_stage.py and only ever touch a scratch copy outside the repo.
- tools/inc.py Rom.alloc starts after the last non-0xFF byte plus 4. Data that ends in its own 0xFF terminator must not be followed by new data in the same spot.

## Owner rules and style
- Work only on main. No em dashes, no emoji. Concise plain answers for simple questions.
- Do not put model identifiers in commits or PRs.
- Verify before claiming done, and say when a check was emulator-only. A screenshot from a loaded save state shows that state's graphics, not the ROM's.
- GitROMs looks up one name: PokemonWarAndMurder.gba. Do not publish another name.
- Stay in scope. If a needed edit goes beyond the request, stop and confirm.

## Where to look
- CURRENT_WORK.md, ROM_LOG.txt
- docs/SPEC_ARREST_AND_PARTY.md, docs/handoff/grok_handoff.txt (old notes), docs/ANIMATION_NOTES.md, docs/STORY_PLAN.md
- docs/history/ (old notes, history only)

# For new agents

Read this first if you are a fresh Grok session starting from scratch on this project.

## Quick start
- Repos: xenodorian/Pokemon-War-and-Murder (this one, push straight to main), xenodorian/CryMon, pret/pokefirered, pret/pokeemerald (reference for partner battle logic, e.g. battle_controller_player_partner.c).
- The base ROM is the Pokemon Outlaw hack in roms/. It is itself a FireRed hack and has no decomp. All edits are Python binary patches built by tools/apply_all.sh. Do NOT use tools/build_full.sh, which is the old chain.
- Build ROMs roms/c3_build_base.gba and roms/m_final_latest_build.gba must stay.

## Environment setup that worked
- pip: keystone-engine capstone Pillow numpy scipy scikit-image
- apt: clang lld llvm (llvm-objcopy) gcc-arm-none-eabi, and libmgba0.10t64 so tools/harness_ls and tools/harness_new run.
- Scripts expect /home/claude/work: ln -s /workspace/Pokemon-War-and-Murder /home/claude/work. Also mkdir /tmp/claude-0.
- Use shallow clones (git clone --depth 1) for the pret repos.

## Pitfalls hit early
- The computer can take a long time to start. Shell may fail with "still starting up". Retry. Do not ask the user to touch the machine; they are in the cloud.
- The GitHub connector is text-only and truncates large files. Read big files from a clone.
- Push with git, not the connector: gh auth login --web, approve the code at github.com/login/device in the box browser (already signed in as xenodorian), then gh auth setup-git. After that git push works with binaries.
- The local checkout drifts behind origin when others push. Run git fetch and git pull --rebase before any commit.
- Coord event trigger 0 runs immediately, so use a var as the trigger.
- Test-only env switches (TEST_BATTLE, TEST_WARP, TEST_GIVE, TEST_FOE, VIRI_FORCE, VIRI_LEVEL and similar) never go in release builds.
- A rebuild differed from the repo ROM by 5 bytes of compiled code, likely a compiler version difference. Not a behaviour bug found so far.

## Owner rules and style
- Push straight to main. Never delete or overwrite uploaded ROMs, IPS patches, saves, states or art.
- No em dashes, no emoji. Be concise.
- Verify before claiming done, and say when a check was emulator-only.
- Do not ask questions the repos or ROM can answer. Decisions are delegated: use judgment and record the choice.
- After each large step, commit, push and add a dated note to CURRENT_WORK.md.
- Stay in this project's scope. If blocked, search online first.

## Where to look
- CURRENT_WORK.md (newest notes at the end)
- docs/SPEC_ARREST_AND_PARTY.md
- docs/handoff/grok_handoff.txt
- docs/ANIMATION_NOTES.md
- docs/STORY_PLAN.md

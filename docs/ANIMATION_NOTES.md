# Battle animation notes

- Symbol addresses: build pret/pokefirered as FireRed 1.0 (agbcc from /workspace/agbcc: `./install.sh /workspace/pokefirered`, then `make -j8 firered`). The resulting pokefirered.gba has sha1 41cb23d8dccc8ebd7c649cd8fbb58eeace6e2fdc and pokefirered.map lists every symbol. The Outlaw ROM keeps FireRed 1.0 code at the same addresses (checked: gBattleAnims_Moves is 0x081c68f4 in both).
- Battle animation sprite sheets and palettes are indexed by tag minus 10000. Both tables had 289 entries; tools/anim_throw.py moves them to free space with 291 entries (tag 10289 = Leaf throw frames, 10290 = Poke Ball). References: exact pointers, entry-offset pointers, and two literals at 0x728b8 / 0x728bc that hold table minus 0x13880.
- Animation scripts: opcode lengths are in tools/anim_throw.py (LEN). createvisualtask runs the task function once at once, so a task can set gBattleAnimArgs[7] and the script can branch with jumpargeq 7, 1, ptr.
- Leaf frames are only added to Swift, Barrage, Egg Bomb, Spike Cannon, Sludge Bomb and Shadow Ball when the attacker is species 107 (Hitmonchan) or 255 (LEAF); other users keep the original animation. Bitch Slap and Ball Throw always use Leaf.
- Position tuning env vars for builds: LEAF_X, LEAF_Y, BALL_X, BALL_Y. tools/anim_test.py takes dense screenshots of a move (needs out/user_new.raw).

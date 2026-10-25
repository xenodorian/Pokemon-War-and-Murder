"""Static check (run from the repo root): python3 tools/tests/police_vars.py [ROM.gba]
The three police store natives (pbit in police_apply, pset in pol_mark and npc_shoot) must load the byte offset of var 0x401E (0x103C), no longer 0x40E8 (0x11D0, which spans the
reputation var 0x40E9), and none of the trainer menu's bit store vars may be 0x401E or 0x401F."""
import os, struct, sys
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(R); sys.path.insert(0, 'tools')
d = open(sys.argv[1] if len(sys.argv) > 1 else 'PokemonWarAndMurder.gba', 'rb').read()
bad = []
def check(name, ok, info=''):
    print(('PASS ' if ok else 'FAIL ') + name + (' ' + str(info) if info else ''))
    if not ok: bad.append(name)
for a in (0xF227E0, 0xF22888, 0xF22C64): check('literal at %#x is the offset of var 0x401E' % a, struct.unpack('<I', d[a:a + 4])[0] == 0x103C)
import trainer_menu_fix as T
check('trainer menu store does not use 0x401E or 0x401F', 0x401E not in T.BIT_VARS and 0x401F not in T.BIT_VARS)
sys.exit(1 if bad else 0)

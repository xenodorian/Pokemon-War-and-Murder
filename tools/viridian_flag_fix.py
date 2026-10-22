"""Viridian base empty fix: on map load, clear flag 0x4C2 if the player does not have the Viridian medal (item 59).
The base objects are correctly keyed to 0x4C2. If that flag is set without the medal, the soldiers are hidden
even though the captain was never defeated. This script restores them on entry."""
import sys, struct
sys.path.insert(0, 'tools')
from inc import *
from shinigami import SB, put_script
from story_afterlife import add_mapscript
from leg1 import header, r32

FLAG_VIRIDIAN = 0x4C2
ITEM_PURPLE_HEART = 59   # Viridian's medal

def install(r):
    # Script: checkitem 59; if result == 1 (have it), skip; else clearflag 0x4C2
    S = SB()
    S.raw(0x47); S._add(struct.pack('<HH', ITEM_PURPLE_HEART, 1))  # checkitem
    S.compare(0x800D, 1)
    S.goto_if(1, 'have')
    S.clearflag(FLAG_VIRIDIAN)
    S.lab('have')
    S.end()
    sc = 0x08000000 + put_script(r, S)
    # Type 3 = on map transition / load
    add_mapscript(r, 2, 71, 3, sc)
    print('viridian flag fix: map script', hex(sc))

if __name__ == '__main__':
    r = Rom(sys.argv[1])
    install(r)
    r.save(sys.argv[2])
    print('end', hex(r.cur))

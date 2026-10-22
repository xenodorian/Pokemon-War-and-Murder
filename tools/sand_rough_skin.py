"""Owner request: the whole Sandshrew line has ROUGH SKIN instead of SAND VEIL (usage: sand_rough_skin.py IN.gba OUT.gba).
SANDSHREW (27), SANDSLASH (28), SANDGRAVE (251): ability slot 1 = 24 (ROUGH SKIN), slot 2 stays empty. The ability is read from the species data,
so Pokemon already in a save get it too. ROUGH SKIN exists in this ROM's ability table (id 24); INTIMIDATE (22) was the fallback."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from inc import Rom
from g3 import ENC
STATS = 0x254784; LINE = (27, 28, 251); ROUGH_SKIN = 24; SAND_VEIL = 8
def apply(r):
    name = bytes(ENC[c] for c in 'ROUGH SKIN'); i = bytes(r.b).find(bytes(ENC[c] for c in 'SAND VEIL')); base = i - 13 * SAND_VEIL
    assert bytes(r.b[base + 13 * ROUGH_SKIN:base + 13 * ROUGH_SKIN + len(name)]) == name, 'ability 24 is not ROUGH SKIN in this ROM'
    for s in LINE:
        o = STATS + 28 * s + 22
        assert r.b[o] == SAND_VEIL and r.b[o + 1] == 0, 'species %d abilities are not SAND VEIL / none' % s
        r.b[o] = ROUGH_SKIN
    print('sand_rough_skin: species %s now have ROUGH SKIN' % (LINE,))
if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')

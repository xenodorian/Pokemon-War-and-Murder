"""Church tower: the player can walk behind it (usage: church_walkbehind.py IN.gba OUT.gba). Owner request.
Pallet Town (group 3 map 0), tiles (7,9) (8,9) (7,10) (8,10) = metatiles 729 730 731 732 (the cross and the tower top):
 - (7,10) and (8,10) are unblocked (collision 0, elevation 3 like the open tiles beside them)
 - the four metatiles change layer type from COVERED (1, drawn under the player) to NORMAL (0): their church art is drawn over the player
The row below (6..9,11) stays blocked, so the player can stand behind the tower but not walk through the roof."""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from inc import Rom
CELLS = {(7, 9): 729, (8, 9): 730, (7, 10): 731, (8, 10): 732}
def apply(r):
    b = r.b
    G = 0x3526A8; gp = r.r32(G + 12) - 0x08000000; h = r.r32(gp) - 0x08000000; lay = r.r32(h) - 0x08000000
    W = r.r32(lay); mp = r.r32(lay + 12) - 0x08000000; ST = r.r32(lay + 20) - 0x08000000
    at = r.r32(ST + 20) - 0x08000000
    for (x, y), m in CELLS.items():
        o = mp + 2 * (y * W + x); v = struct.unpack_from('<H', b, o)[0]
        assert v & 0x3ff == m, 'tile %s is metatile %d, expected %d' % ((x, y), v & 0x3ff, m)
        if y == 10:
            assert (v >> 10) & 3 == 1, 'tile %s is not blocked' % ((x, y),)
            struct.pack_into('<H', b, o, m | (3 << 12))                      # collision 0, elevation 3
        a = at + 4 * (m - 640); old = struct.unpack_from('<I', b, a)[0]
        assert (old >> 29) & 3 == 1, 'metatile %d layer type is %d, expected 1' % (m, (old >> 29) & 3)
        struct.pack_into('<I', b, a, old & ~0x60000000)                       # layer type NORMAL
    print('church_walkbehind: unblocked (7,10) (8,10); metatiles 729-732 now drawn over the player')
if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')

"""Owner tasks 8, 9, 10: SAND GRAVE (move 358), Sandgrave learns it at 35 (usage: sand_grave.py IN.gba OUT.gba). Runs after fe8_allies.py.
 - move 358 SAND GRAVE: Body Slam's record with power 120, type GROUND (4), accuracy 100 and 10 PP (best judgement, not in the spec),
   and the secondary effect chance 100, so the paralysis always lands (Body Slam's effect is paralysis; its chance is 30).
 - description: "The target is buried up to\nthe neck in dirt." (task 9)
 - battle animation: a copy of ROCK TOMB's script (task 8 recolour and screen shake are NOT done yet)
 - the move tables are moved to free space with 359 entries (same method as moves_extend.py); the code sentinels (0x40238, 0x933e8)
   and the battle_message compares go from 358 to 359
 - Sandgrave (251) learns SAND GRAVE at level 35, when Sandslash evolves into her"""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(1, '/home/claude/work/tools')
from inc import Rom
import species_add as SA
import move_tables as MT
import moves_extend as ME

OLD_N = 358; NEW_N = 359; SAND_GRAVE = 358; BODY_SLAM = 34; ROCK_TOMB = 317; GROUND = 4; SANDGRAVE = 251
LEARN = 0x25d7b4; SENTINEL_SITES = (0x40238, 0x933e8)

def apply(r):
    b = r.b
    L = MT.live(b)
    assert L['n'] == OLD_N
    assert struct.unpack('<I', b[0x40238:0x4023c])[0] == OLD_N and struct.unpack('<I', b[0x933e8:0x933ec])[0] == OLD_N, 'sentinels'
    # 1. move data
    rec = bytearray(b[L['md'] + 12 * BODY_SLAM:L['md'] + 12 * BODY_SLAM + 12])
    assert rec[0] == 0x06 and rec[5] == 30, 'body slam paralysis record'
    rec[1] = 120; rec[2] = GROUND; rec[3] = 100; rec[4] = 10; rec[5] = 100
    newdata = bytes(b[L['md']:L['md'] + 12 * OLD_N]) + bytes(rec)
    md_new = r.alloc(newdata, 4)
    # 2. names
    names = bytes(b[L['mn']:L['mn'] + 13 * OLD_N])
    n = SA.text('SAND GRAVE'); assert len(n) <= 13
    names += n + b'\xff' * (13 - len(n))
    mn_new = r.alloc(names, 4)
    # 3. descriptions (entry move-1)
    descs = bytes(b[L['mdesc']:L['mdesc'] + 4 * (OLD_N - 1)])
    descs += struct.pack('<I', 0x08000000 + r.alloc(SA.text('The target is buried up to\nthe neck in dirt.'), 1))
    mdesc_new = r.alloc(descs, 4)
    # 4. battle animation: ROCK TOMB's script pointer
    anims = bytes(b[L['anim']:L['anim'] + 4 * OLD_N])
    anims += anims[4 * ROCK_TOMB:4 * ROCK_TOMB + 4]
    anim_new = r.alloc(anims, 4)
    # 5. repoint every reference to the old tables (the pp field pointer too, as in moves_extend)
    ME.repoint(b, L['md'] + 4, md_new + 4)
    counts = (ME.repoint(b, L['md'], md_new), ME.repoint(b, L['mn'], mn_new),
              ME.repoint(b, L['mdesc'], mdesc_new), ME.repoint(b, L['anim'], anim_new))
    assert all(c > 0 for c in counts), counts
    # 6. sentinels and the battle text limit (move ids up to 358 print their names)
    for o in SENTINEL_SITES: r.w32(o, NEW_N)
    for o, br in ((0xd75fc, 0xd3), (0xd7e96, 0xd2), (0xd7eae, 0xd3)):
        assert b[o] == 0xb3 and b[o + 1] == 0x20 and b[o + 2] == 0x40 and b[o + 3] == 0x00 and b[o + 4:o + 6] == b'\x81\x42', hex(o)
        assert b[o + 7] == br, hex(o)
        b[o] = 0xb4
    # 7. Sandgrave learns SAND GRAVE at 35
    p = struct.unpack_from('<I', b, LEARN + 4 * SANDGRAVE)[0] - 0x08000000
    moves = []
    while True:
        v = struct.unpack_from('<H', b, p)[0]; p += 2
        if v == 0xffff: break
        moves.append((v >> 9, v & 0x1ff))
    assert (35, SAND_GRAVE) not in moves
    moves.append((35, SAND_GRAVE)); moves.sort(key=lambda t: t[0])
    data = b''.join(struct.pack('<H', (l << 9) | m) for l, m in moves) + b'\xff\xff'
    r.w32(LEARN + 4 * SANDGRAVE, 0x08000000 + r.alloc(data, 2))
    print('sand_grave: move %d, tables %s, Sandgrave learns it at 35' % (SAND_GRAVE, [hex(x) for x in (md_new, mn_new, mdesc_new, anim_new)]))

if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')

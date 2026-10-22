"""Add Xatwo evolution line and learnsets.
Natu (177) evolves to Xatu (178) at level 20.
Xatu learns Fly/Future Sight/Wish at 21/24/27, evolves to Xatwo (430) at 30.
Xatwo: +30 HP/SpA/SpD from Xatu, red bandana sprite, specified learnset.
"""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from inc import Rom
import species_add as SA

NATU = 177
XATU = 178
XATWO = 430
STATS = 0x254784
LEARN = 0x25d7b4
EVO = 0x259754
FLY = 19
FUTURE_SIGHT = 248
WISH = 273
PSYCHIC = 94
DRILL_PECK = 65
SHADOW_BALL = 247
GIGA_DRAIN = 202
HYPER_BEAM = 63

def apply(r):
    b = r.b
    # 1. Natu -> Xatu at 20 (method 4 = EVO_LEVEL)
    evo_natu = bytearray(b[EVO+40*NATU:EVO+40*NATU+40])
    struct.pack_into('<HHH', evo_natu, 0, 4, 20, XATU)
    b[EVO+40*NATU:EVO+40*NATU+40] = evo_natu
    # 2. Xatu -> Xatwo at 30
    evo_xatu = bytearray(40)
    struct.pack_into('<HHH', evo_xatu, 0, 4, 30, XATWO)
    b[EVO+40*XATU:EVO+40*XATU+40] = evo_xatu
    # 3. Xatu learnset
    p = r.r32(LEARN + 4*XATU) - 0x08000000
    moves = []
    while True:
        v = struct.unpack_from('<H', b, p)[0]
        if v == 0xffff: break
        moves.append((v >> 9, v & 0x1ff))
        p += 2
    moves = [(lv, m) for lv, m in moves if m not in (FUTURE_SIGHT, WISH, FLY)]
    moves += [(21, FLY), (24, FUTURE_SIGHT), (27, WISH)]
    moves.sort(key=lambda t: t[0])
    data = b''.join(struct.pack('<H', (lv << 9) | m) for lv, m in moves) + b'\xff\xff'
    r.w32(LEARN + 4*XATU, 0x08000000 + r.alloc(data, 2))
    # 4. Add Xatwo
    stats = (95, 75, 70, 95, 125, 100)
    learnset = [
        (30, PSYCHIC),
        (35, DRILL_PECK),
        (40, SHADOW_BALL),
        (45, GIGA_DRAIN),
        (50, HYPER_BEAM),
    ]
    front_png = os.path.join(os.path.dirname(HERE), 'xatwo_front.png')
    back_png = os.path.join(os.path.dirname(HERE), 'xatwo_back.png')
    SA.add_species(
        r, XATWO, 'XATWO', front_png, back_png,
        donor=XATU,
        stats=stats,
        types=(14, 2),
        catch=45, exp_yield=165, ev_yield=0,
        gender=127, egg_groups=(4, 4), growth=0,
        abilities=(28, 48),
        learnset=learnset,
        dex_national=None,
    )
    print(f'xatwo_stage: Natu->Xatu@20, Xatu learnset {moves}, Xatu->Xatwo@30, Xatwo slot {XATWO}')

if __name__ == '__main__':
    r = Rom(sys.argv[1])
    apply(r)
    r.save(sys.argv[2])
    print('ok')

"""Owner task 14: EIRIKA replaces KESTREL, the Viridian captain (trainer 24).
Species EIRIKA is slot 256 (free in this ROM). Stats, types, abilities, yields and egg data are copied from donor SCIZOR (212),
as in PoekEmblem (Leg 1), and her learnset is PoekEmblem's sEirikaLevelUpLearnset (no TM/tutor changes).
Art: story_assets/eirika/eirika_front.png and eirika_back.png (PoekEmblem's Eirika portrait crop).
Icon, cry and footprint are copied from SCIZOR, not PoekEmblem (not transplanted yet).
Team: KESTREL's team without AIPOM and CORSOLA, plus EIRIKA Lv 15 last: ELEKID 11, CHINCHOU 12, CLEFFA 13, EIRIKA 15.
The trainer keeps KESTREL's class and picture; only the name and party change.
usage: eirika_kestrel.py IN.gba OUT.gba"""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(1, '/home/claude/work/tools')
from inc import Rom
import species_add as SA

A = os.path.join(HERE, '..', 'story_assets', 'eirika')
SLOT = 256; DONOR = 212; KESTREL = 24
TRAINERS = 0x08798790; BASE_STATS = 0x254784

# PoekEmblem sEirikaLevelUpLearnset as FireRed move ids
EIRIKA_LEARN = [(1, 98), (1, 43), (6, 14), (7, 10), (9, 210), (11, 228), (12, 31), (14, 15), (16, 185),
                (17, 232), (19, 75), (21, 97), (22, 11), (25, 163), (28, 211), (31, 13), (34, 238), (36, 334)]

def apply(r):
    b = r.b
    o = BASE_STATS + 28 * DONOR; row = bytes(b[o:o + 28])
    stats = list(row[0:6]); types = (row[6], row[7])
    SA.add_species(r, SLOT, 'EIRIKA', os.path.join(A, 'eirika_front.png'), os.path.join(A, 'eirika_back.png'), DONOR,
        stats, types, catch=row[8], exp_yield=row[9], ev_yield=struct.unpack_from('<H', row, 10)[0], gender=254,
        egg_groups=(row[20], row[21]), growth=row[19], abilities=(row[22], row[23]), learnset=EIRIKA_LEARN,
        dex_national=None, tm_donors=[DONOR], shiny_shift=0.35)
    # KESTREL: name, party of four
    t = TRAINERS - 0x08000000 + 40 * KESTREL
    nm = SA.text('EIRIKA'); assert len(nm) <= 12
    b[t + 4:t + 16] = nm + b'\xff' * (12 - len(nm))
    old = struct.unpack_from('<I', b, t + 36)[0] - 0x08000000
    assert b[t + 32] == 5
    mon = {}
    for k in range(5):
        e = bytes(b[old + 8 * k:old + 8 * k + 8]); mon[struct.unpack_from('<H', e, 4)[0]] = e
    elekid = mon[239]; chinchou = mon[170]; cleffa = mon[173]; aipom = mon[190]
    eirika = bytearray(aipom); struct.pack_into('<H', eirika, 2, 15); struct.pack_into('<H', eirika, 4, SLOT)
    party = elekid + chinchou + cleffa + bytes(eirika)
    b[t + 32] = 4
    r.w32(t + 36, 0x08000000 + r.alloc(party, 4))
    print('task 14: KESTREL -> EIRIKA (species %d, Scizor donor), party ELEKID 11, CHINCHOU 12, CLEFFA 13, EIRIKA 15' % SLOT)

if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')

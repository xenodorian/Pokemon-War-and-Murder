"""Owner task 12 (part): the SHACKLE BALL item (usage: shackle_item.py IN.gba OUT.gba).
A copy of NET BALL (item 6) in the unused item slot 89: same name length, same icon and pocket, new name, price 1000
(best judgement, not given by the owner) and a description. It is not a Poke Ball for normal Pokemon; its use on a
defeated captain is the SHACKLE option (task 13), not built here. Selling it in the shops (task 12) is not built here."""
import sys, os, struct
sys.path.insert(0, '/home/claude/work/tools')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from inc import Rom
import species_add as SA

ITEM = 0x3db028
NET, SLOT = 6, 89

def apply(r):
    b = r.b
    src = ITEM + 44 * NET
    dst = ITEM + 44 * SLOT
    assert b[dst:dst + 9] == b'\xac' * 8 + b'\xff', 'slot 89 is not free'
    rec = bytearray(b[src:src + 44])
    name = SA.text('SHACKLE BALL')
    assert len(name) <= 14
    rec[0:14] = name + b'\xff' * (14 - len(name))
    rec[14:16] = struct.pack('<H', SLOT)
    rec[16:18] = struct.pack('<H', 1000)
    desc = SA.text('A ball that holds a defeated\nCAPTAIN. Use it after a fight.')
    rec[20:24] = struct.pack('<I', 0x08000000 + r.alloc(desc, 1))
    b[dst:dst + 44] = bytes(rec)
    print('shackle_item: SHACKLE BALL in item slot 89 (Net Ball graphics, price 1000)')
    marts(r)

def marts(r):
    """Sell SHACKLE BALL in every PokeMart list that sells the BLESS TAG (item 56): every shop in the game, which means every
    city's shop (Pallet Town has none). Each list is copied with 89 added before its end; every command that points at it is repointed."""
    b = r.b
    lists = {}
    for q in range(0, len(b) - 8):
        if b[q] == 0x86 and b[q + 4] == 0x08:
            p = struct.unpack_from('<I', b, q + 1)[0]
            if not (0x08000000 <= p < 0x08000000 + len(b) - 100):
                continue
            a = p - 0x08000000; ids = []; k = a
            while len(ids) < 40:
                v = struct.unpack_from('<H', b, k)[0]
                if v == 0: break
                ids.append(v); k += 2
            if len(ids) >= 2 and ids[-1] == 56 and SLOT not in ids:
                lists.setdefault(p, (ids, []))[1].append(q)
    for p, (ids, sites) in lists.items():
        new = r.alloc(struct.pack('<%dH' % (len(ids) + 2), *(ids + [SLOT, 0])), 4)
        for q in sites:
            r.w32(q + 1, 0x08000000 + new)
    print('shackle_item: SHACKLE BALL added to', len(lists), 'PokeMart lists,', sum(len(v[1]) for v in lists.values()), 'shop commands')

if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')

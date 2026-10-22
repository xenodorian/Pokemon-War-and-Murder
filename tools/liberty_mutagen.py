"""Move PHYS MUTAGEN and SPEC MUTAGEN (items 54 and 55) onto the Liberty buy list.
usage: liberty_mutagen.py IN.gba OUT.gba

liberty.py left them on the town marts. They now sit with the other Liberty goods
(after SHACKLE BALL, before the vitamins) and no pokemart list but that one sells them.
"""
import sys, struct
sys.path.insert(0, 'tools')
from inc import Rom

MUT = (54, 55)
OLD = [56, 52, 53, 89, 63, 64, 65, 67, 70, 66, 68]
NEW = [56, 52, 53, 89, 54, 55, 63, 64, 65, 67, 70, 66, 68]

def read_list(b, off):
    out = []
    while len(out) <= 40:
        v = struct.unpack_from('<H', b, off)[0]
        if v == 0:
            return out
        out.append(v)
        off += 2
    return None

def find_list(b, items):
    pat = struct.pack('<%dH' % (len(items) + 1), *(items + [0]))
    hits = []
    p = 0
    while True:
        i = b.find(pat, p)
        if i < 0:
            break
        hits.append(i)
        p = i + 2
    assert len(hits) == 1, hits
    return hits[0]

def pokemarts(b):
    """opcode 0x86 whose pointer is a short item list"""
    out = []
    for o in range(len(b) - 5):
        if b[o] != 0x86:
            continue
        p = struct.unpack_from('<I', b, o + 1)[0]
        if not 0x08000000 <= p < 0x08000000 + len(b) - 2:
            continue
        lst = read_list(b, p - 0x08000000)
        if lst:
            out.append((o, p, lst))
    return out

def apply(r):
    b = r.b
    old_off = find_list(b, OLD)
    old_ptr = 0x08000000 + old_off
    new_off = r.alloc(struct.pack('<%dH' % (len(NEW) + 1), *(NEW + [0])), 2)
    new_ptr = 0x08000000 + new_off
    nref = 0
    pat = struct.pack('<I', old_ptr)
    q = 0
    while True:
        j = b.find(pat, q)
        if j < 0:
            break
        if j > 0 and b[j - 1] == 0x86:
            r.w32(j, new_ptr)
            nref += 1
        q = j + 4
    assert nref == 2, nref

    stripped = 0
    for o, p, lst in pokemarts(bytes(r.b)):
        if p == new_ptr or not any(v in MUT for v in lst):
            continue
        kept = [v for v in lst if v not in MUT]
        assert len(kept) == len(lst) - sum(v in MUT for v in lst)
        raw = struct.pack('<%dH' % (len(kept) + 1), *(kept + [0]))
        assert len(raw) <= (len(lst) + 1) * 2
        off = p - 0x08000000
        r.b[off:off + len(raw)] = raw
        stripped += 1
    assert stripped == 30, stripped  # 15 live town lists and the 15 dead pre-liberty lists

    live = []
    seen = set()
    for _, p, lst in pokemarts(bytes(r.b)):
        if p in seen or not any(v in MUT for v in lst):
            continue
        seen.add(p)
        live.append(lst)
    assert live == [NEW], live
    print('liberty mutagens: list', hex(new_ptr), 'stripped', stripped)

if __name__ == '__main__':
    r = Rom(sys.argv[1])
    apply(r)
    r.save(sys.argv[2])
    print('ok', hex(r.cur))

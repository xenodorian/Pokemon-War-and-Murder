"""Shackling a captain removes them. Their hide flag was 0, so they stayed.
Each captain's flag is the shackle flag shackle_do2 already sets, and both
callers of that function also remove the sprite.
"""
import sys, struct, json
sys.path.insert(0, 'tools')
from inc import Rom

GROUPS = 0x3526A8
CAPS = [15, 6, 442, 86, 460, 176, 284, 399, 24, 433, 530]
SH = 0x871
DO2 = 0x08F8C7FD


def r32(b, o):
    return struct.unpack_from('<I', b, o)[0]


def apply(r):
    b = r.b
    mg = json.load(open('/tmp/map_groups.json'))
    sizes = [len(mg[g]) for g in mg['group_order']]
    sizes[2] = 82
    n = 0
    for g, nmaps in enumerate(sizes):
        gp = r32(b, GROUPS + 4 * g) - 0x08000000
        for m in range(nmaps):
            hp = r32(b, gp + 4 * m)
            if not (0x08000000 <= hp < 0x0A000000):
                continue
            h = hp - 0x08000000
            evp = r32(b, h + 4)
            if not (0x08000000 <= evp < 0x0A000000):
                continue
            ev = evp - 0x08000000
            no = b[ev]
            if no > 64:
                continue
            po = r32(b, ev + 4) - 0x08000000
            if po < 0 or po + 24 * no > len(b):
                continue
            for i in range(no):
                o = po + 24 * i
                sp = r32(b, o + 0x10)
                if not (0x08000000 <= sp < 0x0A000000):
                    continue
                a = sp - 0x08000000
                if b[a] != 0x5C:
                    continue
                tid = struct.unpack_from('<H', b, a + 2)[0]
                if tid not in CAPS:
                    continue
                flag = SH + CAPS.index(tid)
                struct.pack_into('<H', b, o + 0x14, flag)
                n += 1
    assert n == 11, n
    print('captain hide flags', n)

    sites = []
    pat = b'\x23' + struct.pack('<I', DO2)
    pos = 0
    while True:
        i = b.find(pat, pos)
        if i < 0:
            break
        sites.append(i)
        pos = i + 1
    if len(sites) == 1:
        print('despawn already wired')
        return
    assert len(sites) == 2, sites
    scr = pat + bytes([0x53, 0x0F, 0x80, 0x03])
    at = r.alloc(scr, 4)
    call = bytes([0x04]) + struct.pack('<I', 0x08000000 + at)
    for i in sites:
        b[i:i + 5] = call
    print('despawn', hex(0x08000000 + at), [hex(s) for s in sites])


if __name__ == '__main__':
    r = Rom(sys.argv[1])
    apply(r)
    r.save(sys.argv[2])
    print('ok', hex(r.cur))

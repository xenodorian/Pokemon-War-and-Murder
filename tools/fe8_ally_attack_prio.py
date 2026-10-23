"""Ally attack parts are drawn over the health boxes (usage: fe8_ally_attack_prio.py IN.gba OUT.gba).
The parts had OAM priority 1, the same as the health boxes, so the boxes could cover them. Priority 0 beats every priority 1 object.
Walks the species table made by fe8_ally_attack.py (found through the first template's OamData) and sets attr2 priority bits to 0. Safe to run twice."""
import sys, struct
sys.path.insert(0, 'tools')
from inc import Rom

def apply(r):
    b = r.b
    # the species table: entries of 16 bytes, first species 256, found by its byte pattern after the packer's data
    pat = struct.pack('<H', 256)
    i = 0x1000000
    tab = None
    while True:
        i = b.find(pat, i)
        if i < 0: break
        if i % 4 == 0 and b[i + 3] > 0 and 0 < b[i + 2] <= 8:
            # candidate: palPtr and partsPtr inside the new area
            pp, ap = struct.unpack_from('<II', b, i + 4)
            if 0x08000000 <= pp < 0x0A000000 and 0x08000000 <= ap < 0x0A000000 and struct.unpack_from("<H", b, i + 16)[0] in range(256, 265):
                tab = i; break
        i += 1
    assert tab is not None, 'species table not found'
    seen = set(); n = 0
    e = tab
    while struct.unpack_from('<H', b, e)[0] != 0xFFFF:
        parts = struct.unpack_from('<I', b, e + 8)[0] - 0x08000000
        for k in range(b[e + 2]):
            t = struct.unpack_from('<I', b, parts + 8 * k)[0] - 0x08000000
            oam = struct.unpack_from("<I", b, t + 4)[0] - 0x08000000
            if oam not in seen:
                seen.add(oam)
                a2 = struct.unpack_from('<H', b, oam + 4)[0]
                struct.pack_into('<H', b, oam + 4, a2 & ~0x0C00)
                n += 1
        e += 16
    print('table %#x, %d shared OamData set to priority 0' % (0x08000000 + tab, n))

if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')

"""Finds the live move tables in a built ROM (after moves_extend, anim_throw and later stages moved them).
live(b) -> dict(md=, mn=, mdesc=, anim=, n=) with ROM file offsets. The name table comes from the pointer at ROM 0x148.
The move data table is found by the record of BITCH SLAP (move 355, copied from TACKLE with power 30, type 1, accuracy 100, pp 20)."""
import sys, struct
sys.path.insert(0, '/home/user/Pokemon-War-and-Murder/tools')
from g3 import ENC

def _enc(s): return bytes(ENC[c] for c in s)

def referenced(b, addr):
    pat = struct.pack('<I', 0x08000000 + addr)
    return b.find(pat) >= 0

def live(b):
    mn = struct.unpack_from('<I', b, 0x148)[0] - 0x08000000
    assert b[mn + 13 * 355:mn + 13 * 355 + 10] == _enc('BITCH SLAP'), 'name table'
    md = None
    cands = [o for o in range(0x100000, len(b) - 12 * 359, 4)
             if b[o + 12 * 355 + 1] == 30 and b[o + 12 * 355 + 2] == 1 and b[o + 12 * 355 + 3] == 100 and b[o + 12 * 355 + 4] == 20
             and b[o + 12 * 33 + 1] == 35]
    # old copies of the table stay in the ROM; the live one is the one code points to
    for o in cands:
        if referenced(b, o): md = o; break
    assert md is not None, 'move data'
    # description pointers: entry move-1; the BITCH SLAP text is 'A hard slap that'
    txt = struct.unpack_from('<I', b, 0)  # placeholder, replaced below
    tp = bytes(_enc('A hard slap that'))
    tpos = b.find(tp); assert tpos > 0, 'desc text'
    desc_ptr = 0x08000000 + tpos
    mdesc = None
    for o in range(0, len(b) - 4, 4):
        if struct.unpack_from('<I', b, o)[0] == desc_ptr:
            c = o - 4 * (355 - 1)
            if referenced(b, c): mdesc = c; break
    assert mdesc is not None, 'desc table'
    # battle animation table: entry 33 (TACKLE) equals entry 355 and 356 is different from TACKLE for the Leaf throw
    anim = None
    TACKLE_ANIM = 0x081c7492      # TACKLE's battle animation script (entry 33 of the original table at 0x1c68f4)
    for o in range(0, 0x400000, 4):
        v = struct.unpack_from('<I', b, o)[0] - 0x08000000
        if 0xA00000 <= v < len(b) - 4 * 358 and struct.unpack_from('<I', b, v + 4 * 33)[0] == TACKLE_ANIM:
            anim = v; break
    assert anim is not None, 'anim table'
    return dict(md=md, mn=mn, mdesc=mdesc, anim=anim, n=358)

if __name__ == '__main__':
    b = open(sys.argv[1], 'rb').read()
    print({k: hex(v) if isinstance(v, int) else v for k, v in live(b).items()})

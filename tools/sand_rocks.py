"""Owner task 8 (recolour): SAND GRAVE's rocks are sandy light brown (usage: sand_rocks.py IN.gba OUT.gba). Runs after sand_grave.py.
Rock Tomb's script is copied for SAND GRAVE (move 358). Its rocks use the ROCKS tag (10058) and gRockTombRockSpriteTemplate.
 - new battle sprite tag 10291: the same rock tiles as ROCKS, and a palette that is ROCKS' palette recoloured to sandy light brown
   (each colour keeps its brightness, the hue becomes sand). Both tables (picture and palette) grow from 291 to 292 entries and every
   reference is repointed, as anim_throw.py does.
 - a copy of the rock sprite template with tile and palette tag 10291 (the rock sprites are otherwise unchanged)
 - the copied script loads tag 10291 in place of ROCKS. Its screen shake after each rock is Rock Tomb's own (createvisualtask
   AnimTask_ShakeBattleTerrain), so it is kept. The rocks' sound and timing are unchanged."""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(1, '/home/claude/work/tools')
from inc import Rom
import gfx
import move_tables as MT
import anim_throw as AT

ROCK_TAG = 10058; NEW_TAG = 10291; N_OLD = 291
ROCK_TOMB = 317; SAND_GRAVE = 358
LIT_PIC = 0x728b8; LIT_PAL = 0x728bc; TABLE_LIT_OFF = 0x13880
ROCK_TEMPLATE = 0x083e7508

def sand(cols):
    out = []
    for i, c in enumerate(cols):
        if i == 0: out.append(c); continue      # index 0 is the transparent colour
        L = (0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]) / 255
        k = 0.45 + 0.55 * L
        out.append((min(255, int(232 * k)), min(255, int(190 * k)), min(255, int(128 * k))))
    return out

def cmd_len(b, o):
    op = b[o]
    if op in (2, 3): return 7 + 2 * b[o + 6]
    if op == 0x1f: return 6 + 2 * b[o + 5]
    return AT.LEN[op]

def apply(r):
    b = r.b
    pic = (r.r32(LIT_PIC) + TABLE_LIT_OFF) - 0x08000000
    pal = (r.r32(LIT_PAL) + TABLE_LIT_OFF) - 0x08000000
    rock_pic = struct.unpack_from('<IHH', b, pic + 8 * (ROCK_TAG - 10000))
    assert rock_pic[2] == ROCK_TAG
    rock_pal_ptr = struct.unpack_from('<IHH', b, pal + 8 * (ROCK_TAG - 10000))[0]
    assert struct.unpack_from('<IHH', b, pic + 8 * (ROCK_TAG - 10000))[2] == ROCK_TAG
    cols = gfx.pal_to_rgb(gfx.lz_decomp(b, rock_pal_ptr - 0x08000000))
    new_pal = r.alloc(gfx.lz_comp(gfx.rgb_to_pal(sand(cols))), 4)
    # 1. the two tables with 292 entries
    pic_tab = bytes(b[pic:pic + 8 * N_OLD]) + struct.pack('<IHH', rock_pic[0], rock_pic[1], NEW_TAG)
    pal_tab = bytes(b[pal:pal + 8 * N_OLD]) + struct.pack('<IHH', 0x08000000 + new_pal, NEW_TAG, 0)
    pic_new = r.alloc(pic_tab, 4); pal_new = r.alloc(pal_tab, 4)
    r.w32(LIT_PIC, 0x08000000 + pic_new - 0x13880); r.w32(LIT_PAL, 0x08000000 + pal_new - 0x13880)
    n = 0
    for o in range(0, 0x400000, 4):
        if o in (LIT_PIC, LIT_PAL): continue
        v = struct.unpack_from('<I', b, o)[0]
        for old, new_ in ((pic, pic_new), (pal, pal_new)):
            base = 0x08000000 + old
            if base <= v < base + 8 * N_OLD and (v - base) % 8 == 0:
                r.w32(o, v - old + new_); n += 1
    assert n >= 4, n
    # 2. the rock template with the new tag
    t = bytearray(b[ROCK_TEMPLATE - 0x08000000:ROCK_TEMPLATE - 0x08000000 + 28])
    assert struct.unpack_from('<HH', t, 0) == (ROCK_TAG, ROCK_TAG)
    struct.pack_into('<HH', t, 0, NEW_TAG, NEW_TAG)
    tmpl = r.alloc(bytes(t), 4)
    # 3. Rock Tomb's script with the new tag and template
    anim = MT.live(b)['anim']
    o = struct.unpack_from('<I', b, anim + 4 * ROCK_TOMB)[0] - 0x08000000
    s = bytearray(); swapped = 0
    while True:
        op = b[o]; n_ = cmd_len(b, o); cmd = bytearray(b[o:o + n_])
        if op == 0x00 and struct.unpack_from('<H', cmd, 1)[0] == ROCK_TAG:
            struct.pack_into('<H', cmd, 1, NEW_TAG); swapped += 1
        if op == 0x02 and struct.unpack_from('<I', cmd, 1)[0] == ROCK_TEMPLATE:
            struct.pack_into('<I', cmd, 1, 0x08000000 + tmpl); swapped += 1
        s += cmd; o += n_
        if op == 0x08: break
    assert swapped == 5, swapped   # four rock sprites (createsprite) and the ROCKS load
    script = r.alloc(bytes(s), 1)
    r.w32(anim + 4 * SAND_GRAVE, 0x08000000 + script)
    print('sand_rocks: palette', hex(new_pal), 'tables', hex(pic_new), hex(pal_new), 'template', hex(tmpl), 'script', hex(script), 'swaps', swapped)

if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')

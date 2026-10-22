"""FE8 portrait transparency fix and ally attack import.
Encodes indexed PNGs directly so palette index 0 stays transparent.
Imports battle animation frames from PoekEmblem.
Does not re-run eirika_kestrel.py or fe8_allies.py."""
import sys, os, struct
sys.path.insert(0, 'tools')
from inc import *
from PIL import Image
import gfx

POEK = '/tmp/poek/decomp_overlay'
# species, key, trainer pic
ALLIES = [
    (256, 'eirika', 30),
    (257, 'larachel', 22),
    (258, 'cormag', 23),
    (259, 'innes', 24),
    (260, 'duessel', 25),
    (261, 'dozla', 26),
    (262, 'tana', 27),
    (263, 'joshua', 28),
    (264, 'myrrh', 29),
]
# PoekEmblem folder names differ for some
POEK_KEY = {'larachel': 'l_arachel', 'eirika': 'eirika'}

# Sprite table bases
FRONT_TBL = 0x2350ac
BACK_TBL = 0x23654c
PAL_TBL = 0x23730c
SHINY_TBL = 0x2380cc
PIC_FRONT = 0x23957c
PIC_PAL = 0x239a1c

def png_to_4bpp(path):
    """Indexed PNG -> (tiles_4bpp, palette_rgb). Index 0 stays 0."""
    im = Image.open(path)
    assert im.mode == 'P', path
    w, h = im.size
    pal = im.getpalette()
    # First 16 colors
    cols = [tuple(pal[i*3:i*3+3]) for i in range(16)]
    px = list(im.getdata())
    # Build 4bpp tiles (8x8, 32 bytes each)
    tiles = bytearray()
    for ty in range(h // 8):
        for tx in range(w // 8):
            for row in range(8):
                for col in range(0, 8, 2):
                    x = tx * 8 + col
                    y = ty * 8 + row
                    lo = px[y * w + x] & 0xF
                    hi = px[y * w + x + 1] & 0xF
                    tiles.append(lo | (hi << 4))
    return bytes(tiles), cols

def rgb_to_gba(cols):
    """16 RGB tuples -> 32 bytes GBA palette. Index 0 = transparent (0)."""
    out = bytearray(32)
    for i, (r, g, b) in enumerate(cols[:16]):
        if i == 0:
            continue  # leave as 0
        c = ((r >> 3) & 31) | (((g >> 3) & 31) << 5) | (((b >> 3) & 31) << 10)
        struct.pack_into('<H', out, i * 2, c)
    return bytes(out)

def install(r):
    b = r.b
    for slot, key, pic in ALLIES:
        poek_key = POEK_KEY.get(key, key)
        # Species sprites
        front_path = os.path.join(POEK, 'graphics/pokemon', poek_key, 'front.png')
        back_path = os.path.join(POEK, 'graphics/pokemon', poek_key, 'back.png')
        if not os.path.exists(front_path):
            # Fall back to story_assets
            front_path = f'story_assets/allies/{key}/front.png'
            back_path = f'story_assets/allies/{key}/back.png'
            if key == 'eirika':
                front_path = 'story_assets/eirika/eirika_front.png'
                back_path = 'story_assets/eirika/eirika_back.png'
        ft, fcols = png_to_4bpp(front_path)
        bt, bcols = png_to_4bpp(back_path)
        # Use front palette for both (they share)
        pal = rgb_to_gba(fcols)
        # Alloc and repoint
        fp = r.alloc(gfx.lz_comp(ft), 4)
        bp = r.alloc(gfx.lz_comp(bt), 4)
        pp = r.alloc(gfx.lz_comp(pal), 4)
        # Species tables: 8 bytes each (ptr, size/tag)
        r.w32(FRONT_TBL + 8 * slot, 0x08000000 + fp)
        r.w32(BACK_TBL + 8 * slot, 0x08000000 + bp)
        r.w32(PAL_TBL + 8 * slot, 0x08000000 + pp)
        r.w32(SHINY_TBL + 8 * slot, 0x08000000 + pp)  # same for now
        # Trainer picture
        r.w32(PIC_FRONT + 8 * pic, 0x08000000 + fp)
        r.w32(PIC_PAL + 8 * pic, 0x08000000 + pp)
        print(f'{key}: front {len(ft)} back {len(bt)} pal ok')

    # Battle animations: import frame sheets from PoekEmblem
    for slot, key, pic in ALLIES:
        poek_key = POEK_KEY.get(key, key)
        anim_dir = os.path.join(POEK, 'graphics/battle_anims/ally_attack', key.capitalize())
        if key == 'larachel':
            anim_dir = os.path.join(POEK, 'graphics/battle_anims/ally_attack/Larachel')
        p0 = os.path.join(anim_dir, 'p0.png')
        if not os.path.exists(p0):
            print(f'{key}: no anim frames')
            continue
        # p0 is a filmstrip; convert and store
        tiles, cols = png_to_4bpp(p0)
        ap = r.alloc(tiles, 4)
        print(f'{key}: anim p0 {len(tiles)} bytes at {hex(ap)}')

if __name__ == '__main__':
    r = Rom(sys.argv[1])
    install(r)
    r.save(sys.argv[2])
    print('end', hex(r.cur))

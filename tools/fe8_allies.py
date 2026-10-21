"""Owner task 15: the eight FE8 allies become captains (one per city except Viridian and Cinnabar).
Each captain keeps the team and class; his name, picture, and last Pokemon change, so the ally's Pokemon is the one captured.
  PALLET HAWTHORN -> LARACHEL   PEWTER MARLOW -> CORMAG     CERULEAN VANCE -> INNES      VERMILION DRAYTON -> DUESSEL
  LAVENDER CORVIN -> DOZLA      CELADON ASHFORD -> TANA      SAFFRON THORNE -> JOSHUA      FUCHSIA BRANDT -> MYRRH
Names are kept to the length of the captain's name so the in-place text pass fits (the ROM has no room to grow texts).
Species 257 to 264 (free in this ROM) take the PoekEmblem slots 252 to 259 in the same order; each copies stats, types and
yields from a donor (the base species PoekEmblem uses) and takes PoekEmblem's ally learnset (story_assets/allies/learnsets.json).
Profile art and front/back sprites: story_assets/allies/<name>/front.png and back.png (PoekEmblem's FE8 portrait crops).
Trainer pictures use the unused picture slots 22 to 30 (not referenced by any trainer record).
Also KESTREL -> EIRIKA in the text (the trainer record itself is changed by eirika_kestrel.py).
Not transplanted: ally icons, cries and footprints (copied from the donor), Pokedex entries, and FE8 dialogue.
usage: fe8_allies.py IN.gba OUT.gba"""
import sys, os, re, json, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(1, '/home/claude/work/tools')
from inc import Rom
import species_add as SA
import gfx
from PIL import Image

A = os.path.join(HERE, '..', 'story_assets', 'allies')
TRAINERS = 0x08798790 - 0x08000000
BASE_STATS = 0x254784; MOVE_NAMES = 0x247094; FRONT = 0x23957c; PAL = 0x239a1c
# key, species name, species slot, donor (base species slot), gender byte, trainer picture, captain trainer id, old captain name
ALLIES = [
    ('larachel', 'LARACHEL', 257, 36, 254, 22, 15, 'HAWTHORN'),
    ('cormag',   'CORMAG',   258, 149, 0, 23, 6, 'MARLOW'),
    ('innes',    'INNES',    259, 22, 0, 24, 442, 'VANCE'),
    ('duessel',  'DUESSEL',  260, 76, 0, 25, 86, 'DRAYTON'),
    ('dozla',    'DOZLA',    261, 68, 0, 26, 460, 'CORVIN'),
    ('tana',     'TANA',     262, 18, 254, 27, 176, 'ASHFORD'),
    ('joshua',   'JOSHUA',   263, 123, 0, 28, 284, 'THORNE'),
    ('myrrh',    'MYRRH',    264, 148, 254, 29, 399, 'BRANDT'),
]
# PoekEmblem move names that have no gen 3 name here
MOVE_OVERRIDE = {'ROCK_BLAST': 'ROCK_SLIDE'}
LETTER = range(0xBB, 0xEF)
PIC_TRANSPARENT = (115, 197, 164)

def move_map(r):
    from g3 import ENC
    dec = {v: k for k, v in ENC.items()}
    ids = {}
    for i in range(1, 358):
        raw = bytes(r.b[MOVE_NAMES + 13 * i:MOVE_NAMES + 13 * i + 13]).split(b'\xff')[0]
        name = ''.join(dec.get(c, '') for c in raw)
        ids.setdefault(re.sub(r'[^A-Z]', '', name.upper()), i)
    return ids

def pic_from_png(r, pic, path):
    im = Image.open(path).convert('RGBA'); assert im.size == (64, 64)
    px = [im.getpixel((x, y)) for y in range(64) for x in range(64)]
    cols = []
    for c in px:
        if c[3] >= 128 and c[:3] not in cols: cols.append(c[:3])
    if len(cols) > 15:   # reduce to 15 colours (median cut), as species_add does for species art
        sheet = Image.new('RGB', (sum(c[3] >= 128 for c in px), 1)); sheet.putdata([c[:3] for c in px if c[3] >= 128])
        q = sheet.quantize(colors=15, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE); pp = q.getpalette()
        cols = [tuple(pp[i * 3:i * 3 + 3]) for i in range(15)]
        near = lambda c: min(range(15), key=lambda i: sum((a - b) ** 2 for a, b in zip(c, cols[i])))
    else:
        near = lambda c: cols.index(c)
    idx = [[(near(im.getpixel((x, y))[:3]) + 1) if im.getpixel((x, y))[3] >= 128 else 0 for x in range(64)] for y in range(64)]
    fa = FRONT + 8 * pic; pa = PAL + 8 * pic
    assert struct.unpack('<HH', r.b[fa + 4:fa + 8]) == (0x800, pic), pic
    r.w32(fa, 0x08000000 + r.alloc(gfx.lz_comp(gfx.pixels_to_tiles(idx)), 4))
    r.w32(pa, 0x08000000 + r.alloc(gfx.lz_comp(gfx.rgb_to_pal([PIC_TRANSPARENT] + cols + [(0, 0, 0)] * (15 - len(cols)))), 4))

def text_rename(b, old, new):
    """replace the name in every text outside the trainer table; new is padded with spaces to the old length"""
    from g3 import ENC
    po = bytes(ENC[c] for c in old); pn = bytes(ENC[c] for c in new)
    assert len(pn) <= len(po)
    pn = pn + bytes([0x00]) * (len(po) - len(pn))
    n = 0; i = 0
    while True:
        i = bytes(b).find(po, i + 1)
        if i < 0: break
        if TRAINERS <= i < TRAINERS + 40 * 1000: continue
        if i > 0 and b[i - 1] in LETTER: continue
        if i + len(po) < len(b) and b[i + len(po)] in LETTER: continue
        b[i:i + len(po)] = pn; n += 1
    return n

def apply(r):
    b = r.b
    learn = json.load(open(os.path.join(A, 'learnsets.json')))
    mids = move_map(r)
    for old, new in [(c[7], c[1]) for c in ALLIES] + [('KESTREL', 'EIRIKA')]:
        print('text %s -> %s in %d texts' % (old, new, text_rename(b, old, new)))
    for key, name, slot, donor, gender, pic, tid, old in ALLIES:
        o = BASE_STATS + 28 * donor; row = bytes(b[o:o + 28])
        moves = []
        for lvl, mv in learn[key]:
            mv = MOVE_OVERRIDE.get(mv, mv)
            key_m = mv.replace('_', '')
            assert key_m in mids, (key, mv)
            moves.append((lvl, mids[key_m]))
        SA.add_species(r, slot, name, os.path.join(A, key, 'front.png'), os.path.join(A, key, 'back.png'), donor,
            list(row[0:6]), (row[6], row[7]), catch=row[8], exp_yield=row[9], ev_yield=struct.unpack_from('<H', row, 10)[0],
            gender=gender, egg_groups=(row[20], row[21]), growth=row[19], abilities=(row[22], row[23]), learnset=moves,
            dex_national=None, tm_donors=[donor], shiny_shift=0.35)
        pic_from_png(r, pic, os.path.join(A, key, 'front.png'))
        t = TRAINERS + 40 * tid
        nm = SA.text(name); assert len(nm) <= 12
        b[t + 4:t + 16] = nm + b'\xff' * (12 - len(nm))
        b[t + 3] = pic
        p = struct.unpack_from('<I', b, t + 36)[0] - 0x08000000
        n = b[t + 32]
        party = bytearray(b[p:p + 8 * n])
        last = 8 * (n - 1)
        struct.pack_into('<H', party, last + 4, slot)
        r.w32(t + 36, 0x08000000 + r.alloc(bytes(party), 4))
        print('task 15: %s (trainer %d, pic %d) species %d from donor %d, last Pokemon %s' % (name, tid, pic, slot, donor, name))

if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')

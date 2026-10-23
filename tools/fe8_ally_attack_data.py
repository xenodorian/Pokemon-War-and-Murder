#!/usr/bin/env python3
"""FE8 ally attack animation data for the FireRed ROM (plan: CURRENT_WORK.md, 2026-10-23).

Source: poekemblem decomp_overlay (src/ally_attack.c, src/data/ally_attack/NAME.h, graphics/battle_anims/ally_attack/NAME/).
pack(r, cb, tbl_pal_tag=0xEA01) allocates everything in the ROM and returns the ROM address of the species table:
  species table: 16-byte entries {u16 species, u8 numParts, u8 hit, u32 palPtr, u32 partsPtr, u32 pad}, ended by species 0xFFFF
  part (8 bytes): {u32 SpriteTemplate*, s16 x, s16 y}
  SpriteTemplate (24 bytes): {tileTag 0xFFFF, paletteTag, oam, anims, images, affineAnims 0x08231CFC, callback cb}
  OamData (8 bytes, one per used size, shared): attr0 = shape<<14, attr1 = size<<14, attr2 = priority 0 << 10 (drawn over the health boxes and the text box)
  SpriteFrameImage (8 bytes): {u32 data, u16 size, u16 0}; AnimCmd frame = image | duration<<16; end = 0x0000FFFF
  palette: 16 x u16 (r>>3)|(g>>3)<<5|(b>>3)<<10 from attack.pal (index 0 is the transparent magenta)
  frame pixels: 4bpp in GBA OBJ tile order (8x8 tiles, row-major over the sprite, 32 bytes per tile), frames consecutive.

Everything is parsed from the source files with regexes; nothing is copied by hand.

usage: fe8_ally_attack_data.py IN.gba OUT.gba   (self test: packs a dummy callback into OUT.gba and reads it back)
"""
import sys, os, re, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from inc import Rom
from PIL import Image

DECOMP = os.environ.get('POEKEMBLEM_DECOMP', '/home/user/poekemblem/decomp_overlay')
DATA_DIR = 'src/data/ally_attack'
GFX_DIR = 'graphics/battle_anims/ally_attack'
SPECIES = {'EIRIKA': 256, 'LARACHEL': 257, 'CORMAG': 258, 'INNES': 259, 'DUESSEL': 260,
           'DOZLA': 261, 'TANA': 262, 'JOSHUA': 263, 'MYRRH': 264}
ROM_BASE = 0x08000000
AFFINE_DUMMY = 0x08231CFC          # gDummySpriteAffineAnimTable
TAG_NONE = 0xFFFF
ANIMCMD_END = 0x0000FFFF
MAX_PARTS = 8                      # ALLY_ATTACK_MAX_PARTS
# (w, h) -> (OAM shape, OAM size)
# GBA OAM: shape 0 square (8,16,32,64), shape 1 wide (16x8, 32x8, 32x16, 64x32), shape 2 tall (8x16, 8x32, 16x32, 32x64): 32x64 and 64x32 are size 3.
OAM_CODES = {(64, 64): (0, 3), (32, 64): (2, 3), (64, 32): (1, 3), (32, 32): (0, 2)}

ROM_SIZE_MAX = 0x2000000            # GBA cartridge address space; the base ROM (16 MB) has too little free space for the data
LAST_REPORT = []                   # per species, filled by pack()
DUMMY_CB = ROM_BASE | 1


def _src(*p):
    return os.path.join(DECOMP, *p)


def _read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def _jasc(path):
    lines = _read(path).splitlines()
    assert lines[0] == 'JASC-PAL', path
    n = int(lines[2])
    cols = [tuple(int(v) for v in l.split()) for l in lines[3:3 + n]]
    assert len(cols) == 16 and all(len(c) == 3 and all(0 <= v <= 255 for v in c) for c in cols), path
    return cols


def _pal_bytes(cols):
    return struct.pack('<16H', *[(r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10) for r, g, b in cols])


def _tile(px, w, h):
    """w x h indexed pixels (one index per byte, row-major) -> 4bpp in GBA OBJ tile order."""
    out = bytearray(w * h // 2)
    tw = w // 8
    for ty in range(h // 8):
        for tx in range(tw):
            base = (ty * tw + tx) * 32
            for y in range(8):
                row = (ty * 8 + y) * w + tx * 8
                for x in range(4):
                    out[base + y * 4 + x] = px[row + 2 * x] | (px[row + 2 * x + 1] << 4)
    return bytes(out)


def _untile(b, w, h):
    px = bytearray(w * h)
    tw = w // 8
    for ty in range(h // 8):
        for tx in range(tw):
            base = (ty * tw + tx) * 32
            for y in range(8):
                row = (ty * 8 + y) * w + tx * 8
                for x in range(4):
                    v = b[base + y * 4 + x]
                    px[row + 2 * x] = v & 15
                    px[row + 2 * x + 1] = v >> 4
    return bytes(px)


def parse_species(name, key, species, defines, oam_defined, pal_rgb):
    h = _read(_src(DATA_DIR, name + '.h'))
    m = re.search(r'#define\s+(\w+)_ATTACK_HIT\s+(\d+)', h)
    assert m and m.group(1) == key, (name, m and m.group(1))
    hit = int(m.group(2))

    incbin = {int(n): p for n, p in re.findall(r'static const u8 s\w+?Gfx(\d+)\[\] = INCBIN_U8\("([^"]+)"\);', h)}

    # frame image tables: { sXGfxN + 0xS * k, 0xS }, k-th frame, S = frame byte size
    images = {}
    for n, body in re.findall(r'static const struct SpriteFrameImage s\w+?Images(\d+)\[\] = \{(.*?)\};', h, re.S):
        ents = re.findall(r'\{\s*s\w+?Gfx(\d+)\s*\+\s*0x([0-9A-Fa-f]+)\s*\*\s*(\d+)\s*,\s*0x([0-9A-Fa-f]+)\s*\}', body)
        sizes = []
        for k, (g, mul, idx, sz) in enumerate(ents):
            assert int(g) == int(n) and int(idx) == k and int(mul, 16) == int(sz, 16), (name, n, k)
            sizes.append(int(sz, 16))
        images[int(n)] = sizes

    # sprite templates: one per part, OAM size, anim table and image table
    tmpl = {}
    for n, body in re.findall(r'static const struct SpriteTemplate s\w+?Template(\d+) = \{(.*?)\};', h, re.S):
        oam = re.search(r'\.oam = &sOamData_(\d+)x(\d+)', body)
        anims = re.search(r'\.anims = (s\w+?Anims)', body)
        imgs = re.search(r'\.images = s\w+?Images(\d+)', body)
        assert oam and anims and imgs, (name, n)
        assert int(imgs.group(1)) == int(n) and 'TAG_NONE' in body and 'SpriteCB_AllyAttack' in body, (name, n)
        assert anims.group(1) == 's%sAnims' % name, (name, n, anims.group(1))
        tmpl[int(n)] = (int(oam.group(1)), int(oam.group(2)))

    # parts: template index order, centre x, y on screen
    pm = re.search(r'static const struct AllyAttackPart s\w+?Parts\[\] = \{(.*?)\};', h, re.S)
    plist = re.findall(r'\{\s*&s\w+?Template(\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*\}', pm.group(1))
    assert len(plist) == len(tmpl) == len(images) and 0 < len(plist) <= MAX_PARTS, (name, len(plist))

    # animation script (shared by all parts): frame index, duration, ends with ANIMCMD_END
    am = re.search(r'static const union AnimCmd s\w+?Anim\[\] = \{(.*?)\};', h, re.S)
    body = am.group(1)
    assert body.rstrip().endswith('ANIMCMD_END'), name
    assert re.search(r'\*const s%sAnims\[\] = \{ s%sAnim \}' % (name, name), h), name
    cmds = []
    for img, dur in re.findall(r'ANIMCMD_FRAME\(\s*(\d+)\s*,\s*(\w+)\s*\)', body):
        d = int(dur) if dur.isdigit() else defines[dur]
        assert 0 <= d <= 63, (name, d)
        assert int(img) < 0xFFFF
        cmds.append(int(img) | (d << 16))
    total = sum(c >> 16 for c in cmds)
    assert 0 < hit < total, (name, hit, total)
    cmds.append(ANIMCMD_END)
    last_frame = max(c & 0xFFFF for c in cmds if c != ANIMCMD_END)

    parts = []
    for i, (pi, x, y) in enumerate(plist):
        assert int(pi) == i, (name, pi, i)
        w, fh = tmpl[i]
        assert (w, fh) in OAM_CODES and (w, fh) in oam_defined, (name, w, fh)
        assert images[i] and all(s == w * fh // 2 for s in images[i]), (name, i, images[i][:1])
        nf = len(images[i])
        assert last_frame < nf, (name, i, last_frame, nf)
        assert f'{GFX_DIR}/{name}/p{i}.4bpp' == incbin[i], (name, i, incbin.get(i))

        im = Image.open(_src(GFX_DIR, name, f'p{i}.png'))
        assert im.mode == 'P', (name, i)
        W, H = im.size
        assert W == w and H == nf * fh, (name, i, im.size, nf, fh)
        assert im.getpalette()[:48] == [c for col in pal_rgb for c in col], (name, i, 'palette differs from attack.pal')
        px = im.tobytes()
        assert max(px) < 16, (name, i)
        frames = [px[k * fh * w:(k + 1) * fh * w] for k in range(nf)]
        data = b''.join(_tile(f, w, fh) for f in frames)
        assert len(data) == nf * images[i][0], (name, i)
        parts.append({'w': w, 'h': fh, 'x': int(x), 'y': int(y), 'nf': nf, 'size': images[i][0],
                      'px': frames, 'data': data})

    return {'name': name, 'key': key, 'species': species, 'hit': hit, 'cmds': cmds, 'parts': parts,
            'pal': _pal_bytes(pal_rgb), 'pal_rgb': pal_rgb}


def parse_all():
    c = _read(_src('src/ally_attack.c'))
    defines = {m.group(1): int(m.group(2)) for m in re.finditer(r'^#define\s+(\w+)\s+(\d+)\b', c, re.M)}
    oam_defined = {(int(a), int(b)) for a, b in re.findall(r'OAM_DATA\((\d+),\s*(\d+)\)', c)}
    out = []
    for sp, name, key in re.findall(r'ANIM_ENTRY\(\s*SPECIES_(\w+?)\s*,\s*(\w+?)\s*,\s*(\w+?)\s*\)', c):
        assert sp == key and sp in SPECIES, (sp, name, key)
        pal = _jasc(_src(GFX_DIR, name, 'attack.pal'))
        out.append(parse_species(name, key, SPECIES[sp], defines, oam_defined, pal))
    assert len(out) == len(SPECIES), [s['name'] for s in out]
    return out


def pack(r, cb, tbl_pal_tag=0xEA01):
    """Writes the ally attack data into Rom r and returns the ROM address of the species table."""
    assert cb & 1 and (cb & ~1) >> 24 == 0x08, hex(cb)
    specs = parse_all()
    del LAST_REPORT[:]
    # space check before writing anything: the raw bytes plus up to 3 bytes of alignment per allocation
    raw = 16 * (len(specs) + 1)                                   # species table and its terminator
    raw += 8 * len({(p['w'], p['h']) for sp in specs for p in sp['parts']})   # shared OamData
    allocs = len(specs) + 1 + len({(p['w'], p['h']) for sp in specs for p in sp['parts']})
    for sp in specs:
        raw += len(sp['pal']) + 4 * len(sp['cmds']) + 4 + 8 * len(sp['parts'])   # palette, anim script, anim table, parts
        allocs += 4 + 3 * len(sp['parts'])
        for p in sp['parts']:
            raw += len(p['data']) + 8 * p['nf'] + 24     # frames, SpriteFrameImage table, SpriteTemplate
    need = raw + 3 * allocs
    avail = len(r.b) - r.cur
    if need > avail:
        raise RuntimeError('ally attack data needs about %d bytes, the ROM has %d free from 0x%X: expand the ROM to %d bytes first'
                           % (need, avail, r.cur, ROM_SIZE_MAX))
    rom = lambda off: ROM_BASE + off
    oam_cache = {}

    def oam(w, h):
        if (w, h) not in oam_cache:
            shape, size = OAM_CODES[(w, h)]
            oam_cache[(w, h)] = r.alloc(struct.pack("<HHHH", shape << 14, size << 14, 0 << 10, 0), 4)
        return oam_cache[(w, h)]

    shared_start = r.cur
    for sp in specs:                                   # OAM shapes used by any part, allocated once up front
        for p in sp['parts']:
            oam(p['w'], p['h'])
    recs = []
    for sp in specs:
        start = r.cur
        pal = r.alloc(sp['pal'], 4)
        cmds = r.alloc(struct.pack('<%dI' % len(sp['cmds']), *sp['cmds']), 4)
        anims = r.alloc(struct.pack('<I', rom(cmds)), 4)
        tmpls = []
        for i, p in enumerate(sp['parts']):
            data = r.alloc(p['data'], 4)
            imgs = r.alloc(b''.join(struct.pack('<IHH', rom(data + k * p['size']), p['size'], 0)
                                    for k in range(p['nf'])), 4)
            t = r.alloc(struct.pack('<HHIIIII', TAG_NONE, tbl_pal_tag, rom(oam(p['w'], p['h'])),
                                    rom(anims), rom(imgs), AFFINE_DUMMY, cb), 4)
            tmpls.append((t, p))
        parts = r.alloc(b''.join(struct.pack('<Ihh', rom(t), p['x'], p['y']) for t, p in tmpls), 4)
        recs.append((sp, pal, parts))
        LAST_REPORT.append({'name': sp['name'], 'species': sp['species'], 'hit': sp['hit'],
                            'parts': [(p['w'], p['h'], p['nf']) for p in sp['parts']],
                            'frames': sum(c >> 16 for c in sp['cmds'] if c != ANIMCMD_END),
                            'bytes': r.cur - start, 'pal': rom(pal), 'partsaddr': rom(parts)})
    tbl = r.alloc(b''.join(struct.pack('<HBBIII', sp['species'], len(sp['parts']), sp['hit'],
                                       rom(pal), rom(parts), 0) for sp, pal, parts in recs)
                  + struct.pack('<HBBIII', 0xFFFF, 0, 0, 0, 0, 0), 4)
    LAST_REPORT.append({'name': 'ALL', 'bytes': r.cur - shared_start})
    return rom(tbl)


def _check_rom(data, table_addr, specs):
    """Reads the packed data back from the ROM bytes and compares it with the parsed source."""
    base = lambda a: a - ROM_BASE
    def u32(o): return struct.unpack('<I', data[o:o + 4])[0]
    def rd(a, n): return data[base(a):base(a) + n]
    t = base(table_addr)
    n_checked = 0
    for i, sp in enumerate(specs):
        sp_, n, hit, palp, partsp, pad = struct.unpack('<HBBIII', data[t + 16 * i:t + 16 * i + 16])
        assert (sp_, n, hit, pad) == (sp['species'], len(sp['parts']), sp['hit'], 0), sp['name']
        assert rd(palp, 32) == sp['pal'], sp['name'] + ' palette'
        for j, p in enumerate(sp['parts']):
            tm, x, y = struct.unpack('<Ihh', rd(partsp + 8 * j, 8))
            assert (x, y) == (p['x'], p['y']), (sp['name'], j)
            tt, tag, oamp, animp, imgp, aff, cbk = struct.unpack('<HHIIIII', rd(tm, 24))
            assert (tt, tag, aff, cbk) == (TAG_NONE, 0xEA01, AFFINE_DUMMY, DUMMY_CB), (sp['name'], j)
            a0, a1, a2, _ = struct.unpack('<HHHH', rd(oamp, 8))
            shape, size = OAM_CODES[(p['w'], p['h'])]
            assert (a0 >> 14, a1 >> 14, (a2 >> 10) & 3, a2 & 0x3FF) == (shape, size, 1, 0), (sp['name'], j)
            seq = struct.unpack('<%dI' % len(sp['cmds']), rd(u32(base(animp)), 4 * len(sp['cmds'])))
            assert list(seq) == sp['cmds'], (sp['name'], j)
            for k in range(p['nf']):
                dp, sz, z = struct.unpack('<IHH', rd(imgp + 8 * k, 8))
                assert sz == p['size'] and z == 0 and ROM_BASE <= dp < ROM_BASE + len(data), (sp['name'], j, k)
                px = _untile(rd(dp, sz), p['w'], p['h'])
                assert px == p['px'][k], (sp['name'], j, k, 'pixels')
            n_checked += p['nf']
    end = struct.unpack('<HBBIII', data[t + 16 * len(specs):t + 16 * len(specs) + 16])
    assert end[0] == 0xFFFF, 'table terminator'
    return n_checked


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    orig = open(argv[1], 'rb').read()
    r = Rom(argv[1])
    if len(r.b) < ROM_SIZE_MAX:                        # the scratch output is grown to 32 MB, the data does not fit in 16 MB
        r.b.extend(b'\xff' * (ROM_SIZE_MAX - len(r.b)))
    before = r.cur
    addr = pack(r, DUMMY_CB)
    r.save(argv[2])
    out = open(argv[2], 'rb').read()
    assert len(out) == ROM_SIZE_MAX
    diff = [i for i in range(len(out)) if (orig[i] if i < len(orig) else 0xFF) != out[i]]
    assert diff and diff[0] >= before and diff[-1] < r.cur, (hex(diff[0]), hex(diff[-1]), hex(before), hex(r.cur))
    specs = parse_all()
    frames = _check_rom(out, addr, specs)
    print('%-9s %4s %5s %4s  %-28s %8s' % ('species', 'id', 'parts', 'hit', 'parts WxH x frames', 'bytes'))
    for rep in LAST_REPORT:
        if rep['name'] == 'ALL':
            continue
        desc = ' '.join('%dx%dx%d' % p for p in rep['parts'])
        print('%-9s %4d %5d %4d  %-28s %8d  (anim %d frames)' % (rep['name'], rep['species'], len(rep['parts']),
                                                              rep['hit'], desc, rep['bytes'], rep['frames']))
    total = r.cur - before
    assert total == [x for x in LAST_REPORT if x['name'] == 'ALL'][0]['bytes']
    print('species table at ROM address 0x%08X' % addr)
    print('frames checked by read-back: %d' % frames)
    print('total bytes added (with alignment): %d (0x%X)' % (total, total))
    print('self test OK; wrote %s' % argv[2])
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))

"""Bless / threaten / leave at the end of bystander dialogue.

A bystander is a person who only walks and talks: vanilla graphic, no hide flag,
not a trainer, not police, and a script that never changes the world (no items,
flags, vars, warps, shops, battles, or native calls).

usage: bystander.py IN.gba OUT.gba
Once per person. Blessing gives no item and raises reputation by 1.
Threatening pays 50 to 200 and lowers reputation by 1.
"""
import os, sys, struct, subprocess, collections, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from inc import Rom
from shinigami import SB, put_script
from g3 import ENC, dec

MAGIC = b'BYSTAND1'
MAGIC2 = b'BYSTAND2'
GROUPS = 0x3526A8
MENU_REFS = (0x9CB58, 0x9CFD4)
BLACK = bytes.fromhex('fc04020003')
GRAYC = bytes.fromhex('fc04030003')
SRC = os.path.join(HERE, '..', 'story')
WORK = '/tmp/bystander_build'
EVENT_INC = '/tmp/event.inc'
MAP_JSON = '/tmp/map_groups.json'

# opcode byte, then these extra sizes. Pointers here are movement, not scripts.
EXTRA = {
    0x4f: [2, 4],
    0x50: [2, 4, 1, 1],
    0x51: [2],
    0x52: [2, 1, 1],
    0x53: [2],
    0x54: [2, 1, 1],
    0x55: [2],
    0x56: [2, 1, 1],
    0x58: [2, 1, 1],
    0x59: [2, 1, 1],
    0x39: [1, 1, 1, 2, 2],
    0x3a: [1, 1, 1, 2, 2],
    0x3b: [1, 1, 1, 2, 2],
    0x3c: [1, 1],
    0x3d: [1, 1, 1, 2, 2],
    0x3e: [1, 1, 1, 2, 2],
    0x3f: [1, 1, 1, 2, 2],
    0x40: [1, 1, 1, 2, 2],
    0x41: [1, 1, 1, 2, 2],
    0xd1: [1, 1, 1, 2, 2],
    0xa2: [],
}
WORLD = {
    'setflag', 'clearflag', 'additem', 'removeitem', 'addpcitem', 'checkitemspace',
    'givemon', 'giveegg', 'setmonmove', 'warp', 'warpsilent', 'warpdoor', 'warphole',
    'warpteleport', 'warpspinenter', 'setwarp', 'setdynamicwarp', 'setdivewarp',
    'setholewarp', 'pokemart', 'pokemartdecoration', 'pokemartdecoration2',
    'playslotmachine', 'addobject', 'removeobject', 'hideobjectat', 'showobjectat',
    'settrainerflag', 'cleartrainerflag', 'dotrainerbattle', 'fadescreen',
    'setmaplayoutindex', 'special', 'specialvar', 'callnative', 'gotonative',
    'setobjectxy', 'setobjectxyperm', 'moveobjectoffscreen', 'createvobject',
    'setobjectmovementtype', 'copyobjectxytoperm', 'opendoor', 'closedoor',
    'waitdooranim', 'setdooropened', 'setdoorclosed', 'addelevation',
    'setelevation', 'removeobjectat', 'addobjectat',
}
# writes of a save var (below the specials) count as a purpose
VAR_WRITE = {0x16, 0x17, 0x18, 0x19, 0x1a}
TERMINAL = {0x02, 0x03, 0x05, 0x08, 0x0c, 0x0d}
JUMP = {0x04, 0x05, 0x06, 0x07}


def load_ops():
    t = open(EVENT_INC).read()
    ops = {}
    for m in re.finditer(r'\.macro\s+(\w+)([^\n]*)\n(.*?)\n\s*\.endm', t, re.S):
        lines = [l.split('@')[0].strip() for l in m.group(3).split('\n')]
        lines = [l for l in lines if l]
        if lines and lines[0].startswith('.byte 0x') and all(
                l.split()[0] in ('.byte', '.2byte', '.4byte') for l in lines):
            op = int(lines[0].split()[1], 16)
            if op not in ops:
                ops[op] = (m.group(1), [{'.byte': 1, '.2byte': 2, '.4byte': 4}[l.split()[0]] for l in lines[1:]])
    for op, sz in EXTRA.items():
        ops.setdefault(op, ('op%02x' % op, sz))
    return ops


def map_sizes():
    import json
    mg = json.load(open(MAP_JSON))
    sizes = [len(mg[g]) for g in mg['group_order']]
    sizes[2] = 82
    assert sizes[1] == 123 and sizes[3] == 66 and len(sizes) == 43
    return sizes


def enc(s):
    return bytes(ENC[c] for c in s) + b'\xff'


def compile_native(r, entries, rep):
    os.makedirs(WORK, exist_ok=True)
    ent = ','.join(str(b) for row in entries for b in row)
    open(os.path.join(WORK, 'bystander_gen.h'), 'w').write(
        '#define BY_N %d\nstatic const u8 BY_ENT[]={%s};\n'
        '#define REP_CALC_ADDR 0x%08x\n'
        % (len(entries), ent or '0', rep))
    r.cur = (r.cur + 3) & ~3
    base = 0x08000000 + r.cur
    ld = os.path.join(WORK, 'by.ld')
    o = os.path.join(WORK, 'by.o')
    e = os.path.join(WORK, 'by.elf')
    bn = os.path.join(WORK, 'by.bin')
    open(ld, 'w').write(
        'ENTRY(by_gate)\nSECTIONS { . = 0x%08x; .all : { *(.text*) *(.rodata*) *(.data*) } '
        '/DISCARD/ : { *(.ARM.exidx*) *(.comment) *(.note*) *(.ARM.attributes) } }\n' % base)
    env = dict(os.environ, PATH='/tmp/bin:' + os.environ.get('PATH', ''))
    subprocess.run(['clang', '--target=thumbv4t-none-eabi', '-mthumb', '-Os', '-ffreestanding',
                    '-fno-builtin', '-fno-pic', '-fno-stack-protector', '-nostdlib',
                    '-fno-unwind-tables', '-fno-asynchronous-unwind-tables',
                    '-I', WORK, '-c', os.path.join(SRC, 'bystander_native.c'), '-o', o], check=True, env=env)
    subprocess.run(['ld.lld', '-T', ld, o, '-o', e], check=True, env=env)
    subprocess.run(['llvm-objcopy', '-O', 'binary', e, bn], check=True, env=env)
    blob = open(bn, 'rb').read()
    a = r.alloc(blob, 4)
    assert 0x08000000 + a == base
    sym = {}
    for ln in subprocess.run(['nm', e], capture_output=True, text=True, check=True, env=env).stdout.split('\n'):
        f = ln.split()
        if len(f) == 3 and f[2] in ('by_note', 'by_gate', 'by_bless', 'by_threat'):
            sym[f[2]] = (int(f[0], 16) & ~1) | 1
    assert set(sym) == {'by_note', 'by_gate', 'by_bless', 'by_threat'}
    return sym


def apply(r):
    b = r.b
    if b.find(MAGIC2, 0xA00000) >= 0:
        print('bystander: already applied')
        return
    OPS = load_ops()
    SIZES = map_sizes()

    def r32(o):
        return struct.unpack_from('<I', b, o)[0]

    def r16(o):
        return struct.unpack_from('<H', b, o)[0]

    def inrom(p):
        return 0x08000000 <= p < 0x08000000 + len(b)

    groups = [r32(GROUPS + 4 * i) - 0x08000000 for i in range(43)]

    def walk(root):
        ins = {}
        q = [root]
        n = 0
        while q:
            p = q.pop()
            if not inrom(p) or (p - 0x08000000) in ins:
                continue
            a = p - 0x08000000
            guard = 0
            while guard < 400:
                guard += 1
                n += 1
                if n > 500 or a >= len(b):
                    return 'oversize', None
                if a in ins:
                    break
                op = b[a]
                if op == 0x5c:
                    return 'trainerbattle', None
                if op not in OPS:
                    return 'op%02x' % op, None
                name, sizes = OPS[op]
                start = a
                a += 1
                args = []
                for z in sizes:
                    if a + z > len(b):
                        return 'trunc', None
                    args.append(int.from_bytes(b[a:a + z], 'little'))
                    a += z
                raw = bytearray(b[start:a])
                jumps = []
                if op in JUMP:
                    jumps.append((1 + sum(sizes[:-1]), args[-1]))
                    if inrom(args[-1]):
                        q.append(args[-1])
                if name in WORLD or (op in EXTRA and name.startswith('op') and op in (0x53, 0x54, 0x55, 0x56, 0x58, 0x59)):
                    return name, None
                if op in (0x39, 0x3a, 0x3b, 0x3c, 0x3d, 0x3e, 0x3f, 0x40, 0x41, 0xd1):
                    return 'warp', None
                if op in VAR_WRITE and args and args[0] < 0x8000:
                    return 'var%04x' % args[0], None
                ins[start] = (raw, jumps)
                if op in TERMINAL:
                    break
        if not ins:
            return 'empty', None
        return 'ok', ins

    def clone(ins):
        addrs = sorted(ins)
        # contiguous runs keep fall-through
        runs = []
        run = [addrs[0]]
        for prev, cur in zip(addrs, addrs[1:]):
            if cur == prev + len(ins[prev][0]):
                run.append(cur)
            else:
                runs.append(run)
                run = [cur]
        runs.append(run)
        # each run must end on a terminal, or the next byte is also an instruction we have
        for run in runs:
            last = run[-1]
            op = ins[last][0][0]
            if op not in TERMINAL:
                return None
        total = sum(len(ins[a][0]) for a in addrs)
        blob_at = {}
        pos = 0
        # place runs in address order so a run is contiguous in the clone
        pieces = []
        for run in runs:
            for a in run:
                blob_at[a] = pos
                pos += len(ins[a][0])
            pieces.append(run)
        blob = bytearray(total)
        pos = 0
        for run in pieces:
            for a in run:
                raw, jumps = ins[a]
                chunk = bytearray(raw)
                if chunk[0] == 0x02:
                    chunk[0] = 0x03
                elif chunk[0] == 0x0d:
                    chunk[0] = 0x0c
                blob[pos:pos + len(chunk)] = chunk
                pos += len(chunk)
        base = r.alloc(bytes(blob), 4)
        # patch internal jumps now that the base is known
        for a, (raw, jumps) in ins.items():
            for off, target in jumps:
                to = target - 0x08000000
                if to not in blob_at:
                    continue
                struct.pack_into('<I', r.b, base + blob_at[a] + off, 0x08000000 + base + blob_at[to])
        # no end opcodes left
        body = bytes(r.b[base:base + total])
        assert 0x02 not in _opcodes(body, ins, blob_at), 'end survived'
        return 0x08000000 + base

    def _opcodes(body, ins, blob_at):
        ops = []
        for a in ins:
            ops.append(body[blob_at[a]])
        return ops

    reasons = collections.Counter()
    people = []
    seen_obj = set()
    for g, nmaps in enumerate(SIZES):
        gp = groups[g]
        for n in range(nmaps):
            hp = r32(gp + 4 * n)
            if not inrom(hp):
                continue
            h = hp - 0x08000000
            evp = r32(h + 4)
            if not inrom(evp):
                continue
            ev = evp - 0x08000000
            no = b[ev]
            if no > 64:
                continue
            po = r32(ev + 4) - 0x08000000
            if po < 0 or po + 24 * no > len(b):
                continue
            for i in range(no):
                o = po + 24 * i
                lid = b[o]
                gfx = b[o + 1]
                trainer = r16(o + 0x0C)
                flag = r16(o + 0x14)
                sp = r32(o + 0x10)
                if lid == 0 or gfx >= 0x58 or gfx == 60 or flag or trainer or not inrom(sp):
                    continue
                key = (g, n, lid)
                if key in seen_obj:
                    continue
                seen_obj.add(key)
                # a previous pass already wrapped this person: call clone, goto menu
                if b[sp - 0x08000000] == 0x04 and b[sp - 0x08000000 + 5] == 0x05:
                    clone_p = r32(sp - 0x08000000 + 1)
                    if inrom(clone_p):
                        people.append((g, n, lid, clone_p, o + 0x10, None))
                        continue
                status, ins = walk(sp)
                if status != 'ok':
                    reasons[status] += 1
                    continue
                people.append((g, n, lid, sp, o + 0x10, ins))

    # one clone per script. None means the script is already a clone.
    clones = {}
    kept = []
    for g, n, lid, sp, ptr_at, ins in people:
        if ins is None:
            clones[sp] = sp
        elif sp not in clones:
            clones[sp] = clone(ins)
        if clones[sp] is None:
            reasons['falloff'] += 1
            continue
        kept.append((g, n, lid, sp, ptr_at))
    assert kept, 'no bystanders'
    assert len(kept) <= 3200

    i = b.find(b'STORYFN1', 0xA00000)
    assert i > 0, 'rep_calc missing'
    rep = struct.unpack_from('<I', b, i + 8)[0]
    assert rep & 1, hex(rep)

    tab = r32(MENU_REFS[0]) - 0x08000000
    k = 0
    while True:
        p = r32(tab + 8 * k)
        c = b[tab + 8 * k + 4]
        if not (0x08000000 <= p < 0x0A000000) or c == 0 or c > 30:
            break
        k += 1

    def add_menu(rows):
        raws = b''
        for text, gray in rows:
            raw = (GRAYC if gray else BLACK) + enc(text)
            raws += struct.pack('<II', 0x08000000 + r.alloc(raw, 1), 0)
        return 0x08000000 + r.alloc(raws, 4), len(rows)

    fresh_p, fresh_n = add_menu([('BLESS', 0), ('THREATEN', 0), ('LEAVE', 0)])
    done_p, done_n = add_menu([('BLESS', 1), ('THREATEN', 1), ('LEAVE', 0)])
    ents = bytes(b[tab:tab + 8 * k])
    ents += struct.pack('<IBBBB', fresh_p, fresh_n, 0, 0, 0)
    ents += struct.pack('<IBBBB', done_p, done_n, 0, 0, 0)
    newtab = r.alloc(ents, 4)
    for ref in MENU_REFS:
        r.w32(ref, 0x08000000 + newtab)
    fresh_id, done_id = k, k + 1

    entries = [(g, n, lid) for g, n, lid, sp, ptr_at in kept]
    fn = compile_native(r, entries, rep)
    bless = 0x08000000 + r.alloc(enc('You bless them.\nYour reputation rose.'), 1)
    pay = 0x08000000 + r.alloc(bytes(ENC[c] for c in 'They hand over $') + bytes([0xFD, 0x02]) + enc('.\nYour reputation fell.'), 1)

    S = SB()
    S.raw(0x68)
    S.lock()
    S.raw(0x23); S.ptr(fn['by_gate'])
    S.compare(0x8008, 1); S.goto_if(1, 'used')
    S.raw(0x6F, 0, 0, fresh_id, 0); S.goto('chosen')
    S.lab('used')
    S.raw(0x70, 0, 0, done_id, 2, 0)          # cursor starts on LEAVE
    S.compare(0x800D, 1); S.goto_if(3, 'used')  # bless or threaten: dead, menu again
    S.goto('leave')
    S.lab('chosen')
    S.compare(0x800D, 0); S.goto_if(1, 'bless')
    S.compare(0x800D, 1); S.goto_if(1, 'threat')
    S.goto('leave')
    S.lab('bless')
    S.raw(0x23); S.ptr(fn['by_bless'])
    S.msg(bless, 4); S.goto('leave')
    S.lab('threat')
    S.raw(0x23); S.ptr(fn['by_threat'])
    S.raw(0x83, 0); S._add(struct.pack('<H', 0x8000))
    S.msg(pay, 4)
    S.lab('leave')
    S.releaseall(); S.end()
    menu = 0x08000000 + put_script(r, S)

    for g, n, lid, sp, ptr_at in kept:
        W = SB()
        W.raw(0x16); W._add(struct.pack('<HH', 0x8000, lid))
        W.raw(0x16); W._add(struct.pack('<HH', 0x8001, n | (g << 8)))
        W.raw(0x23); W.ptr(fn['by_note'])
        W.raw(0x04); W.ptr(clones[sp])
        W.raw(0x05); W.ptr(menu)
        r.w32(ptr_at, 0x08000000 + put_script(r, W))

    r.alloc(MAGIC2, 4)
    # a few towns, so a test can find someone
    show = [p for p in kept if p[0] == 3 and p[1] in (0, 1, 3)]
    print('bystander: %d people, menus %d/%d, skipped %s' % (len(kept), fresh_id, done_id, dict(reasons)))
    print('bystander: menu', hex(menu), 'natives', {k: hex(v) for k, v in fn.items()})
    for g, n, lid, sp, ptr_at in show[:12]:
        print('  map', (g, n), 'lid', lid, 'at', hex(0x08000000 + ptr_at - 0x10))


if __name__ == '__main__':
    r = Rom(sys.argv[1])
    apply(r)
    r.save(sys.argv[2])
    print('ok', hex(r.cur))

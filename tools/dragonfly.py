"""Dragonfly, move 360 (usage: dragonfly.py IN.gba OUT.gba). Runs on the current ROM; do not re-run accuracy or UNSTABLE stages.
Gyarados (130) learns it at level 20, after Bite, and its base Special Attack becomes 125. It does not learn Bubblebeam.
The move is Fly: same power, accuracy, PP, target, flags and two-turn semi-invulnerable script ("flew up high", Fly's animation),
but Dragon type, its own effect. On the connecting hit the target's Defense falls one stage (text, arrows, sound) and it is confused.
From the party menu it travels like Fly and the usability check always returns true, so no badge is required.
"""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from inc import Rom
import species_add as SA
import move_tables as MT
import moves_extend as ME

OLD_N = 360; NEW_N = 361; MOVE = 360; FLY = 19
EFFECT = 15; EFFECT_TABLE = 0x1d65a8
GYARADOS = 130; LEARN = 0x25d7b4; BASE = 0x254784; NAMES = 0x245ee0
DRAGON = 16; BITE = 44; BUBBLEBEAM = 61
# battle RAM / script targets (absolute), taken from Fly's own script
HITMARKER = 0x02023DD0; CURRENT_MOVE = 0x02023D4A; STRING_ID = 0x02023FD3
CHOOSER = 0x02023E85; ANIM_TURN = 0x02023FDC; RESULT = 0x02023DCC
STATCHANGER = 0x02023FDE; MULTI = 0x02023E87; ANIM_ARG1 = 0x02023FD4
STAT_DOWN_STRINGS = 0x083FE588
CHARGING_TURN = 0x081D6F58; MOVE_END = 0x081D694E; MOVE_MISSED = 0x081D695E
MULTIPLETURNS = 0x1000; NO_ATTACKSTRING = 0x200; NO_PPDEDUCT = 0x800
NO_EFFECT = 0x29          # missed | doesn't affect | failed, the mask Fly's neighbors test with
STAT_DEF = 2
# field move (the live sewer-slide tables; the addresses in build.py are the dead originals)
FM_LIST = 0xA01DB4; FM_LIST_PTR = 0x122A7C
FM_CB = 0xA01DD4; FM_CB_PTRS = (0x124614, 0x124680)
FM_ALWAYS = 0x08A01DD1    # movs r0,#1; bx lr
FM_JT = 0xA01F34; FM_JT_PTR = 0x124684; FM_CMP = 0x124670
FM_FLY = 0x0812474C; FM_USE = 0x081245A5
FM_HELP = 0xA01F7C; FM_HELP_PTR = 0x1221D0; FLY_HELP = 0x08417548
FM_CO_NEW = 0xA01F34      # dead once the jump table is relocated; action 0x1F lands here

def stat_down(stat, stages): return stat | (stages << 4) | 0x80

def script_bytes(base):
    P = lambda a: struct.pack('<I', a)
    parts = []; labels = {}
    def emit(b): parts.append(('b', b))
    def lab(n): labels[n] = sum(len(x[1]) if x[0] == 'b' else 4 for x in parts)
    def ref(n): parts.append(('r', n))
    def go(addr): emit(bytes([0x28])); parts.append(('a', addr))
    # turn 1, same shape as Fly but the string is always "flew up high"
    emit(bytes([0x1d, 1]) + P(MULTIPLETURNS)); ref('second')
    emit(bytes([0x2b, 4]) + P(HITMARKER) + P(NO_ATTACKSTRING)); ref('second')
    emit(bytes([0x2e]) + P(STRING_ID) + bytes([4]))
    emit(bytes([0x41]) + P(CHARGING_TURN))
    emit(bytes([0xc5])); go(MOVE_END)
    # turn 2
    lab('second')
    emit(bytes([0x00]))
    emit(bytes([0x2e]) + P(CHOOSER) + bytes([12]))          # MOVE_EFFECT_CHARGING, so the dive half plays
    emit(bytes([0x2e]) + P(ANIM_TURN) + bytes([1]))
    emit(bytes([0x18, 1]))
    emit(bytes([0x35]) + P(HITMARKER) + P(NO_PPDEDUCT))
    emit(bytes([0x01])); ref('miss'); emit(struct.pack('<H', 0))
    emit(bytes([0xc6]))
    # the hit, inlined from HitFromAtkString so both extras can run (that script does one effect)
    emit(bytes([0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x09, 0x0a, 0x0e, 0x5c, 0x00, 0x3a, 0x0b, 0x00, 0x0c, 0x00, 0x0d]))
    emit(bytes([0x12, 0x40, 0x00, 0x0f, 0x12, 0x40, 0x00]))
    emit(bytes([0x29, 4]) + P(RESULT) + bytes([NO_EFFECT])); ref('faint')
    emit(bytes([0x2e]) + P(STATCHANGER) + bytes([stat_down(STAT_DEF, 1)]))
    emit(bytes([0x89, 1])); ref('confuse')
    emit(bytes([0x29, 3]) + P(MULTI) + bytes([2])); ref('do_anim')   # chooser < 2: a normal drop, show the arrows
    emit(bytes([0x29, 0]) + P(MULTI) + bytes([3])); ref('confuse')   # chooser == 3: nothing happened
    emit(bytes([0x39, 0x20, 0x00])); go_print = True
    emit(bytes([0x28])); ref('print')
    lab('do_anim')
    emit(bytes([0x47, 0x45, 0x00, 0x01]) + P(ANIM_ARG1))
    emit(bytes([0x0a]))
    lab('print')
    emit(bytes([0x13]) + P(STAT_DOWN_STRINGS))
    emit(bytes([0x12, 0x40, 0x00]))
    lab('confuse')
    emit(bytes([0x2e]) + P(CHOOSER) + bytes([7]))             # MOVE_EFFECT_CONFUSION. seteffectprimary applies it; the CERTAIN bit would miss every case and hang
    emit(bytes([0x16]))
    lab('faint')
    emit(bytes([0x19, 0, 0, 0, 0, 0, 0])); go(MOVE_END)
    lab('miss')
    emit(bytes([0xc6])); go(MOVE_MISSED)
    assert go_print
    out = bytearray()
    for k, v in parts:
        if k == 'b': out += v
        elif k == 'a': out += P(v)
        else: out += P(base + labels[v])
    # every opcode must be one this ROM's battle interpreter knows, and the walk must end on the last byte
    size = {0x00:0,0x01:6,0x02:0,0x03:0,0x04:0,0x05:0,0x06:0,0x07:0,0x09:0,0x0a:0,0x0b:1,0x0c:1,0x0d:0,0x0e:0,
            0x0f:0,0x12:2,0x13:4,0x16:0,0x18:1,0x19:6,0x1d:9,0x28:4,0x29:10,0x2b:13,0x2e:5,0x35:8,0x39:2,0x3a:0,0x41:4,
            0x45:6,0x47:0,0x5c:1,0x89:5,0xc5:0,0xc6:0}
    i = 0
    while i < len(out):
        op = out[i]
        assert op in size, hex(op)
        i += 1 + size[op]
    assert i == len(out), (i, len(out))
    return bytes(out)

def apply(r):
    b = r.b
    L = MT.live(b)
    assert struct.unpack_from('<I', b, 0x40238)[0] == OLD_N and struct.unpack_from('<I', b, 0x933e8)[0] == OLD_N, 'sentinels'
    assert b[L['md'] + 12 * FLY:L['md'] + 12 * FLY + 12] == bytes.fromhex('9b46025f0f00000033000000'), 'Fly record moved'
    assert all(b[L['md'] + 12 * m] != EFFECT for m in range(OLD_N)), 'effect 15 is in use'
    for o in (0xd75fc, 0xd7e96, 0xd7eae):
        assert b[o] == 0xb5 and b[o + 4:o + 6] == b'\x81\x42', 'battle text limit'  # ids below 362 already print
    # 1. effect script
    base = r.cur = (r.cur + 3) & ~3
    a = r.alloc(script_bytes(0x08000000 + base), 4); assert a == base
    r.w32(EFFECT_TABLE + 4 * EFFECT, 0x08000000 + a)
    # 2. move tables: Fly's record, Dragon type, this effect, Fly's animation
    rec = bytearray(b[L['md'] + 12 * FLY:L['md'] + 12 * FLY + 12])
    rec[0] = EFFECT; rec[2] = DRAGON
    md_new = r.alloc(bytes(b[L['md']:L['md'] + 12 * OLD_N]) + bytes(rec), 4)
    names = bytearray(b[L['mn']:L['mn'] + 13 * OLD_N])
    n = SA.text('DRAGONFLY'); assert len(n) <= 13
    names += n + b'\xff' * (13 - len(n))
    mn_new = r.alloc(bytes(names), 4)
    desc = SA.text('Flies up, then strikes.\nLowers Defense and\nconfuses the foe.')
    descs = bytes(b[L['mdesc']:L['mdesc'] + 4 * (OLD_N - 1)]) + struct.pack('<I', 0x08000000 + r.alloc(desc, 1))
    mdesc_new = r.alloc(descs, 4)
    anims = bytes(b[L['anim']:L['anim'] + 4 * OLD_N]) + bytes(b[L['anim'] + 4 * FLY:L['anim'] + 4 * FLY + 4])
    anim_new = r.alloc(anims, 4)
    pp = ME.repoint(b, L['md'] + 4, md_new + 4)
    counts = (ME.repoint(b, L['md'], md_new), ME.repoint(b, L['mn'], mn_new),
              ME.repoint(b, L['mdesc'], mdesc_new), ME.repoint(b, L['anim'], anim_new))
    assert pp > 0 and all(c > 0 for c in counts), (pp, counts)
    for o in ME.SENTINEL_SITES: r.w32(o, NEW_N)
    # 3. Gyarados: SpA 125, learn Dragonfly at 20 right after Bite. No Bubblebeam.
    st = BASE + 28 * GYARADOS
    assert b[NAMES + 11 * GYARADOS:NAMES + 11 * GYARADOS + 8] == SA.text('GYARADOS')[:8]
    assert b[st + 4] == 60, b[st + 4]
    b[st + 4] = 125
    p = struct.unpack_from('<I', b, LEARN + 4 * GYARADOS)[0] - 0x08000000
    moves = []
    while True:
        v = struct.unpack_from('<H', b, p)[0]; p += 2
        if v == 0xffff: break
        moves.append((v >> 9, v & 0x1ff))
    assert (20, BITE) in moves and all(m != BUBBLEBEAM for _, m in moves), moves
    moves.append((20, MOVE)); moves.sort(key=lambda t: t[0])
    data = b''.join(struct.pack('<H', (lv << 9) | m) for lv, m in moves) + b'\xff\xff'
    r.w32(LEARN + 4 * GYARADOS, 0x08000000 + r.alloc(data, 2))
    # 4. party menu: one more field move, usability always true, same handler as Fly
    ids = []
    o = FM_LIST
    while True:
        w = struct.unpack_from('<H', b, o)[0]; o += 2
        ids.append(w)
        if w == 0x000c: break
    assert ids[-2] == 344 and len(ids) == 14, ids
    ids.insert(-1, MOVE)
    nref = ME.repoint(b, FM_LIST, r.alloc(b''.join(struct.pack('<H', w) for w in ids), 2))
    assert nref == 1, nref
    cb = bytes(b[FM_CB:FM_CB + 13 * 8]) + struct.pack('<II', FM_ALWAYS, 0xD)
    cb_at = r.alloc(cb, 4)
    for ptr in FM_CB_PTRS:
        assert r.r32(ptr) == 0x08000000 + FM_CB, hex(ptr)
        r.w32(ptr, 0x08000000 + cb_at)
    jt = [struct.unpack_from('<I', b, FM_JT + 4 * i)[0] for i in range(11)]
    assert jt[0] == FM_FLY and jt[10] == FM_FLY, [hex(x) for x in jt]
    jt.append(FM_FLY)
    jt_at = r.alloc(b''.join(struct.pack('<I', w) for w in jt), 4)
    assert r.r32(FM_JT_PTR) == 0x08000000 + FM_JT
    r.w32(FM_JT_PTR, 0x08000000 + jt_at)
    assert b[FM_CMP] == 0x0a and b[FM_CMP - 2:FM_CMP] == bytes([0xa0, 0x1e])
    b[FM_CMP] = 0x0b
    # the jump table no longer owns 0xA01F34; action 0x1F (field index 13) reads the name/func pair from there
    struct.pack_into('<II', b, FM_CO_NEW, 0x08000000 + mn_new + 13 * MOVE, FM_USE)
    help_n = 13
    hb = bytes(b[FM_HELP:FM_HELP + 4 * help_n]) + struct.pack('<I', FLY_HELP)
    assert r.r32(FM_HELP_PTR) == 0x08000000 + FM_HELP
    r.w32(FM_HELP_PTR, 0x08000000 + r.alloc(hb, 4))
    print('dragonfly: move %d effect %d script %s, Gyarados SpA %d, learns %s' % (MOVE, EFFECT, hex(0x08000000 + a), b[st + 4], moves))

if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')

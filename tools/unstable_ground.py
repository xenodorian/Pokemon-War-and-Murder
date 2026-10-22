"""Owner request: UNSTABLE GROUND, move 359, learned by Sandshrew (27) at level 8 (usage: unstable_ground.py IN.gba OUT.gba). Runs after sand_rocks.py.
 - Ground type, status move (power 0), accuracy 100, 5 PP, target FOES AND ALLY (Earthquake's target, so it hits every battler except the user).
   Earthquake's animation is used (its battle animation entry is copied).
 - effect 14 (unused in this ROM): a custom battle script. Ground-type targets are skipped. Other targets get accuracy -2, then evasion -2.
   The user is not affected (the owner's choice).
 - name "UNSTABLE" (the name field holds 12 characters, so "UNSTABLE GROUND" does not fit). Description is a best guess.
 - the move tables grow to 360 entries (same method as sand_grave.py), the code sentinels and the battle text limit go from 359 to 360
 - Sandshrew learns it at level 8."""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(1, '/home/claude/work/tools')
from inc import Rom
import species_add as SA
import move_tables as MT
import moves_extend as ME

OLD_N = 359; NEW_N = 360; NEW_MOVE = 359; EARTHQUAKE = 89
EFFECT = 14; SANDSHREW = 27; LEARN = 0x25d7b4
STATCHANGER = 0x02023fde           # gBattleScripting.statChanger (the setbyte operand of the base stat-change scripts)
STATDOWN_END = 0x081d6c5d          # BattleScript_StatDownEnd (goto BattleScript_MoveEnd), used by the base stat-change scripts
EFFECT_TABLE = 0x081d65a8          # gBattleScriptsForMoveEffects
SB_ATTACKCANCELER, SB_ATTACKSTRING, SB_PPREDUCE, SB_JUMPIFTYPE, SB_GOTO, SB_SETBYTE, SB_STATBUFFCHANGE = 0, 2, 3, 34, 40, 46, 137
TYPE_GROUND = 4; STAT_ACC, STAT_EVA = 6, 7
def stat_down(stat, stages): return stat | (stages << 4) | 0x80    # setstatchanger STAT, stages, TRUE

def script_bytes(base):
    """the effect script at ROM address base (all addresses are absolute)"""
    out = bytearray()
    def emit(*parts):
        for p in parts: out.extend(p)
    B = lambda *v: bytes(v)
    P = lambda a: struct.pack('<I', a)
    # layout: 0 attackcanceler, 1 attackstring, 2 ppreduce, 3 jumpiftype (7 bytes), 10 setbyte acc (6), 16 statbuffchange (6),
    # 22 setbyte eva (6, also the failure target of the accuracy change), 28 statbuffchange (6), 34 goto (5)
    EVA_L = base + 22
    emit(B(SB_ATTACKCANCELER), B(SB_ATTACKSTRING), B(SB_PPREDUCE))
    emit(B(SB_JUMPIFTYPE, 0, TYPE_GROUND), P(STATDOWN_END))
    emit(B(SB_SETBYTE), P(STATCHANGER), B(stat_down(STAT_ACC, 2)))
    emit(B(SB_STATBUFFCHANGE, 1), P(EVA_L))
    emit(B(SB_SETBYTE), P(STATCHANGER), B(stat_down(STAT_EVA, 2)))
    emit(B(SB_STATBUFFCHANGE, 1), P(STATDOWN_END))
    emit(B(SB_GOTO), P(STATDOWN_END))
    assert len(out) == 34 + 5
    return bytes(out)

def apply(r):
    b = r.b
    L = MT.live(b)
    assert struct.unpack('<I', b[0x40238:0x4023c])[0] == OLD_N and struct.unpack('<I', b[0x933e8:0x933ec])[0] == OLD_N, 'sentinels'
    # 1. the effect script, then the effect table entry
    base = r.cur = (r.cur + 3) & ~3
    script = script_bytes(0x08000000 + base)
    a = r.alloc(script, 4); assert a == base
    eff_slot = EFFECT_TABLE - 0x08000000 + 4 * EFFECT
    assert struct.unpack_from('<I', b, eff_slot)[0] != 0x08000000 + a
    # (the slot must be unused: no move in the ROM has effect 14 before this stage)
    assert all(b[L['md'] + 12 * m] != EFFECT for m in range(OLD_N)), 'effect 14 is in use'
    r.w32(eff_slot, 0x08000000 + a)
    # 2. move data: Earthquake's record, changed to a 5 PP status move
    rec = bytearray(b[L['md'] + 12 * EARTHQUAKE:L['md'] + 12 * EARTHQUAKE + 12])
    rec[0] = EFFECT; rec[1] = 0; rec[2] = TYPE_GROUND; rec[3] = 100; rec[4] = 5; rec[5] = 0
    md_new = r.alloc(bytes(b[L['md']:L['md'] + 12 * OLD_N]) + bytes(rec), 4)
    # 3. names (13 bytes)
    names = bytes(b[L['mn']:L['mn'] + 13 * OLD_N])
    n = SA.text('UNSTABLE'); assert len(n) <= 13
    names += n + b'\xff' * (13 - len(n))
    mn_new = r.alloc(names, 4)
    # 4. description
    descs = bytes(b[L['mdesc']:L['mdesc'] + 4 * (OLD_N - 1)])
    descs += struct.pack('<I', 0x08000000 + r.alloc(SA.text('Sharply lowers the accuracy\nand evasion of all non-GROUND.'), 1))
    mdesc_new = r.alloc(descs, 4)
    # 5. battle animation: Earthquake's
    anims = bytes(b[L['anim']:L['anim'] + 4 * OLD_N])
    anims += anims[4 * EARTHQUAKE:4 * EARTHQUAKE + 4]
    anim_new = r.alloc(anims, 4)
    # 6. repoint the references (pp field included), sentinels, battle text limit
    ME.repoint(b, L['md'] + 4, md_new + 4)
    counts = (ME.repoint(b, L['md'], md_new), ME.repoint(b, L['mn'], mn_new),
              ME.repoint(b, L['mdesc'], mdesc_new), ME.repoint(b, L['anim'], anim_new))
    assert all(c > 0 for c in counts), counts
    for o in ME.SENTINEL_SITES: r.w32(o, NEW_N)
    for o, br in ((0xd75fc, 0xd3), (0xd7e96, 0xd2), (0xd7eae, 0xd3)):
        assert b[o] == 0xb4 and b[o + 1] == 0x20 and b[o + 2] == 0x40 and b[o + 3] == 0x00 and b[o + 4:o + 6] == b'\x81\x42', hex(o)
        assert b[o + 7] == br, hex(o)
        b[o] = 0xb5
    # 7. Sandshrew learns it at 8
    p = struct.unpack_from('<I', b, LEARN + 4 * SANDSHREW)[0] - 0x08000000
    moves = []
    while True:
        v = struct.unpack_from('<H', b, p)[0]; p += 2
        if v == 0xffff: break
        moves.append((v >> 9, v & 0x1ff))
    moves.append((8, NEW_MOVE)); moves.sort(key=lambda t: t[0])
    data = b''.join(struct.pack('<H', (l << 9) | m) for l, m in moves) + b'\xff\xff'
    r.w32(LEARN + 4 * SANDSHREW, 0x08000000 + r.alloc(data, 2))
    print('unstable_ground: move %d, effect %d script %s, tables %s, Sandshrew learns it at 8' % (NEW_MOVE, EFFECT, hex(0x08000000 + a), [hex(x) for x in (md_new, mn_new, mdesc_new, anim_new)]))

if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')

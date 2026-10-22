"""UNSTABLE (move 359): show the animation, play the sound and say what it does (usage: unstable_effects.py IN.gba OUT.gba). Owner request.
The effect script from unstable_ground.py had no attackanimation, so nothing played even though Earthquake's animation entry was copied for the move.
New script: attackcanceler, attackstring, ppreduce, [first target only: "The ground became unstable!"], attackanimation, waitanimation (Earthquake's
visual and sound), skip GROUND targets, accuracy -2, evasion -2 (same as before). The message is a new battle string: the strings table (355 entries, string id =
index + 12) is copied with one more entry and every reference is repointed. The message is printed only while animTargetsHit is 0 so a double battle says it once.
Runs after unstable_ground.py."""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from inc import Rom
import species_add as SA
import moves_extend as ME
EFFECT = 14; EFFECT_TABLE = 0x081d65a8; STRINGS = 0x3fdf3c; N_STRINGS = 355; ID_ADDER = 12
STATCHANGER = 0x02023fde; ANIM_TARGETS_HIT = 0x02023fdd; STATDOWN_END = 0x081d6c5d
TYPE_GROUND = 4; STAT_ACC, STAT_EVA = 6, 7
def stat_down(stat, stages): return stat | (stages << 4) | 0x80
MESSAGE = 'The ground became\nunstable!'
MULTI = 0x02023e87           # gBattleCommunication + 5, the string chooser the stat-change command sets
STAT_DOWN_STRINGS = 0x083fe588; ANIM_ARG1 = 0x02023fd4
def script_bytes(base, msg_id):
    P = lambda a: struct.pack('<I', a)
    parts = []; labels = {}
    def emit(b): parts.append(('b', b))
    def lab(n): labels[n] = sum(len(x[1]) if x[0] == 'b' else 4 for x in parts)
    def ref(n): parts.append(('r', n))
    def stat_block(nxt):
        # the vanilla BattleScript_EffectStatDown tail, with our own jump targets (it ends in goto MoveEnd, which we cannot reuse for the second stat)
        emit(bytes([0x89, 1])); ref(nxt)                                              # statbuffchange, on failure go on
        emit(bytes([0x29, 3]) + P(MULTI) + bytes([2])); ref('anim_%s' % nxt)          # chooser > 2: do the stat animation
        emit(bytes([0x29, 0]) + P(MULTI) + bytes([3])); ref(nxt)                      # chooser == 3: nothing to show
        emit(bytes([0x39, 0x20, 0x00])); emit(bytes([0x28])); ref('print_%s' % nxt)   # pause, print
        lab('anim_%s' % nxt); emit(bytes([0x47, 0x45, 0x00, 0x01]) + P(ANIM_ARG1))    # setgraphicalstatchangevalues, playanimation STATS_CHANGE
        lab('print_%s' % nxt); emit(bytes([0x13]) + P(STAT_DOWN_STRINGS) + bytes([0x12]) + struct.pack('<H', 0x40))   # printfromtable, waitmessage
    emit(bytes([0x00, 0x02, 0x03]))                          # attackcanceler, attackstring, ppreduce
    emit(bytes([0x29, 1]) + P(ANIM_TARGETS_HIT) + bytes([0])); ref('anim')      # jumpifbyte NOT_EQUAL animTargetsHit 0 -> anim (message once)
    emit(bytes([0x10]) + struct.pack('<H', msg_id) + bytes([0x12]) + struct.pack('<H', 0x40))   # printstring, waitmessage
    lab('anim'); emit(bytes([0x09, 0x0a]))                   # attackanimation, waitanimation (Earthquake's visual and sound)
    emit(bytes([0x22, 0, TYPE_GROUND])); ref('end')          # jumpiftype target GROUND -> end
    emit(bytes([0x2e]) + P(STATCHANGER) + bytes([stat_down(STAT_ACC, 2)]))
    stat_block('eva')
    lab('eva'); emit(bytes([0x2e]) + P(STATCHANGER) + bytes([stat_down(STAT_EVA, 2)]))
    stat_block('end')
    lab('end'); emit(bytes([0x28])); parts.append(('a', STATDOWN_END))   # goto BattleScript_MoveEnd
    out = bytearray()
    for k, v in parts:
        if k == 'b': out += v
        elif k == 'a': out += P(v)
        else: out += P(base + labels[v])
    return bytes(out)
def apply(r):
    b = r.b
    # 1. battle string: copy the strings table with one more entry, repoint the code
    old_tab = [struct.unpack_from('<I', b, STRINGS + 4 * i)[0] for i in range(N_STRINGS)]
    assert all(0x08300000 <= v < 0x08500000 for v in old_tab) and not (0x08300000 <= struct.unpack_from('<I', b, STRINGS + 4 * N_STRINGS)[0] < 0x08500000), 'strings table size changed'
    text = SA.text(MESSAGE)
    t_a = r.alloc(text, 1)
    tab_a = r.alloc(b''.join(struct.pack('<I', v) for v in old_tab) + struct.pack('<I', 0x08000000 + t_a), 4)
    n = ME.repoint(b, STRINGS, tab_a); assert n >= 20, 'strings table references: %d' % n
    msg_id = ID_ADDER + N_STRINGS
    # 2. effect script
    slot = EFFECT_TABLE - 0x08000000 + 4 * EFFECT
    old = struct.unpack_from('<I', b, slot)[0] - 0x08000000
    assert bytes(b[old:old + 3]) == bytes([0x00, 0x02, 0x03]) and b[old + 3] == 0x22, 'effect 14 is not the unstable_ground.py script'
    r.cur = (r.cur + 3) & ~3; base = r.cur
    a = r.alloc(script_bytes(0x08000000 + base, msg_id), 4); assert a == base
    r.w32(slot, 0x08000000 + a)
    print('unstable_effects: string id %d (table %s, %d refs), effect 14 script %s' % (msg_id, hex(0x08000000 + tab_a), n, hex(0x08000000 + a)))
if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')

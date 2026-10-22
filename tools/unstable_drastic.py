"""UNSTABLE (move 359) v2: drastically lowers the foe's accuracy and drastically raises the user's own (usage: unstable_drastic.py IN.gba OUT.gba). Owner request.
Replaces the effect script from unstable_effects.py (evasion -2 / accuracy -2 on the foe). Now: "The ground became unstable!", then the USER's accuracy +3
(first target only, so a double battle raises it once), Earthquake's animation and sound, then the FOE's accuracy -3 (GROUND-type targets skipped as before).
"Drastically" is 3 stages. This ROM (Gen 3) has no wording for 3 stages (it printed plain "rose!" and "fell!"), so two new battle strings say
"SANDSHREW's accuracy drastically rose!" and "Wild RATTATA's accuracy drastically fell!" (the strings table is copied again with two more entries).
The move description is rewritten too. Runs after unstable_effects.py."""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from inc import Rom
from g3 import ENC
import moves_extend as ME
import species_add as SA
import move_tables as MT
import unstable_effects as UE
STAT_UP_STRINGS = 0x083fe57c
STAGES = 3
def stat_up(stat, stages): return stat | (stages << 4)
def script_bytes(base, msg_id, up_id, down_id):
    P = lambda a: struct.pack('<I', a)
    parts = []; labels = {}
    def emit(b): parts.append(('b', b))
    def lab(n): labels[n] = sum(len(x[1]) if x[0] == 'b' else 4 for x in parts)
    def ref(n): parts.append(('r', n))
    def down_block(nxt):                                       # the vanilla stat-down tail, with a custom line for a normal change
        emit(bytes([0x89, 1])); ref(nxt)
        emit(bytes([0x29, 3]) + P(UE.MULTI) + bytes([2])); ref('danim')               # chooser < 2: a normal change
        emit(bytes([0x29, 0]) + P(UE.MULTI) + bytes([3])); ref(nxt)
        emit(bytes([0x39, 0x20, 0x00])); emit(bytes([0x28])); ref('dtab')             # limit or protection: the game's own line
        lab('danim'); emit(bytes([0x47, 0x45, 0x00, 0x01]) + P(UE.ANIM_ARG1))
        emit(bytes([0x10]) + struct.pack('<H', down_id) + bytes([0x12]) + struct.pack('<H', 0x40)); emit(bytes([0x28])); ref(nxt)
        lab('dtab'); emit(bytes([0x13]) + P(UE.STAT_DOWN_STRINGS) + bytes([0x12]) + struct.pack('<H', 0x40))
    def up_block(nxt):                                         # the vanilla stat-up tail: flags 0x41 = applies to the user
        emit(bytes([0x89, 0x41])); ref(nxt)
        emit(bytes([0x29, 1]) + P(UE.MULTI) + bytes([2])); ref('uanim')               # chooser != 2: a normal change
        emit(bytes([0x39, 0x20, 0x00])); emit(bytes([0x28])); ref('utab')
        lab('uanim'); emit(bytes([0x47, 0x45, 0x01, 0x01]) + P(UE.ANIM_ARG1))
        emit(bytes([0x10]) + struct.pack('<H', up_id) + bytes([0x12]) + struct.pack('<H', 0x40)); emit(bytes([0x28])); ref(nxt)
        lab('utab'); emit(bytes([0x13]) + P(STAT_UP_STRINGS) + bytes([0x12]) + struct.pack('<H', 0x40))
    emit(bytes([0x00, 0x02, 0x03]))                            # attackcanceler, attackstring, ppreduce
    emit(bytes([0x29, 1]) + P(UE.ANIM_TARGETS_HIT) + bytes([0])); ref('anim')      # not the first target: skip the message and the user's boost
    emit(bytes([0x10]) + struct.pack('<H', msg_id) + bytes([0x12]) + struct.pack('<H', 0x40))
    emit(bytes([0x2e]) + P(UE.STATCHANGER) + bytes([stat_up(UE.STAT_ACC, STAGES)]))
    up_block('anim')
    lab('anim'); emit(bytes([0x09, 0x0a]))                     # attackanimation, waitanimation
    emit(bytes([0x22, 0, UE.TYPE_GROUND])); ref('end')
    emit(bytes([0x2e]) + P(UE.STATCHANGER) + bytes([UE.stat_down(UE.STAT_ACC, STAGES)]))
    down_block('end')
    lab('end'); emit(bytes([0x28])); parts.append(('a', UE.STATDOWN_END))
    out = bytearray()
    for k, v in parts:
        if k == 'b': out += v
        elif k == 'a': out += P(v)
        else: out += P(base + labels[v])
    return bytes(out)
def apply(r):
    b = r.b
    slot = UE.EFFECT_TABLE - 0x08000000 + 4 * UE.EFFECT
    old = struct.unpack_from('<I', b, slot)[0] - 0x08000000
    assert bytes(b[old:old + 3]) == bytes([0x00, 0x02, 0x03]) and b[old + 3] == 0x29, 'effect 14 is not the unstable_effects.py script'
    # two more battle strings: find the current table (356 entries, the last one is "The ground became unstable!"), copy it with 2 more, repoint the code
    ground = bytes(ENC[c] for c in 'The ground became')
    cur = None
    for o in range(0xA00000, len(b) - 4 * 356, 4):
        last = struct.unpack_from('<I', b, o + 4 * 355)[0] - 0x08000000
        if 0 <= last < len(b) - 20 and bytes(b[last:last + len(ground)]) == ground and all(0x08000000 <= struct.unpack_from('<I', b, o + 4 * i)[0] < 0x0a000000 for i in (0, 100, 354)):
            cur = o; break
    assert cur is not None, 'strings table with the Unstable message not found'
    entries = [struct.unpack_from('<I', b, cur + 4 * i)[0] for i in range(356)]
    mk = lambda who, word: bytes([0xfd, who, 0xb4, 0xe7, 0x00, 0xfd, 0x00, 0xfe]) + bytes(ENC[c] for c in word) + b'\xff'
    up_a = r.alloc(mk(0x0f, 'drastically rose!'), 1); down_a = r.alloc(mk(0x10, 'drastically fell!'), 1)
    tab = r.alloc(b''.join(struct.pack('<I', v) for v in entries) + struct.pack('<I', 0x08000000 + up_a) + struct.pack('<I', 0x08000000 + down_a), 4)
    n = ME.repoint(b, cur, tab); assert n >= 20, 'strings table references: %d' % n
    msg_id = UE.ID_ADDER + UE.N_STRINGS; up_id = msg_id + 1; down_id = msg_id + 2
    r.cur = (r.cur + 3) & ~3; base = r.cur
    a = r.alloc(script_bytes(0x08000000 + base, msg_id, up_id, down_id), 4); assert a == base
    r.w32(slot, 0x08000000 + a)
    L = MT.live(b)
    d_a = r.alloc(SA.text("Drastically lowers\nthe foe's accuracy\nand raises your own."), 1)
    r.w32(L['mdesc'] + 4 * (UE.NEW_MOVE - 1) if hasattr(UE, 'NEW_MOVE') else L['mdesc'] + 4 * 358, 0x08000000 + d_a)
    print('unstable_drastic: effect 14 script %s, description rewritten' % hex(0x08000000 + a))
if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')

"""UNSTABLE fix: ensure Earthquake plays first, then message, then debuff text+anim, then buff text+anim.
Accuracy table is already correct (80/60/40/30/20/10).
This rewrites the effect script to force the texts and animations after applying the stages.
"""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from inc import Rom
import unstable_effects as UE
import unstable_drastic as UD
FIRST = 0x020370D6
STAGES = 3
def script_bytes(base, msg_id, up_id, down_id):
    P = lambda a: struct.pack('<I', a)
    W = lambda v: struct.pack('<H', v)
    parts = []; labels = {}
    def emit(b): parts.append(('b', b))
    def lab(n): labels[n] = sum(len(x[1]) if x[0] == 'b' else 4 for x in parts)
    def ref(n): parts.append(('r', n))
    def text(sid): emit(bytes([0x10]) + W(sid) + bytes([0x12]) + W(0x40))
    emit(bytes([0x00, 0x02, 0x03]))  # attackcanceler attackstring ppreduce
    emit(bytes([0x29, 1]) + P(UE.ANIM_TARGETS_HIT) + bytes([0])); ref('notfirst')
    emit(bytes([0x2e]) + P(FIRST) + bytes([1])); ref('go')
    lab('notfirst'); emit(bytes([0x2e]) + P(FIRST) + bytes([0]))
    lab('go'); emit(bytes([0x09, 0x0a]))  # Earthquake anim + sound FIRST
    emit(bytes([0x29, 1]) + P(FIRST) + bytes([1])); ref('skipmsg'); text(msg_id)
    lab('skipmsg'); emit(bytes([0x22, 0, UE.TYPE_GROUND])); ref('buff')  # skip ground
    # Debuff foe accuracy -3
    emit(bytes([0x2e]) + P(UE.STATCHANGER) + bytes([UE.stat_down(UE.STAT_ACC, STAGES)]))
    emit(bytes([0x89, 1])); ref('buff')  # statbuffchange, fail -> buff
    text(down_id)  # always print the lowered text if we got here
    emit(bytes([0x47, 0x45, 0x00, 0x01]) + P(UE.ANIM_ARG1)); emit(bytes([0x0a]))  # anim + wait
    # Buff user +3
    lab('buff'); emit(bytes([0x29, 1]) + P(FIRST) + bytes([1])); ref('end')
    emit(bytes([0x2e]) + P(UE.STATCHANGER) + bytes([UD.stat_up(UE.STAT_ACC, STAGES)]))
    emit(bytes([0x89, 0x41])); ref('end')
    text(up_id)
    emit(bytes([0x47, 0x45, 0x01, 0x01]) + P(UE.ANIM_ARG1)); emit(bytes([0x0a]))
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
    assert bytes(b[old:old + 3]) == bytes([0x00, 0x02, 0x03]), 'effect 14 script missing start'
    msg_id = UE.ID_ADDER + UE.N_STRINGS
    r.cur = (r.cur + 3) & ~3; base = r.cur
    a = r.alloc(script_bytes(0x08000000 + base, msg_id, msg_id + 1, msg_id + 2), 4); assert a == base
    r.w32(slot, 0x08000000 + a)
    print('unstable_fix: effect 14 script %s' % hex(0x08000000 + a))
if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')

"""UNSTABLE (move 359) v3: message order (usage: unstable_order.py IN.gba OUT.gba). Owner request. Runs after unstable_drastic.py.
New order: Earthquake's animation and sound, "The ground became unstable!", then the FOE's line ("Wild RATTATA's accuracy drastically fell!") and the
debuff animation, then the USER's line ("SANDSHREW's accuracy drastically rose!") and the buff animation. Text first, then its animation.
The foe's accuracy -3 (GROUND targets skipped) and the user's accuracy +3 are unchanged. In a double battle the message and the user's boost still happen once:
the first-target test (animTargetsHit == 0, true only before the move's animation has played) is stored in script scratch word 0x800F before the animation."""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from inc import Rom
import unstable_effects as UE
import unstable_drastic as UD
FIRST = 0x020370D6          # script scratch word 0x800F: 1 on the first target of this use, 0 on the others
STAGES = 3
def script_bytes(base, msg_id, up_id, down_id):
    P = lambda a: struct.pack('<I', a)
    W = lambda v: struct.pack('<H', v)
    parts = []; labels = {}
    def emit(b): parts.append(('b', b))
    def lab(n): labels[n] = sum(len(x[1]) if x[0] == 'b' else 4 for x in parts)
    def ref(n): parts.append(('r', n))
    def text(sid): emit(bytes([0x10]) + W(sid) + bytes([0x12]) + W(0x40))              # printstring, waitmessage
    def table(addr): emit(bytes([0x13]) + P(addr) + bytes([0x12]) + W(0x40))          # printfromtable, waitmessage
    def jump(n): emit(bytes([0x28])); ref(n)
    emit(bytes([0x00, 0x02, 0x03]))                                                    # attackcanceler, attackstring, ppreduce
    emit(bytes([0x29, 1]) + P(UE.ANIM_TARGETS_HIT) + bytes([0])); ref('notfirst')    # first target? (animTargetsHit == 0 before the animation)
    emit(bytes([0x2e]) + P(FIRST) + bytes([1])); jump('go')
    lab('notfirst'); emit(bytes([0x2e]) + P(FIRST) + bytes([0]))
    lab('go'); emit(bytes([0x09, 0x0a]))                                               # 1. Earthquake's animation and sound
    emit(bytes([0x29, 1]) + P(FIRST) + bytes([1])); ref('skipmsg'); text(msg_id)       # 2. "The ground became unstable!" (first target only)
    lab('skipmsg'); emit(bytes([0x22, 0, UE.TYPE_GROUND])); ref('buff')                # GROUND targets: no debuff
    # 3. the foe: accuracy -3 (text, then the debuff animation)
    emit(bytes([0x2e]) + P(UE.STATCHANGER) + bytes([UE.stat_down(UE.STAT_ACC, STAGES)]))
    emit(bytes([0x89, 1])); ref('buff')                                                # statbuffchange, on failure go on
    emit(bytes([0x29, 3]) + P(UE.MULTI) + bytes([2])); ref('dnorm')                    # chooser < 2: a normal change
    emit(bytes([0x29, 0]) + P(UE.MULTI) + bytes([3])); ref('buff')
    emit(bytes([0x39, 0x20, 0x00])); table(UE.STAT_DOWN_STRINGS); jump('buff')         # limit: the game's own line
    lab('dnorm'); text(down_id)
    emit(bytes([0x47, 0x45, 0x00, 0x01]) + P(UE.ANIM_ARG1)); emit(bytes([0x0a]))       # setgraphicalstatchangevalues, playanimation, waitanimation
    # 4. the user: accuracy +3 (first target only)
    lab('buff'); emit(bytes([0x29, 1]) + P(FIRST) + bytes([1])); ref('end')
    emit(bytes([0x2e]) + P(UE.STATCHANGER) + bytes([UD.stat_up(UE.STAT_ACC, STAGES)]))
    emit(bytes([0x89, 0x41])); ref('end')
    emit(bytes([0x29, 1]) + P(UE.MULTI) + bytes([2])); ref('unorm')                    # chooser != 2: a normal change
    emit(bytes([0x39, 0x20, 0x00])); table(UD.STAT_UP_STRINGS); jump('end')            # limit: "won't go higher"
    lab('unorm'); text(up_id)
    emit(bytes([0x47, 0x45, 0x01, 0x01]) + P(UE.ANIM_ARG1)); emit(bytes([0x0a]))
    lab('end'); emit(bytes([0x28])); parts.append(('a', UE.STATDOWN_END))              # goto BattleScript_MoveEnd
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
    assert bytes(b[old:old + 3]) == bytes([0x00, 0x02, 0x03]) and b[old + 3] == 0x29 and b[old + 4] == 1, 'effect 14 is not the unstable_drastic.py script'
    msg_id = UE.ID_ADDER + UE.N_STRINGS
    r.cur = (r.cur + 3) & ~3; base = r.cur
    a = r.alloc(script_bytes(0x08000000 + base, msg_id, msg_id + 1, msg_id + 2), 4); assert a == base
    r.w32(slot, 0x08000000 + a)
    print('unstable_order: effect 14 script %s' % hex(0x08000000 + a))
if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')

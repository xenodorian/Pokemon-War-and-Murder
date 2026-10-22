"""Stand-in death rule (usage: standin_death.py IN.gba OUT.gba). Source: story/standin_native.c. Runs after rebase_natives.py and death_fade.py.
Owner rule: in a playable run, if the player is in the party as a playable POKeMON when all POKeMON faint, she dies and goes to HEAVEN or HELL;
if she is not in the party, the normal POKeMON CENTER respawn. The white-out script's LEAF-down check only counted a fainted real LEAF.
- the battle-start hook now calls prepare_note (old max_prepare, then notes a stand-in LEAF in a playable run in script scratch word 0x800A). The battle-end
  callback deletes the stand-in before the white-out script runs, which is why she has to be noted at battle start.
- the white-out script's LEAF-down check is leaf_down_standin: real LEAF fainted, or the noted stand-in."""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from inc import Rom
import rebase_natives as RN
import death_fade
from death_fade import compile_one
def bl_target(b, at):
    hi, lo = struct.unpack_from('<HH', b, at)
    assert hi & 0xF800 == 0xF000 and lo & 0xF800 == 0xF800
    off = ((hi & 0x7FF) << 12) | ((lo & 0x7FF) << 1)
    if off & 0x400000: off -= 0x800000
    return at + 4 + off
def apply(r):
    b = r.b
    fns = RN.addrs(r)
    sc = struct.unpack_from('<I', b, RN.WHITEOUT_PTR)[0] - 0x08000000
    assert b[sc + 16] == 0x23 and b[sc + 21:sc + 26] == bytes([0x21, 0x07, 0x80, 0x01, 0x00]), 'white-out script layout not recognised'
    old_leaf = struct.unpack_from('<I', b, sc + 17)[0]
    assert bytes(b[(old_leaf & ~1) - 0x08000000:(old_leaf & ~1) - 0x08000000 + 2]) == bytes([0xf0, 0xb5]), 'old LEAF-down native not found'
    p2 = (struct.unpack_from('<I', b, RN.BATTLE_SITE_TRAMP + 4)[0] & ~1) - 0x08000000
    assert bl_target(b, p2 + 2) == (fns['max_prepare_wrap'] & ~1) - 0x08000000, 'battle-start hook is not the rebase_natives one'
    i = bytes(b).find(b'STORYFN1', 0xA00000); old_mp = struct.unpack_from('<I', b, i + 16)[0]
    open(os.path.join(death_fade.SRC, 'standin_gen.h'), 'w').write('#define OLD_MAX_PREPARE (0x%08x)\n' % old_mp)
    pn = compile_one(r, 'standin_native.c', 'prepare_note')
    ld = compile_one(r, 'standin_native.c', 'leaf_down_standin')
    r.bl(p2 + 2, (pn & ~1) - 0x08000000)
    r.w32(sc + 17, ld)
    print('standin_death: battle-start hook -> %s, white-out check %s -> %s' % (hex(pn), hex(old_leaf), hex(ld)))
if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')

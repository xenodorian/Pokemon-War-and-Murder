"""Fix the killer class on death (usage: death_class_fix.py IN.gba OUT.gba). Source: story/death_class_native.c. Runs after death_fade.py.
A JRA soldier, captain or general kill must play the gunshot and skip the "mauled" line. The class saved at battle start was always 0 for trainer
battles, so every death was "mauled" with the attacker's cry. death_fx now jumps to death_fx_live, which reads the class when the death happens."""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from inc import Rom
import rebase_natives as RN
from death_fade import compile_one
def apply(r):
    old = RN.addrs(r)['death_fx'] & ~1; o = old - 0x08000000
    assert old % 4 == 0, 'death_fx is not 4-aligned'
    new = compile_one(r, 'death_class_native.c', 'death_fx_live')
    assert bytes(r.b[o:o + 2]) != bytes([0x00, 0x4b]), 'already patched'
    r.b[o:o + 8] = bytes([0x00, 0x4b, 0x18, 0x47]) + struct.pack('<I', new)     # ldr r3,[pc,#0]; bx r3; .word new
    print('death_class_fix: death_fx %s now jumps to %s' % (hex(old), hex(new)))
if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')

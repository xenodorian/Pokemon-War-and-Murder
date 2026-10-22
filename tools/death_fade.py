"""Fix the death scene (usage: death_fade.py IN.gba OUT.gba). Source: story/death_fade_native.c.
 - The red fade never showed: death_fx asks for it while the fade from the lost battle is still running, and the game refuses.
   The new death script retries (native death_fade_try, VAR_RESULT = started) every 2 frames until it starts, then holds 40 frames.
 - "You were mauled to death by a pokemon." was cut off at the right edge of the box. It now breaks after "death".
Runs after rebase_natives.py. Replaces the death script that rebase_natives wrote; the references to it are repointed."""
import sys, os, struct, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from inc import Rom
from cry_open import SB, put_script, enc
import rebase_natives as RN

WORK = '/tmp/death_fade_build'; SRC = os.path.join(HERE, '..', 'story')
def compile_one(r, src, name):
    os.makedirs(WORK, exist_ok=True)
    r.cur = (r.cur + 3) & ~3; base = 0x08000000 + r.cur
    ld = os.path.join(WORK, 'x.ld'); o = os.path.join(WORK, 'x.o'); e = os.path.join(WORK, 'x.elf'); bn = os.path.join(WORK, 'x.bin')
    open(ld, 'w').write('ENTRY(%s)\nSECTIONS { . = 0x%08x; .all : { *(.text*) *(.rodata*) *(.data*) } /DISCARD/ : { *(.ARM.exidx*) *(.comment) *(.note*) *(.ARM.attributes) } }\n' % (name, base))
    subprocess.run(['clang', '--target=thumbv4t-none-eabi', '-mthumb', '-Os', '-ffreestanding', '-fno-builtin', '-fno-pic', '-fno-stack-protector', '-nostdlib',
                    '-fno-unwind-tables', '-fno-asynchronous-unwind-tables', '-c', os.path.join(SRC, src), '-o', o], check=True)
    subprocess.run(['ld.lld', '-T', ld, o, '-o', e], check=True)
    subprocess.run(['llvm-objcopy', '-O', 'binary', e, bn], check=True)
    a = r.alloc(open(bn, 'rb').read(), 4); assert 0x08000000 + a == base
    for ln in subprocess.run(['nm', e], capture_output=True, text=True, check=True).stdout.split('\n'):
        f = ln.split()
        if len(f) == 3 and f[2] == name: return (int(f[0], 16) & ~1) | 1
    raise AssertionError('symbol missing')

def apply(r):
    b = r.b
    fns = RN.addrs(r)
    sc = struct.unpack_from('<I', b, RN.WHITEOUT_PTR)[0] - 0x08000000
    goto_center = bytes([0x05]) + struct.pack('<I', RN.CENTER_SCRIPT)
    k = bytes(b[sc:sc + 600]).find(goto_center); assert k > 0 and b[sc + k + 5] == 0x05
    cur = struct.unpack_from('<I', b, sc + k + 6)[0]; cs = cur - 0x08000000
    # the script rebase_natives wrote: lockall, callnative death_fx, cmp 0x800c 1, goto_if 1 'm', 'go': delay 40, goto old_death
    assert b[cs] == 0x69 and b[cs + 1] == 0x23 and struct.unpack_from('<I', b, cs + 2)[0] == fns['death_fx'], 'death script not the rebase_natives one'
    assert b[cs + 17] == 0x28 and b[cs + 20] == 0x05, 'unexpected death script layout'
    old_death = struct.unpack_from('<I', b, cs + 21)[0]
    assert 0x08000000 <= old_death < 0x09000000 and old_death != cur
    fade = compile_one(r, 'death_fade_native.c', 'death_fade_try')
    mauled = 0x08000000 + r.alloc(enc('You were mauled to death\nby a pokemon.'), 1)
    D = SB(); D.lockall(); D.raw(0x23); D.ptr(fns['death_fx'])
    D.lab('try'); D.raw(0x23); D.ptr(fade); D.cmp(0x800D, 1); D.goto_if(1, 'ok'); D.raw(0x28, 2, 0); D.goto('try')
    D.lab('ok'); D.raw(0x28, 40, 0)
    D.cmp(0x800c, 1); D.goto_if(1, 'm')
    D.lab('go'); D.raw(0x05); D.ptr(old_death)
    D.lab('m'); D.msg(mauled); D.goto('go')
    new = 0x08000000 + put_script(r, D)
    pat = struct.pack('<I', cur); n = 0; pos = 0
    while True:
        pos = bytes(b).find(pat, pos)
        if pos < 0: break
        if not (new - 0x08000000 <= pos < new - 0x08000000 + 128):
            r.w32(pos, new); n += 1
        pos += 1
    assert n >= 1
    print('death_fade: native %s, death script %s -> %s (%d references)' % (hex(fade), hex(cur), hex(new), n))
if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')

"""Start menu fix (usage: start_menu_fix.py IN.gba OUT.gba). Runs after start_controls.py.
start_controls.py called the menu add-action function from the new tail with Thumb-2 wide bl instructions (out of the 4 MB range of a Thumb-1 bl).
The GBA CPU cannot run those, so the menu stopped building after POKEMON. It also hooked a function the main loop does not use, waited for keys
in a native loop that never lets a frame pass, and kept the report in a RAM buffer nothing saves.
Here the tail, the two callbacks and the fade exemption list use the Thumb-1 call pattern of the KARMA entry (ldr r1,=target / bl thunk that is bx r1).
REPORT: hands off, then press A, then press B. The key hook samples the raw key register every frame (and what the game would see after the remap),
and the text report goes to flash sector 31 (the unused Trainer Tower sector) as PWAMRPT, which the GitROMs launcher lifts out of the .srm.
REMAP: two prompts read the raw key register; the chosen key masks are kept in two saved script variables; the key hook that ReadKeys already
calls (0x08175228) swaps the A and B bits with those keys."""
import sys, struct
sys.path.insert(0, 'tools')
from inc import Rom
from cry_open import SB, put_script, enc

THUNK1 = 0xECEB20     # bx r1
THUNK2 = 0xECEB24     # bx r2
TBL = 0xFF3450        # action table, 14 entries of (name ptr, callback ptr)
DESC = 0xFF34C0       # description pointer table
SEND, REG = 12, 13
HOOK = 0x175228       # key hook called by ReadKeys (0x080005E8)
WRITE_SECTOR = 0x080DA5E1   # u8 WriteTrainerTowerSector(u8 sector, const void *src): copies 0xFFC bytes, returns 1 on success
SECTOR = 31
BUF = 0x02039A3C      # save scratch buffer + 4; the routine copies from here onto itself, so the report is written here
V4, V5, V6, VR = 0x020370C0, 0x020370C2, 0x020370C4, 0x020370D2   # script scratch variables 0x8004, 0x8005, 0x8006, 0x800D
VAR_A, VAR_B = 0x40C4, 0x40DC          # saved script variables holding the registered key masks: unnamed in ref/vars.h, no script op, coord event or literal in the ROM touches them
VARS_OFF = 0x1000                      # offset of the script variable array inside the save block 1


def call(addr):
    return 'ldr r1,=%d\nbl %d\n' % (addr | 1, 0x08000000 + THUNK1)


def thumb1_check(code, base, what):
    """Reject anything the ARM7TDMI cannot run: Thumb-2 wide instructions, a bl whose second half is not a bl suffix, hint and ARMv6 ops."""
    n = len(code) // 2
    h = [struct.unpack('<H', code[2 * i:2 * i + 2])[0] for i in range(n)]
    data = set()
    for i in range(n):
        if h[i] & 0xF800 == 0x4800:
            w = ((base + 2 * i + 4) & ~3) + (h[i] & 0xFF) * 4 - base
            data.update((w // 2, w // 2 + 1))
    i = 0
    while i < n:
        if i in data:
            i += 1; continue
        x = h[i]
        if x & 0xF800 == 0xF000:
            assert i + 1 < n and h[i + 1] & 0xF800 == 0xF800, '%s: wide instruction %04x %04x at +%#x' % (what, x, h[i + 1] if i + 1 < n else 0, 2 * i)
            i += 2; continue
        assert x & 0xF800 not in (0xE800, 0xF800), '%s: wide instruction %04x at +%#x' % (what, x, 2 * i)
        if x == 0xBF00 and i and (h[i - 1] & 0xFF00 == 0x4700 or h[i - 1] & 0xFF00 == 0xBD00 or h[i - 1] & 0xF800 == 0xE000):
            i += 1; continue              # alignment padding the assembler puts after a return, before the literal pool; never executed
        assert not (0xBF00 <= x <= 0xBFFF or 0xB200 <= x <= 0xB2FF or 0xBA00 <= x <= 0xBAFF or 0xB600 <= x <= 0xB6FF), '%s: non-ARMv4T op %04x at +%#x' % (what, x, 2 * i)
        i += 1


def fn(r, src, what):
    code = r.asm(src, (r.cur + 3) & ~3)
    thumb1_check(code, (r.cur + 3) & ~3, what)
    return r.fn(src)


def callback(r, script, what):
    # same shape as the KARMA callback: close the menu, then run the script
    return fn(r, 'push {lr}\n' + call(0x0806EF18) + call(0x080F7998) + call(0x0806FEA0) +
              'ldr r0,=%d\n' % (0x08000000 + script) + call(0x08069AE4) + 'movs r0,#1\npop {r1}\nbx r1\n.ltorg\n', what)


SRC = 'story/start_native.c'
WORK = '/tmp/start_menu_build'


def compile_natives(r, names):
    """Compile story/start_native.c at the end of the ROM and return {name: thumb address}."""
    import os, subprocess
    os.makedirs(WORK, exist_ok=True)
    r.cur = (r.cur + 3) & ~3; base = 0x08000000 + r.cur
    ld, o, e, bn = [os.path.join(WORK, x) for x in ('x.ld', 'x.o', 'x.elf', 'x.bin')]
    open(ld, 'w').write('ENTRY(%s)\nSECTIONS { . = 0x%08x; .all : { *(.text*) *(.rodata*) *(.data*) } /DISCARD/ : { *(.ARM.exidx*) *(.comment) *(.note*) *(.ARM.attributes) } }\n' % (names[0], base))
    subprocess.run(['clang', '--target=thumbv4t-none-eabi', '-mthumb', '-Os', '-ffreestanding', '-fno-builtin', '-fno-pic', '-fno-stack-protector', '-nostdlib',
                    '-fno-unwind-tables', '-fno-asynchronous-unwind-tables', '-DVARS_OFF=%#x' % VARS_OFF, '-DVAR_A=%#x' % VAR_A, '-DVAR_B=%#x' % VAR_B,
                    '-c', SRC, '-o', o], check=True)
    subprocess.run(['ld.lld', '-T', ld, o, '-o', e], check=True)
    subprocess.run(['llvm-objcopy', '-O', 'binary', e, bn], check=True)
    code = open(bn, 'rb').read()
    thumb1_check(code, base, 'start_native.c')
    a = r.alloc(code, 4); assert 0x08000000 + a == base
    out = {}
    for ln in subprocess.run(['nm', e], capture_output=True, text=True, check=True).stdout.split('\n'):
        f = ln.split()
        if len(f) == 3 and f[2] in names: out[f[2]] = (int(f[0], 16) & ~1) | 1
    assert len(out) == len(names), out
    return out


def build_scripts(r, nat):
    t = lambda s: 0x08000000 + r.alloc(enc(s), 1)
    def cn(S, name): S.raw(0x23); S.ptr(nat[name])
    def wait_release(S, lab):
        S.lab(lab); S.raw(0x28, 1, 0); cn(S, 'kn_now'); S.cmp(0x8004, 0); S.goto_if(5, lab)
    # REPORT: hands off, press A, press B, then flash the log. The key hook samples the raw key register every frame while 0x8009 = 0xC0DE.
    S = SB(); S.lockall(); S.setvar(0x8009, 0xC0DE); cn(S, 'kn_begin')
    def phase(S, start, lab):
        cn(S, start); S.lab(lab); S.raw(0x28, 1, 0); cn(S, 'kn_poll'); S.cmp(0x800D, 0); S.goto_if(1, lab)
    S.raw(0x67); S.ptr(t('Let go of every button.')); S.raw(0x66)
    phase(S, 'kn_settle', 'p0')
    S.raw(0x67); S.ptr(t('Do not touch the controller\nfor two seconds.')); S.raw(0x66)
    phase(S, 'kn_idle', 'p1'); cn(S, 'kn_idlefin')
    S.raw(0x67); S.ptr(t('Press and hold the A button\nfor one second, then let go.')); S.raw(0x66)
    phase(S, 'kn_rec', 'p2'); cn(S, 'kn_finA')
    S.raw(0x67); S.ptr(t('Now press and hold the B\nbutton for one second.')); S.raw(0x66)
    phase(S, 'kn_rec', 'p3'); cn(S, 'kn_finB')
    S.close(); S.setvar(0x8009, 0); cn(S, 'kn_write'); S.cmp(0x800D, 1); S.goto_if(1, 'ok')
    S.msg(t('The report could not be saved.'), 4); S.releaseall(); S.end()
    S.lab('ok'); S.msg(t('Controller report saved.\nGitROMs uploads it later.'), 4); S.releaseall(); S.end()
    report = put_script(r, S)
    # REMAP
    S = SB(); S.lockall(); S.setvar(0x8009, 0xC0DE)
    wait_release(S, 'r0')
    S.raw(0x67); S.ptr(t('Press the button that\nshould be A. Not B.')); S.raw(0x66)
    S.lab('pa'); S.raw(0x28, 1, 0); cn(S, 'kn_pickA'); S.cmp(0x8004, 0); S.goto_if(1, 'pa')
    S.raw(0x19, 0x05, 0x80, 0x04, 0x80); S.raw(0x19, VAR_A & 255, VAR_A >> 8, 0x04, 0x80)
    wait_release(S, 'r1')
    S.raw(0x67); S.ptr(t('Press the button that\nshould be B. Not A.')); S.raw(0x66)
    S.lab('pb'); S.raw(0x28, 1, 0); cn(S, 'kn_pickB'); S.cmp(0x8004, 0); S.goto_if(1, 'pb')
    S.raw(0x19, VAR_B & 255, VAR_B >> 8, 0x04, 0x80)
    wait_release(S, 'r2')
    S.close(); S.setvar(0x8009, 0); S.msg(t('A and B are registered.\nThe game uses them now.'), 4); S.releaseall(); S.end()
    remap = put_script(r, S)
    return report, remap


def install_hook(r, nat):
    # restore the key function at 0x15c898 that the failed remap hijacked, then hook the one ReadKeys really calls
    orig = bytes.fromhex('10b507480088074a')
    assert bytes(r.b[0x15C898:0x15C8A0]) == bytes.fromhex('004b1847a932ff08'), 'unexpected bytes at 0x15c898'
    r.b[0x15C898:0x15C8A0] = orig
    src = ('push {lr}\neors r3,r1\nmovs r0,r3\nldr r1,=%d\nbl cv\nmovs r3,r0\nldr r1,=0x030030f0\npop {r0}\nbx r0\ncv:\nbx r1\n.ltorg\n' % nat['kn_map'])
    hook = fn(r, src, 'hook')
    assert bytes(r.b[HOOK:HOOK + 2]) == bytes.fromhex('01b5'), 'hook entry not as expected'
    r.b[HOOK:HOOK + 8] = struct.pack('<HHI', 0x4A00, 0x4710, 0x08000000 + hook + 1)      # ldr r2,[pc,#0]; bx r2; .word hook
    return hook


def install(r):
    b = r.b
    assert bytes(b[THUNK1:THUNK1 + 2]) == bytes([0x08, 0x47]) and bytes(b[THUNK2:THUNK2 + 2]) == bytes([0x10, 0x47])
    nat = compile_natives(r, ['kn_now', 'kn_pickA', 'kn_pickB', 'kn_begin', 'kn_settle', 'kn_idle', 'kn_rec', 'kn_poll', 'kn_idlefin', 'kn_finA', 'kn_finB', 'kn_write', 'kn_map'])
    scripts = dict(zip((SEND, REG), build_scripts(r, nat)))
    cbs = {}
    for k, s in scripts.items():
        cbs[k] = 0x08000000 + callback(r, s, 'cb%d' % k) + 1
        r.w32(TBL + 8 * k + 4, cbs[k])
    # shorter names: the menu window is 8 characters wide
    for k, name in ((SEND, 'REPORT'), (REG, 'REMAP')):
        r.w32(TBL + 8 * k, 0x08000000 + r.alloc(enc(name), 1))
    for k, d in ((SEND, 'Save a controller log for\nthe GitROMs upload.'), (REG, 'Choose the buttons the game\nuses as A and B.')):
        r.w32(DESC + 4 * k, 0x08000000 + r.alloc(enc(d), 1))
    # menu tail: the same actions as before, called through the thunk
    order = [2, 9, 10, 11, 3, 4, 5, 6, SEND, REG]
    tail = fn(r, ''.join('movs r0,#%d\n' % k + call(0x0806ED94) for k in order) + 'pop {r0}\nbx r0\n.ltorg\n', 'tail')
    assert r.r32(0x6EDEC) != 0
    r.w32(0x6EDEC, 0x08000000 + tail + 1)
    # fade exemption: callbacks that run a script on the field keep the menu from fading out
    keep = [r.r32(TBL + 8 * k + 4) for k in (9, 10, 11, 4, 6, 7)] + [cbs[SEND], cbs[REG]]
    fade = fn(r, 'push {lr}\nldr r0,=0x20370f0\nldr r1,[r0]\n' +
              ''.join('ldr r0,=%d\ncmp r1,r0\nbeq done\n' % v for v in keep) +
              call(0x080CCB68) + 'movs r0,#1\nmovs r1,#0\nldr r2,=%d\nbl %d\n' % (0x0807A819, 0x08000000 + THUNK2) +
              'done:\npop {r0}\nbx r0\n.ltorg\n', 'fade')
    r.w32(0x6F398, 0x08000000 + fade + 1)
    hook = install_hook(r, nat)
    print('menu tail %#x fade %#x hook %#x natives %s' % (tail, fade, hook, {k: hex(v) for k, v in nat.items()}))


if __name__ == '__main__':
    r = Rom(sys.argv[1])
    install(r)
    r.save(sys.argv[2])

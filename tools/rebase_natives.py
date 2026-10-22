"""Native code added on top of the owner's personal ROM (usage: rebase_natives.py IN.gba OUT.gba). Source: story/rebase_native.c, table REBASE01.
 - battle-start hook: the trampoline's call to the old max_prepare goes to max_prepare_wrap (saves the trainer class in VAR 0x40F8, then runs max_prepare)
 - death: a new script runs death_fx (gunshot or cry, red fade), prints "You were mauled to death by a pokemon." for non-JRA killers, then continues
   into the old death script (white / hell). Every reference to the old death script goes to the new one.
 - AI partner: sPlayerBufferCommands entry 20 goes to partner_choose_move_fix
 - SHACKLE natives are in the table (tools/shackle.py builds the script that uses them)
Table order: max_prepare_wrap, death_fx, shackle_check, shackle_do, shoot_captain, partner_choose_move_fix."""
import sys, os, struct, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(1, '/home/claude/work/tools')
from inc import Rom
from cry_open import SB, put_script, say

SRC = os.path.join(HERE, '..', 'story'); WORK = '/tmp/rebase_native_build'
MAGIC = b'REBASE01'
NAMES = ('max_prepare_wrap', 'death_fx', 'shackle_check', 'shackle_do', 'shoot_captain', 'partner_choose_move_fix')
BATTLE_SITE_TRAMP = 0x3b2480          # the trampoline the battle start hook goes through (see story_native.py TRAMP_FREE[1])
PLAYER_CMDS = 0x25089c; PARTNER_ENTRY = 20
WHITEOUT_PTR = 0x7F5CC; CENTER_SCRIPT = 0x081A8D97

def addrs(r):
    i = bytes(r.b).find(MAGIC, 0xA00000); assert i > 0, 'rebase natives not applied'
    return dict(zip(NAMES, struct.unpack('<%dI' % len(NAMES), r.b[i + 8:i + 8 + 4 * len(NAMES)])))

def apply(r):
    b = r.b
    i = bytes(b).find(b'STORYFN1', 0xA00000); assert i > 0, 'story natives missing'
    old_mp = struct.unpack_from('<I', b, i + 16)[0]            # rep_calc, max_remove, max_prepare
    assert 0x08000000 <= old_mp < 0x09000000 and old_mp & 1
    open(os.path.join(SRC, 'rebase_gen.h'), 'w').write('#define OLD_MAX_PREPARE (0x%08x)\n' % old_mp)
    os.makedirs(WORK, exist_ok=True)
    r.cur = (r.cur + 3) & ~3; base = 0x08000000 + r.cur
    ld = os.path.join(WORK, 'rebase.ld'); o = os.path.join(WORK, 'rebase.o'); e = os.path.join(WORK, 'rebase.elf'); bn = os.path.join(WORK, 'rebase.bin')
    open(ld, 'w').write('ENTRY(max_prepare_wrap)\nSECTIONS { . = 0x%08x; .all : { *(.text*) *(.rodata*) *(.data*) } /DISCARD/ : { *(.ARM.exidx*) *(.comment) *(.note*) *(.ARM.attributes) } }\n' % base)
    subprocess.run(['clang', '--target=thumbv4t-none-eabi', '-mthumb', '-Os', '-ffreestanding', '-fno-builtin', '-fno-pic', '-fno-stack-protector', '-nostdlib',
                    '-fno-unwind-tables', '-fno-asynchronous-unwind-tables', '-c', os.path.join(SRC, 'rebase_native.c'), '-o', o], check=True)
    subprocess.run(['ld.lld', '-T', ld, o, '-o', e], check=True)
    subprocess.run(['llvm-objcopy', '-O', 'binary', e, bn], check=True)
    a = r.alloc(open(bn, 'rb').read(), 4); assert 0x08000000 + a == base
    sym = {}
    for ln in subprocess.run(['nm', e], capture_output=True, text=True, check=True).stdout.split('\n'):
        f = ln.split()
        if len(f) == 3: sym[f[2]] = int(f[0], 16)
    fn = lambda n: (sym[n] & ~1) | 1
    r.alloc(MAGIC + struct.pack('<%dI' % len(NAMES), *[fn(n) for n in NAMES]), 4)
    # 1. battle start: the trampoline's BL to the old max_prepare
    assert bytes(b[BATTLE_SITE_TRAMP:BATTLE_SITE_TRAMP + 4]) == bytes([0x00, 0x4b, 0x18, 0x47])
    p2 = (struct.unpack_from('<I', b, BATTLE_SITE_TRAMP + 4)[0] & ~1) - 0x08000000
    assert bytes(b[p2:p2 + 2]) == bytes([0x03, 0xb5]), 'trampoline not found'
    def bl_target(at):
        hi, lo = struct.unpack_from('<HH', b, at)
        assert hi & 0xF800 == 0xF000 and lo & 0xF800 == 0xF800
        off = ((hi & 0x7FF) << 12) | ((lo & 0x7FF) << 1)
        if off & 0x400000: off -= 0x800000
        return at + 4 + off
    assert bl_target(p2 + 2) == (old_mp & ~1) - 0x08000000, hex(bl_target(p2 + 2))
    r.bl(p2 + 2, (fn('max_prepare_wrap') & ~1) - 0x08000000)
    # 2. partner AI
    old_partner = struct.unpack_from('<I', b, PLAYER_CMDS + 4 * PARTNER_ENTRY)[0]
    assert 0x08000000 <= old_partner < 0x09000000 and old_partner & 1
    r.w32(PLAYER_CMDS + 4 * PARTNER_ENTRY, fn('partner_choose_move_fix'))
    # 3. death script
    sc = struct.unpack_from('<I', b, WHITEOUT_PTR)[0] - 0x08000000
    goto_center = bytes([0x05]) + struct.pack('<I', CENTER_SCRIPT)
    k = bytes(b[sc:sc + 600]).find(goto_center); assert k > 0, 'white-out script layout not recognised'
    assert b[sc + k + 5] == 0x05
    old_death = struct.unpack_from('<I', b, sc + k + 6)[0]
    assert 0x08000000 <= old_death < 0x09000000
    mauled = say(r, ['You were mauled to death by a pokemon.'])[0]
    D = SB(); D.lockall(); D.raw(0x23); D.ptr(fn('death_fx'))
    D.cmp(0x800c, 1); D.goto_if(1, 'm')
    D.lab('go'); D.raw(0x28, 40, 0); D.raw(0x05); D.ptr(old_death)
    D.lab('m'); D.msg(mauled); D.goto('go')
    new_death = 0x08000000 + put_script(r, D)
    pat = struct.pack('<I', old_death); n = 0; pos = 0
    while True:
        pos = bytes(b).find(pat, pos)
        if pos < 0: break
        if not (new_death - 0x08000000 <= pos < new_death - 0x08000000 + 64):     # not inside the new script
            r.w32(pos, new_death); n += 1
        pos += 1
    assert n >= 1, 'no reference to the old death script found'
    print('rebase_natives: table', MAGIC.decode(), 'old max_prepare', hex(old_mp), 'old partner', hex(old_partner),
          'death %s -> %s (%d references)' % (hex(old_death), hex(new_death), n))

if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')

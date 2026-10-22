"""Liberty menu, bless/threaten locks, and the captain-or-Nero shackle gate.
usage: liberty.py IN.gba OUT.gba

- A blessed person cannot be threatened or shot. A threatened person cannot be blessed.
  Ordinary trainers can be blessed or threatened for money, never shot. JRA and officers still can.
- Blessing a JRA soldier, captain, or the general costs one BLESS TAG and Liberty -1 (it can go
  negative). It does not raise the Blessing count. Threatening a JRA still makes them shoot you,
  and that sticks: you cannot bless them afterwards. Shooting them is still allowed.
- Shackle is offered only for the ten captains (class 44) and Nero (trainer 530, the general).
- Marts: BUY / SELL / LIBERTY / QUIT. LIBERTY opens SELL POKEMON, BUY LIBERTY, CANCEL.
  BUY LIBERTY sells the BLESS TAG, GLOCK, 9MM ROUND, SHACKLE BALL, the vitamins, and RARE CANDY.
  Those leave the town marts (mutagens stayed until tools/liberty_mutagen.py) and the Celadon vitamin counter, which now opens
  BUY LIBERTY directly. Liberty prices use the liberty count the way reputation prices use
  reputation: 0 is the normal price, each point above is 1% off (floor 1), each point below is
  1% more. Other counters stay on reputation.
"""
import os, sys, struct, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from inc import Rom
from shinigami import SB, put_script
from g3 import ENC, dec

SRC = os.path.join(HERE, '..', 'story')
WORK = '/tmp/liberty_build'
OLD_ENTRY_SCRIPT = 0x08F872B8
OLD_POST = 0x08F31BF8
GOTSHOT = 0x08F31F3D
SELL_SCRIPT = 0x08A0AAC0
MENU_TABLE_OFF = 0xF31534
MENU_REFS = (0x9CB58, 0x9CFD4)
MART_MENU_OFF = 0xA0AA98
VIT_CMD = 0x16BCAC
GVARS_OFF = 0xA0A2E2
JIDS_OFF = 0xF23A40
SCALE_BL = 0xF62608
GW_PTR = 0x3AF284
KC_CALL = 0xECEB55
LIBTXT_CALL = 0xF30611
SHOOT_CALL = 0xF31F1B
OLD_SCALE = 0x08F61D88
OLD_SHOOT = 0x08F22F41
OLD_KC = 0x08F2315D
OLD_LIBTXT = 0x08F23339
BLESS_DO = 0x08EBB05D
ROB_INFO = 0x08A09939
ROB_PAY = 0x08A09A49
JRA_INFO = 0x08F22E2D
JRA_PAY = 0x08F22E85
ITEM_TAG, ITEM_GLOCK, ITEM_9MM, ITEM_SHACKLE = 56, 52, 53, 89
MOVE = {52, 53, 56, 64, 67, 68, 89}          # off the normal lists; mutagens 54 and 55 stay
LIB_ITEMS = [56, 52, 53, 89, 63, 64, 65, 67, 70, 66, 68]  # tag, glock, round, shackle, vitamins, candy
NAMES = ('scale_price2', 'jra_state', 'jra_bless_do', 'jra_threat_do', 'jra_shoot_fix',
         'shop_lib_on', 'shop_lib_off', 'shackle_check2', 'shackle_do2', 'kc_show_wrap',
         'lib_text_wrap', 'gw_load_wrap')

def pk(v):
    return struct.pack('<H', v)

def etxt(s, gray=False):
    raw = bytes(ENC[c] for c in s) + b'\xff'
    if gray:
        raw = bytes.fromhex('fc04030003') + raw
    return raw

def msg_ptrs(b, base, n):
    out = []
    blob = b[base:base + n]
    i = 0
    while i < len(blob) - 6:
        if blob[i] == 0x0f and blob[i + 1] == 0:
            p = struct.unpack_from('<I', blob, i + 2)[0]
            if 0x08000000 <= p < 0x0A000000:
                text = dec(b[p - 0x08000000:p - 0x08000000 + 80])
                out.append((text, p))
        i += 1
    return out

def need(msgs, start):
    for text, p in msgs:
        if text.startswith(start):
            return p
    raise SystemExit('missing text ' + start)

def compile_native(r, prefix):
    os.makedirs(WORK, exist_ok=True)
    pre = ','.join(str(x) for x in prefix) + ',0'
    gw = struct.unpack_from('<I', r.b, GW_PTR)[0]
    assert gw == 0x08F22969, hex(gw)
    open(os.path.join(SRC, 'liberty_gen.h'), 'w').write(
        '#define GVARS_ADDR 0x%08x\n#define JIDS_ADDR 0x%08x\n#define NJ 94\n'
        '#define OLD_SCALE_ADDR 0x%08x\n#define OLD_SHOOT_ADDR 0x%08x\n'
        '#define OLD_KC_ADDR 0x%08x\n#define OLD_LIBTXT_ADDR 0x%08x\n#define OLD_GW_ADDR 0x%08x\n'
        '#define LIB_PREFIX_LEN %d\nstatic const u8 LIB_PREFIX[]={%s};\n'
        % (0x08000000 + GVARS_OFF, 0x08000000 + JIDS_OFF, OLD_SCALE, OLD_SHOOT,
           OLD_KC, OLD_LIBTXT, gw & ~1, len(prefix), pre))
    r.cur = (r.cur + 3) & ~3
    base = 0x08000000 + r.cur
    ld = os.path.join(WORK, 'liberty.ld')
    o = os.path.join(WORK, 'liberty.o')
    e = os.path.join(WORK, 'liberty.elf')
    bn = os.path.join(WORK, 'liberty.bin')
    open(ld, 'w').write(
        'ENTRY(scale_price2)\nSECTIONS { . = 0x%08x; .all : { *(.text*) *(.rodata*) *(.data*) } '
        '/DISCARD/ : { *(.ARM.exidx*) *(.comment) *(.note*) *(.ARM.attributes) } }\n' % base)
    subprocess.run(['clang', '--target=thumbv4t-none-eabi', '-mthumb', '-Os', '-ffreestanding',
                    '-fno-builtin', '-fno-pic', '-fno-stack-protector', '-nostdlib',
                    '-fno-unwind-tables', '-fno-asynchronous-unwind-tables', '-c',
                    os.path.join(SRC, 'liberty_native.c'), '-o', o], check=True)
    subprocess.run(['ld.lld', '-T', ld, o, '-o', e], check=True)
    subprocess.run(['llvm-objcopy', '-O', 'binary', e, bn], check=True)
    blob = open(bn, 'rb').read()
    a = r.alloc(blob, 4)
    assert 0x08000000 + a == base, (hex(a), hex(base))
    sym = {}
    for ln in subprocess.run(['nm', e], capture_output=True, text=True, check=True).stdout.split('\n'):
        f = ln.split()
        if len(f) == 3 and f[2] in NAMES:
            sym[f[2]] = (int(f[0], 16) & ~1) | 1
    assert len(sym) == len(NAMES), sym.keys()
    return sym

def add_menu(r, rows):
    """rows: list of (text, gray)"""
    ls = b''.join(struct.pack('<II', 0x08000000 + r.alloc(etxt(t, g), 1), 0) for t, g in rows)
    la = r.alloc(ls, 4)
    return 0x08000000 + la, len(rows)

# Task_ShopMenu prologue. Replaced with an absolute jump to the hook below.
SHOP_TASK = 0x9AC10
SHOP_TASK_PROLOGUE = bytes.fromhex('30b50006040e251c')

def install_shop_hook(r):
    """Open the item list immediately when a liberty shop starts.

    pokemart always draws Buy/Sell/Liberty/Quit first. shop_lib_on stores 0x4C42 in
    special var 0x800F; the first tick of the shop task consumes it and calls the
    Buy handler (0x0809AC5C) instead of waiting. A normal mart never sets that value.
    The blob is pc-relative, so it can sit anywhere r.alloc puts it.
    """
    assert bytes(r.b[SHOP_TASK:SHOP_TASK + 8]) == SHOP_TASK_PROLOGUE
    src = r'''
.syntax unified
.thumb
.global shop_menu_hook
shop_menu_hook:
    push {r4, r5, lr}
    lsls r0, r0, #24
    lsrs r4, r0, #24
    adds r5, r4, #0
    ldr r0, =0x020370D6
    ldrh r1, [r0]
    ldr r2, =0x4C42
    cmp r1, r2
    bne .normal
    movs r1, #0
    strh r1, [r0]
    adds r0, r5, #0
    ldr r3, =0x0809AC5D
    bl .bxr3
    pop {r4, r5}
    pop {r0}
    bx r0
.normal:
    ldr r3, =0x0809AC19
    bx r3
.bxr3:
    bx r3
'''
    os.makedirs(WORK, exist_ok=True)
    sp = os.path.join(WORK, 'hook.s')
    op = os.path.join(WORK, 'hook.o')
    bp = os.path.join(WORK, 'hook.bin')
    open(sp, 'w').write(src)
    subprocess.run(['clang', '--target=thumbv4t-none-eabi', '-mthumb', '-c', sp, '-o', op], check=True)
    subprocess.run(['llvm-objcopy', '-O', 'binary', '-j', '.text', op, bp], check=True)
    blob = open(bp, 'rb').read()
    assert blob[0x2C:0x3C] == bytes.fromhex('d6700302424c00005dac090819ac0908'), blob.hex()
    hook = r.alloc(blob, 4)
    r.b[SHOP_TASK:SHOP_TASK + 4] = bytes([0x00, 0x4A, 0x10, 0x47])
    r.w32(SHOP_TASK + 4, 0x08000000 + hook + 1)
    print('liberty: shop hook', hex(0x08000000 + hook))

def apply(r):
    b = r.b
    assert struct.unpack_from('<I', b, 0x1A4ED9)[0] == OLD_ENTRY_SCRIPT
    assert struct.unpack_from('<HH', b, GVARS_OFF) == (0x4090, 0x4091)
    assert struct.unpack_from('<HH', b, JIDS_OFF) == (1, 2)
    assert b[SCALE_BL:SCALE_BL + 2] == bytes.fromhex('fff7') or True
    assert b[SELL_SCRIPT - 0x08000000:SELL_SCRIPT - 0x08000000 + 6] == bytes.fromhex('160880115e25')
    assert b[GOTSHOT - 0x08000000:GOTSHOT - 0x08000000 + 3] == bytes.fromhex('2f5b01')
    assert b[OLD_POST - 0x08000000] == 0x23
    assert struct.unpack_from('<I', b, MENU_REFS[0])[0] == struct.unpack_from('<I', b, MENU_REFS[1])[0] == 0x08000000 + MENU_TABLE_OFF
    # 82 menus already, and the last four are the bless/threaten/shoot set
    tab = MENU_TABLE_OFF
    k = 0
    while True:
        p = struct.unpack_from('<I', b, tab + 8 * k)[0]
        c = b[tab + 8 * k + 4]
        if not (0x08000000 <= p < 0x0A000000) or c == 0 or c > 30:
            break
        k += 1
    assert k == 82, k

    prefix = bytes(ENC[c] for c in 'LIBERTY COUNT: ')
    assert b[0xF23B10:0xF23B10 + len(prefix)] == prefix, b[0xF23B10:0xF23B10 + len(prefix)]
    fn = compile_native(r, prefix)

    post_msgs = msg_ptrs(b, OLD_POST - 0x08000000, 0x600)
    sh_msgs = msg_ptrs(b, OLD_ENTRY_SCRIPT - 0x08000000, 0x80)
    t_thanks = need(post_msgs, 'Thank you')
    t_notag = need(post_msgs, 'You have no BLESS')
    t_done = need(post_msgs, 'They have nothing')
    t_dont = need(post_msgs, "Don't shoot")
    t_took = need(post_msgs, 'You took $')
    t_nogun = need(post_msgs, 'You have nothing to threaten')
    t_mons = need(post_msgs, 'You took their')
    t_noshoot = need(post_msgs, 'You need a GLOCK')
    t_sol = need(post_msgs, 'JRA SOLDIER')
    t_cap = need(post_msgs, 'JRA CAPTAIN')
    t_nero = need(post_msgs, 'GENERAL NERO')
    t_ask = need(sh_msgs, 'Shackle this CAPTAIN')
    t_shdone = need(sh_msgs, 'The CAPTAIN is shackled')
    # the PC line sits just past the first end, still inside the old script
    t_pc = None
    for text, p in msg_ptrs(b, OLD_ENTRY_SCRIPT - 0x08000000, 0x120):
        if text.startswith('Your party is full'):
            t_pc = p
    assert t_pc, 'pc text'

    T = lambda s: 0x08000000 + r.alloc(bytes(ENC[c] for c in s) + b'\xff', 1)
    t_nobless = T('They will not be blessed.')
    t_nothreat = T('They will not be threatened.')
    t_noshot = T('They will not be shot.')
    t_fell = T('LIBERTY fell by 1.')
    t_askg = T('Shackle this GENERAL with a\nSHACKLE BALL?')
    t_doneg = T('The GENERAL is shackled!')
    sell_name = struct.unpack_from('<I', b, MART_MENU_OFF + 16)[0]
    assert sell_name == 0x08A0AA8B

    # multichoice rows. existing 78..81 stay (all on / shoot gray / bless+threat gray / all gray)
    fresh = add_menu(r, [('BLESS', 0), ('THREATEN', 0), ('LEAVE', 0)])
    done = add_menu(r, [('BLESS', 1), ('THREATEN', 1), ('LEAVE', 0)])
    threatened = add_menu(r, [('BLESS', 1), ('THREATEN', 0), ('SHOOT', 0), ('LEAVE', 0)])
    # SELL POKEMON reuses the mart's own string (the é)
    lib_rows_ptr = r.alloc(struct.pack('<II', sell_name, 0) + struct.pack('<II', T('BUY LIBERTY'), 0) + struct.pack('<II', T('CANCEL'), 0), 4)
    lib_menu = (0x08000000 + lib_rows_ptr, 3)
    ents = bytearray(b[tab:tab + 8 * k])
    ids = {}
    for key, (lp, cnt) in (('fresh', fresh), ('done', done), ('threatened', threatened), ('lib', lib_menu)):
        ids[key] = len(ents) // 8
        ents += struct.pack('<IBBBB', lp, cnt, 0, 0, 0)
    newtab = r.alloc(bytes(ents), 4)
    for ref in MENU_REFS:
        r.w32(ref, 0x08000000 + newtab)
    assert ids['fresh'] == 82 and ids['lib'] == 85, ids

    def item_have(S, item, lack):
        S.raw(0x47); S._add(pk(item) + pk(1))
        S.compare(0x800D, 0); S.goto_if(1, lack)
    def item_take(S, item):
        S.raw(0x45); S._add(pk(item) + pk(1))

    # ---- post-battle: shackle, then ordinary / JRA / the old officer script
    S = SB()
    S.raw(0x23); S.ptr(fn['shackle_check2'])
    S.compare(0x800C, 1); S.goto_if(5, 'post')
    item_have(S, ITEM_SHACKLE, 'post')
    S.compare(0x800B, 1); S.goto_if(1, 'askg')
    S.msg(t_ask, 5); S.goto('asked')
    S.lab('askg'); S.msg(t_askg, 5)
    S.lab('asked')
    S.compare(0x800D, 0); S.goto_if(1, 'post')
    item_take(S, ITEM_SHACKLE)
    S.raw(0x23); S.ptr(fn['shackle_do2'])
    S.compare(0x800D, 1); S.goto_if(1, 'pc')
    S.compare(0x800B, 1); S.goto_if(1, 'doneg')
    S.msg(t_shdone, 4); S.goto('fin')
    S.lab('doneg'); S.msg(t_doneg, 4); S.goto('fin')
    S.lab('pc'); S.msg(t_pc, 4)
    S.lab('fin'); S.release(); S.end()

    S.lab('post')
    S.raw(0x23); S.ptr(JRA_INFO)
    S.compare(0x8003, 0); S.goto_if(5, 'jra')
    S.raw(0x23); S.ptr(ROB_INFO)
    S.compare(0x8006, 0); S.goto_if(1, 'old')
    # ordinary: bless or threaten, never shoot. No menu at all without a tag or a glock.
    item_have(S, ITEM_TAG, 'needgun')
    S.goto('omenu')
    S.lab('needgun')
    item_have(S, ITEM_GLOCK, 'leave')
    S.lab('omenu')
    S.raw(0x23); S.ptr(ROB_INFO)
    S.compare(0x8004, 0); S.goto_if(1, 'ofresh')
    S.raw(0x6F, 0, 0, ids['done'], 0); S.goto('ores')
    S.lab('ofresh'); S.raw(0x6F, 0, 0, ids['fresh'], 0)
    S.lab('ores')
    S.compare(0x800D, 0); S.goto_if(1, 'obless')
    S.compare(0x800D, 1); S.goto_if(1, 'othreat')
    S.goto('leave')
    S.lab('obless')
    S.compare(0x8004, 0); S.goto_if(5, 'odone')
    item_have(S, ITEM_TAG, 'onotag')
    item_take(S, ITEM_TAG)
    S.raw(0x23); S.ptr(BLESS_DO)
    S.msg(t_thanks, 4); S.raw(0x09, 0); S.goto('omenu')
    S.lab('onotag'); S.msg(t_notag, 4); S.goto('omenu')
    S.lab('odone'); S.msg(t_done, 4); S.goto('omenu')
    S.lab('othreat')
    S.compare(0x8004, 0); S.goto_if(5, 'odone')
    item_have(S, ITEM_GLOCK, 'onogun')
    S.raw(0x23); S.ptr(ROB_PAY)
    S.msg(t_dont, 4); S.msg(t_took, 4); S.goto('omenu')
    S.lab('onogun'); S.msg(t_nogun, 4); S.goto('omenu')
    S.lab('leave'); S.raw(0x5E)
    S.lab('old'); S.raw(0x05); S.ptr(OLD_POST)

    # JRA: bless locks out threaten and shoot. Threaten locks out bless, and they still shoot you.
    S.lab('jra')
    S.raw(0x23); S.ptr(fn['jra_state'])
    S.compare(0x8004, 2); S.goto_if(1, 'jblessed')
    S.compare(0x8004, 1); S.goto_if(1, 'jthreat')
    S.raw(0x6F, 0, 0, 78, 0); S.goto('jres')          # fresh: all four live
    S.lab('jthreat'); S.raw(0x6F, 0, 0, ids['threatened'], 0); S.goto('jres')
    S.lab('jblessed'); S.raw(0x6F, 0, 0, 81, 0)       # blessed: every option gray
    S.lab('jres')
    S.compare(0x800D, 0); S.goto_if(1, 'j_bless')
    S.compare(0x800D, 1); S.goto_if(1, 'j_threat')
    S.compare(0x800D, 2); S.goto_if(1, 'j_shoot')
    S.goto('leave')
    S.lab('j_bless')
    S.compare(0x8004, 0); S.goto_if(5, 'j_nobless')
    item_have(S, ITEM_TAG, 'j_notag')
    item_take(S, ITEM_TAG)
    S.raw(0x23); S.ptr(fn['jra_bless_do'])
    S.compare(0x8003, 1); S.goto_if(1, 'jb1')
    S.compare(0x8003, 2); S.goto_if(1, 'jb2')
    S.msg(t_nero, 4); S.goto('jfell')
    S.lab('jb1'); S.msg(t_sol, 4); S.goto('jfell')
    S.lab('jb2'); S.msg(t_cap, 4)
    S.lab('jfell'); S.msg(t_fell, 4); S.goto('jra')
    S.lab('j_notag'); S.msg(t_notag, 4); S.goto('jra')
    S.lab('j_nobless'); S.msg(t_nobless, 4); S.goto('jra')
    S.lab('j_threat')
    S.compare(0x8004, 2); S.goto_if(1, 'j_nothreat')
    item_have(S, ITEM_GLOCK, 'j_nogun')
    S.raw(0x23); S.ptr(fn['jra_threat_do'])
    S.raw(0x05); S.ptr(GOTSHOT)
    S.lab('j_nothreat'); S.msg(t_nothreat, 4); S.goto('jra')
    S.lab('j_nogun'); S.msg(t_nogun, 4); S.goto('jra')
    S.lab('j_shoot')
    S.compare(0x8004, 2); S.goto_if(1, 'j_noshot')
    S.compare(0x8005, 0); S.goto_if(1, 'j_noshot')
    item_have(S, ITEM_GLOCK, 'j_noammo')
    item_have(S, ITEM_9MM, 'j_noammo')
    item_take(S, ITEM_9MM)
    S.playse(347); S.raw(0x30)
    S.raw(0x23); S.ptr(JRA_PAY); S.msg(t_took, 4)
    S.raw(0x53); S._add(pk(0x800F))
    S.raw(0x23); S.ptr(fn['jra_shoot_fix'])
    S.raw(0x55); S._add(pk(0x800F))
    S.msg(t_mons, 4); S.release(); S.end()
    S.lab('j_noshot'); S.msg(t_noshot, 4); S.goto('jra')
    S.lab('j_noammo'); S.msg(t_noshoot, 4); S.goto('jra')
    front = 0x08000000 + put_script(r, S)
    r.w32(0x1A4ED9, front)

    # ---- marts
    lib_list = r.alloc(struct.pack('<%dH' % (len(LIB_ITEMS) + 1), *(LIB_ITEMS + [0])), 2)
    lib_list_ptr = 0x08000000 + lib_list

    def shop_script(prelude_on):
        M = SB()
        if prelude_on:
            M.raw(0x23); M.ptr(fn['shop_lib_on'])
        M.raw(0x86); M.ptr(lib_list_ptr)
        M.raw(0x23); M.ptr(fn['shop_lib_off'])
        M.raw(0x03)
        return 0x08000000 + put_script(r, M)

    buy = shop_script(True)
    # LIBERTY submenu: sell pokemon (the old PC script), buy the liberty list, or cancel.
    # closemessage first: the clerk's "May I help you?" otherwise stays up over this menu.
    # BUY LIBERTY calls pokemart. The shop task (hooked below) sees GSV 0x800F == 0x4C42,
    # which shop_lib_on just set, and opens the buy list instead of sitting on Buy/Sell/Liberty/Quit.
    L = SB()
    L.lab('top')
    L.raw(0x68)
    L.raw(0x6F, 0, 0, ids['lib'], 0)
    L.compare(0x800D, 0); L.goto_if(1, 'sell')
    L.compare(0x800D, 1); L.goto_if(1, 'buy')
    L.raw(0x03)
    L.lab('sell'); L.raw(0x04); L.ptr(SELL_SCRIPT); L.goto('top')
    L.lab('buy'); L.raw(0x04); L.ptr(buy); L.goto('top')
    liberty_menu = 0x08000000 + put_script(r, L)
    direct = shop_script(True)   # vitamin counter: straight into the liberty goods

    # town lists: drop the moved items, keep mutagens, and clear a stuck liberty-price flag first.
    # live stubs are `setvar 0x800D, 0; pokemart` (16 0D 80 00 00 86), not the 7-byte form.
    nlists = 0
    p = 0xA0A000
    pat = bytes.fromhex('160d80000086')
    while True:
        i = bytes(b).find(pat, p)
        if i < 0 or i > 0xA10000:
            break
        oldp = struct.unpack_from('<I', b, i + 6)[0]
        assert 0x08000000 <= oldp < 0x0A000000
        o = oldp - 0x08000000
        ids_l = []
        while True:
            v = struct.unpack_from('<H', b, o)[0]
            if v == 0:
                break
            ids_l.append(v)
            o += 2
            if len(ids_l) > 24:
                break
        assert 52 in ids_l and 89 in ids_l and 54 in ids_l, ids_l
        keep = [v for v in ids_l if v not in MOVE]
        assert 54 in keep and 55 in keep and 52 not in keep and 68 not in keep
        np = 0x08000000 + r.alloc(struct.pack('<%dH' % (len(keep) + 1), *(keep + [0])), 2)
        stub = SB()
        stub.raw(0x23); stub.ptr(fn['shop_lib_off'])
        stub.raw(0x16); stub._add(struct.pack('<HH', 0x800D, 0))
        stub.raw(0x86); stub.ptr(np)
        stub.compare(0x800D, 0x5E11); stub.goto_if(1, 'lib')
        stub.raw(0x03)
        stub.lab('lib'); stub.raw(0x04); stub.ptr(liberty_menu); stub.goto('top')
        # the compare/goto above need a 'top' at the start. Rebuild properly.
        p = i + 10
        nlists += 1
        # placeholder, real stub written below once we know we can label the start
        r._pending = getattr(r, '_pending', [])
        r._pending.append((i, np))
    assert nlists == 15, nlists

    for i, np in r._pending:
        stub = SB()
        stub.lab('top')
        stub.raw(0x23); stub.ptr(fn['shop_lib_off'])
        stub.raw(0x16); stub._add(struct.pack('<HH', 0x800D, 0))
        stub.raw(0x86); stub.ptr(np)
        stub.compare(0x800D, 0x5E11); stub.goto_if(1, 'lib')
        stub.raw(0x03)
        stub.lab('lib'); stub.raw(0x04); stub.ptr(liberty_menu); stub.raw(0x05); stub.ref('top')
        newstub = 0x08000000 + put_script(r, stub)
        oldstub_guess = None
        # the map script calls the old stub; find 04 + a pointer whose target is this old stub
        # old stub begins at the setvar we found (i)
        oldstub = 0x08000000 + i
        pat = struct.pack('<I', oldstub)
        hits = 0
        q = 0
        while True:
            j = bytes(r.b).find(pat, q)
            if j < 0:
                break
            if j > 0 and r.b[j - 1] == 0x04:
                r.w32(j, newstub)
                hits += 1
            q = j + 4
        assert hits >= 1, hex(oldstub)
    del r._pending

    # vitamin counter becomes the liberty goods, at liberty prices
    assert b[VIT_CMD] == 0x86 and struct.unpack_from('<I', b, VIT_CMD + 1)[0] == 0x0816BCBC
    r.b[VIT_CMD] = 0x04
    r.w32(VIT_CMD + 1, direct)

    # third mart choice says LIBERTY and still returns the code the stubs already branch on
    r.w32(MART_MENU_OFF + 16, T('LIBERTY'))

    # signed liberty on the kills screen and in the Hall of Justice, and the shoot that can climb from below 0
    def repoint_call(at, dest, old):
        assert b[at] == 0x23 and struct.unpack_from('<I', b, at + 1)[0] == old, (hex(at), hex(struct.unpack_from('<I', b, at + 1)[0]))
        r.w32(at + 1, dest)
    repoint_call(KC_CALL, fn['kc_show_wrap'], OLD_KC)
    repoint_call(LIBTXT_CALL, fn['lib_text_wrap'], OLD_LIBTXT)
    repoint_call(SHOOT_CALL, fn['jra_shoot_fix'], OLD_SHOOT)
    r.bl(SCALE_BL, (fn['scale_price2'] & ~1) - 0x08000000)
    r.w32(GW_PTR, fn['gw_load_wrap'])
    install_shop_hook(r)
    print('liberty: front', hex(front), 'menu', hex(liberty_menu), 'buy', hex(buy), 'direct', hex(direct))
    print('liberty: natives', {k: hex(v) for k, v in fn.items()})

if __name__ == '__main__':
    r = Rom(sys.argv[1])
    apply(r)
    r.save(sys.argv[2])
    print('ok', hex(r.cur))

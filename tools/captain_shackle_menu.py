"""Shackle is a fifth option on the JRA menu, shown only for captains.
Defeated captain scripts hand off to the menu instead of ending."""
import sys, struct
sys.path.insert(0, 'tools')
from inc import *
from shinigami import SB, put_script
from leg1 import enc

FRONT = 0x08F8CEC0
MENU_REFS = (0x9CB58, 0x9CFD4)
ITEM_SHACKLE = 89

def etxt(s, gray=False):
    GRAY = bytes([0xfc, 0x04, 0x03, 0x00, 0x03])
    raw = enc(s)
    return (GRAY + raw) if gray else raw

def add_menu(r, rows):
    ls = b''.join(struct.pack('<II', 0x08000000 + r.alloc(etxt(t, g), 1), 0) for t, g in rows)
    la = r.alloc(ls, 4)
    return 0x08000000 + la, len(rows)

def install(r):
    b = r.b
    # 1. Captain menu
    cap_ptr, cap_cnt = add_menu(r, [
        ('BLESS', 0), ('THREATEN', 0), ('SHOOT', 0), ('SHACKLE', 0), ('LEAVE', 0)
    ])
    tab = struct.unpack('<I', b[MENU_REFS[0]:MENU_REFS[0]+4])[0] - 0x08000000
    k = 0
    while True:
        p = struct.unpack('<I', b[tab+8*k:tab+8*k+4])[0]
        c = b[tab+8*k+4]
        if not (0x08000000 <= p < 0x0A000000) or c == 0 or c > 30: break
        k += 1
    cap_id = k
    new_tab = r.alloc(b[tab:tab+8*k] + struct.pack('<IBBBB', cap_ptr, cap_cnt, 0, 0, 0), 4)
    for ref in MENU_REFS:
        r.w32(ref, 0x08000000 + new_tab)
    print(f'captain menu id {cap_id}')

    # 2. Chooser: if GSV(3)==2 use captain menu, else menu 78
    chooser = SB()
    chooser.compare(0x8003, 2)
    chooser.goto_if(1, 'cap')
    chooser.raw(0x6f, 0, 0, 78, 0)
    chooser.goto('done')
    chooser.lab('cap')
    chooser.raw(0x6f, 0, 0, cap_id, 0)
    chooser.lab('done')
    chooser.end()
    chooser_ptr = 0x08000000 + put_script(r, chooser)

    # Wire into the front script (replace the menu-78 multichoice)
    front_off = FRONT - 0x08000000
    pat = bytes([0x6f, 0x00, 0x00, 78, 0x00])
    target = None
    pos = front_off
    while pos < front_off + 0x400:
        i = b.find(pat, pos, front_off + 0x400)
        if i < 0: break
        target = i
        break
    assert target, 'menu 78 not found in front script'
    b[target:target+5] = bytes([0x04]) + struct.pack('<I', chooser_ptr)
    print(f'chooser wired at {hex(target)}')

    # 3. Shackle result handler
    # After menu, if GSV(3)==2 and result==3: take shackle, call shackle_do2, message
    # Find shackle_do2 from the native exports (liberty.py compiled it)
    # Search for the function by its unique prologue or known offset
    # For now, emit the item check and a placeholder message; the native call
    # needs the address. We'll find it.
    # shackle_do2 is in the liberty native. Search for its call site in the old pre-menu.
    # The old pre-menu called it. Find that call.
    shackle_do2 = None
    # Look for the pattern: special call followed by compare 0x800D (the result check after shackle)
    pos = 0
    while True:
        i = b.find(b'\x23', pos)
        if i < 0 or i > 0x1000000: break
        ptr = struct.unpack('<I', b[i+1:i+5])[0]
        if 0x08F00000 <= ptr < 0x09000000:
            # Check if next is compare 0x800D
            if b[i+5:i+8] == b'\x21\x0d\x80':
                shackle_do2 = ptr
                break
        pos = i + 1
    print(f'shackle_do2 candidate: {hex(shackle_do2) if shackle_do2 else None}')

    handler = SB()
    handler.compare(0x8003, 2)
    handler.goto_if(5, 'no')
    handler.compare(0x800D, 3)
    handler.goto_if(5, 'no')
    handler.raw(0x47); handler._add(struct.pack('<HH', ITEM_SHACKLE, 1))
    handler.compare(0x800D, 0)
    handler.goto_if(1, 'noitem')
    handler.raw(0x45); handler._add(struct.pack('<HH', ITEM_SHACKLE, 1))
    if shackle_do2:
        handler.raw(0x23); handler.ptr(shackle_do2)
    handler.msg(0x08000000 + r.alloc(enc('The CAPTAIN is shackled.'), 1), 4)
    handler.release()
    handler.end()
    handler.lab('noitem')
    handler.msg(0x08000000 + r.alloc(enc('You have no SHACKLE BALL.'), 1), 4)
    handler.lab('no')
    handler.end()
    handler_ptr = 0x08000000 + put_script(r, handler)

    # Insert the handler call after the shoot goto_if, before the leave fallthrough
    # The shoot check is at ~0xf8d0ae: compare 0x800D,2; goto_if 1, shoot
    # After that (6 bytes for goto_if) is the leave path
    cmp_pat = bytes([0x21]) + struct.pack('<HH', 0x800D, 2)
    pos = front_off
    while pos < front_off + 0x500:
        i = b.find(cmp_pat, pos, front_off + 0x500)
        if i < 0: break
        if b[i+5] == 0x06:
            # goto_if is 6 bytes. The next instruction is the leave fallthrough.
            # Replace the first byte of the fallthrough with a call to handler,
            # and have handler's 'no' path continue to the original fallthrough.
            fall = i + 5 + 6
            # Save the original fallthrough bytes and make handler jump there on 'no'
            # Simpler: overwrite the fallthrough start with a call, and have
            # the handler's end be the original instruction.
            # Even simpler: change the fallthrough to: call handler; <original>
            orig = bytes(b[fall:fall+5])
            b[fall:fall+5] = bytes([0x04]) + struct.pack('<I', handler_ptr)
            # The handler's 'no' label ends. We need it to continue.
            # Rebuild handler so 'no' calls back... actually the handler ends,
            # and the call returns. So after the call, execution continues
            # at fall+5, which is whatever was there. That's wrong if we
            # overwrote a multi-byte instruction.
            # Check what was at fall.
            print(f'fallthrough at {hex(fall)}: {orig.hex()}')
            break
        pos = i + 1

    # 4. Captain scripts: again path jumps to FRONT
    for flag in range(0x4C0, 0x4CA):
        pat = b'\x29' + struct.pack('<H', flag)
        pos = 0
        while True:
            i = b.find(pat, pos)
            if i < 0: break
            # Verify this is a captain script (trainerbattle type 1 nearby)
            if i > 40 and b[i-36:i-34] == b"\x5c\x01":
                # Find the two ends: first win end, then again end
                e1 = b.find(b'\x02', i)
                if 0 < e1 < i + 50:
                    e2 = b.find(b'\x02', e1 + 1)
                    if 0 < e2 < e1 + 40:
                        # The again path is between e1+1 and e2
                        # Replace e2 (the again end) with a call to FRONT
                        b[e2:e2+5] = bytes([0x04]) + struct.pack('<I', FRONT)
                        print(f'flag 0x{flag:04x}: again -> menu')
            pos = i + 1

if __name__ == '__main__':
    r = Rom(sys.argv[1])
    install(r)
    r.save(sys.argv[2])
    print('end', hex(r.cur))

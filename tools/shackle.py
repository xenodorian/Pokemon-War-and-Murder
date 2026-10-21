"""Owner task 13: SHACKLE on a defeated captain (usage: shackle.py IN.gba OUT.gba). Runs after shackle_item.py.
 - the defeated-trainer script at ROM 0x1a4ed9 gets a new front: for a captain (story_native.c shackle_check) that is defeated with a SHACKLE BALL
   (item 89) the player is asked "Shackle this CAPTAIN with a SHACKLE BALL?". YES uses one ball and calls shackle_do: +5 liberty and the captain's
   last Pokemon is given like any other (party, or the PC when the party is full). NO, no ball, or any other trainer goes to the old script
   (the bless / rob / shoot menu), unchanged.
 - every shoot_do call in the script calls shoot_captain instead: the base shoot, then +10 liberty for a captain. Other trainers are unchanged.
Deviation: SHACKLE is a yes/no question before the bless/shoot menu, not a fourth entry in that menu (the menu table is built by gun.py)."""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(1, '/home/claude/work/tools')
from inc import Rom
from shinigami import SB, put_script
import story_native as SN
import leg1

ENTRY = 0x1a4ed9; SHOOT_DO = 0x08a09b61; ITEM_SHACKLE = 89
def pk(v): return struct.pack('<H', v)

def apply(r):
    b = r.b
    old = struct.unpack_from('<I', b, ENTRY)[0]
    assert old >= 0x08000000, hex(old)
    fns = SN.addrs6(r)
    T = lambda s: 0x08000000 + r.alloc(leg1.enc(s), 1)
    t_ask = T('Shackle this CAPTAIN with a\nSHACKLE BALL?')
    t_done = T('The CAPTAIN is shackled!')
    t_pc = T("Your party is full. The POKeMON\nwas sent to the PC.")
    S = SB()
    S.raw(0x23); S.ptr(fns['shackle_check'])
    S.compare(0x800c, 1); S.goto_if(1, 'cap')
    S.lab('oldj'); S.raw(0x05); S.ptr(old)
    S.lab('cap')
    S.raw(0x47); S._add(pk(ITEM_SHACKLE) + pk(1)); S.compare(0x800d, 0); S.goto_if(1, 'oldj')
    S.msg(t_ask, 5); S.compare(0x800d, 0); S.goto_if(1, 'oldj')
    S.raw(0x45); S._add(pk(ITEM_SHACKLE) + pk(1))
    S.raw(0x23); S.ptr(fns['shackle_do'])
    S.compare(0x800d, 1); S.goto_if(1, 'pc')
    S.msg(t_done); S.release(); S.end()
    S.lab('pc'); S.msg(t_pc); S.release(); S.end()
    new = 0x08000000 + put_script(r, S)
    r.w32(ENTRY, new)
    n = 0
    for o in range(0, len(b) - 5):
        if b[o] == 0x23 and struct.unpack_from('<I', b, o + 1)[0] == SHOOT_DO:
            r.w32(o + 1, fns['shoot_captain']); n += 1
    assert n >= 1, 'no shoot call found'
    print('shackle: script %s, shoot calls redirected %d' % (hex(new), n))

if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')

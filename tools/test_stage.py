"""TEST ONLY stage (usage: TEST_...=.. python3 tools/test_stage.py IN.gba OUT.gba). Never run on the release ROM through patch.sh.
Make the scratch copy with tools/mk_test_rom.sh, which writes to /tmp (the guard bans extra .gba files in the repo).
Stepping on the bedroom door tile then runs a test script instead of the normal one. Switches (same names as the old chain build):
  TEST_FOE=species,level (default 16,5) wild battle | TEST_TRAINER=id trainer battle | TEST_GIVE=species,level adds a mon first
  TEST_GIVE_MORE=species,level;species,level | TEST_ITEM=id,qty | TEST_MASTER=1 five MASTER BALLs | TEST_LEAF=1 LEAF joins
  TEST_PLAYABLE=1 sets the playable-run flag (loss = death) | TEST_GOTO=0xADDR run the script at that ROM address | TEST_AFTER=1 (with TEST_TRAINER) jump to the SHACKLE script after the battle | TEST_WARP=group,num,x,y warp instead of battle"""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from inc import Rom
from cry_open import SB, put_script, enc
HEV = 0x3b974c; SHACKLE_ENTRY = 0x1a4ed9
def apply(r):
    e = os.environ; tb = SB()
    if e.get('TEST_PLAYABLE'): tb.setflag(0x84A)
    for g in e.get('TEST_GIVE_MORE', '').split(';'):
        if g:
            gs, gl = [int(x) for x in g.split(',')]; tb.raw(0x79, gs & 255, gs >> 8, gl, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    if e.get('TEST_MASTER'): tb.raw(0x44, 1, 0, 5, 0)
    if e.get('TEST_GIVE'):
        gs, gl = [int(x) for x in e['TEST_GIVE'].split(',')]; tb.raw(0x79, gs & 255, gs >> 8, gl, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    if e.get('TEST_LEAF'): tb.raw(0x23); tb.ptr(0x083b24b1)
    if e.get('TEST_GOTO'):
        tb.lockall(); tb.raw(0x05); tb.ptr(int(e['TEST_GOTO'], 16))
    elif e.get('TEST_WARP'):
        wg, wn, wx, wy = [int(x) for x in e['TEST_WARP'].split(',')]
        tb.releaseall(); tb.raw(0x39, wg, wn, 0xff, wx & 255, wx >> 8, wy & 255, wy >> 8); tb.raw(0x27); tb.end()
    elif e.get('TEST_TRAINER'):
        tid = int(e['TEST_TRAINER']); tt = 0x08000000 + r.alloc(enc("TEST ")[:-1] + b' \xff', 1)
        if e.get('TEST_ITEM'):
            ti, tq = [int(x) for x in e['TEST_ITEM'].split(',')]; tb.raw(0x44, ti & 255, ti >> 8, tq & 255, tq >> 8)
        if e.get('TEST_AFTER'): tb.raw(0x05); tb.ptr(r.r32(SHACKLE_ENTRY))
        tb.raw(0x5c, 0, tid & 255, tid >> 8, 0, 0); tb.ptr(tt); tb.ptr(tt); tb.releaseall(); tb.end()
    else:
        foe = [int(x) for x in e.get('TEST_FOE', '16,5').split(',')]
        tb.raw(0xb6, foe[0] & 255, foe[0] >> 8, foe[1], 0, 0); tb.raw(0xb7); tb.end()
    scr = 0x08000000 + put_script(r, tb)
    n = r.b[HEV + 2]; ca = r.r32(HEV + 12) - 0x08000000
    for i in range(n): r.w32(ca + 16 * i + 12, scr)
    print('test_stage: door tile script %s (%d tile events)' % (hex(scr), n))
if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')

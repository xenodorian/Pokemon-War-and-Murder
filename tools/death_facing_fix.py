"""Death script: "You were mauled..." depended on the way LEAF faced (usage: death_facing_fix.py IN.gba OUT.gba), run through tools/patch.sh.
Bug (open item under the shackle note): the death script death_fade.py wrote is
  lockall; callnative death_fx; try: callnative death_fade_try; compare 0x800D,1; goto_if EQ ok; delay 2; goto try;
  ok: delay 40; compare 0x800C,1; goto_if EQ m; go: goto old_death; m: msgbox mauled; goto go
death_fx (death_fx_live, story/death_class_native.c) stores the mauled flag in GSV(12) = 0x020370D0 = 0x800D (VAR_RESULT), not 0x800C
(VAR_FACING, 0x020370D4), and death_fade_try then overwrites 0x800D with its own result. So the line showed only when LEAF faced down,
for JRA kills too, and never for a wild or ordinary kill while facing another way.
Fix: a new copy of the script saves the flag right after death_fx (copyvar 0x8004, 0x800D) and the mauled branch compares 0x8004.
Everything else (natives, fade loop, mauled text, old death script) is reused as it is. References to the old script are repointed.
Located from the white-out pointer like death_fade.py. Idempotent (refuses nothing, skips when already fixed)."""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from inc import Rom
from cry_open import SB, put_script
import rebase_natives as RN

SAVE_VAR = 0x8004

def find_death(b):
    sc = struct.unpack_from('<I', b, RN.WHITEOUT_PTR)[0] - 0x08000000
    goto_center = bytes([0x05]) + struct.pack('<I', RN.CENTER_SCRIPT)
    k = bytes(b[sc:sc + 600]).find(goto_center); assert k > 0 and b[sc + k + 5] == 0x05
    return struct.unpack_from('<I', b, sc + k + 6)[0]

def apply(r):
    b = r.b; fns = RN.addrs(r)
    cur = find_death(b); cs = cur - 0x08000000
    assert b[cs] == 0x69 and b[cs + 1] == 0x23 and struct.unpack_from('<I', b, cs + 2)[0] == fns['death_fx'], 'death script not the death_fade one'
    if b[cs + 6] == 0x19:
        assert struct.unpack_from('<HH', b, cs + 7) == (SAVE_VAR, 0x800D); print('death_facing_fix: already applied at %#x' % cur); return
    # death_fade.py layout: 23 fade; 21 0d80 0100; 06 01 ok; 28 02 00; 05 try | ok: 28 28 00; 21 0c80 0100; 06 01 m | go: 05 old | m: 0f 00 txt; 09 04; 05 go
    assert b[cs + 6] == 0x23; fade = struct.unpack_from('<I', b, cs + 7)[0]
    assert bytes(b[cs + 11:cs + 16]) == bytes([0x21, 0x0D, 0x80, 0x01, 0x00]) and b[cs + 16] == 0x06
    assert bytes(b[cs + 22:cs + 25]) == bytes([0x28, 0x02, 0x00]) and b[cs + 25] == 0x05
    o = cs + 30
    assert bytes(b[o:o + 3]) == bytes([0x28, 0x28, 0x00]), 'no delay 40'
    assert bytes(b[o + 3:o + 8]) == bytes([0x21, 0x0C, 0x80, 0x01, 0x00]) and bytes(b[o + 8:o + 10]) == bytes([0x06, 0x01]), 'mauled compare not 0x800C'
    m = struct.unpack_from('<I', b, o + 10)[0] - 0x08000000
    go = o + 14; assert b[go] == 0x05; old_death = struct.unpack_from('<I', b, go + 1)[0]
    assert m == go + 5 and bytes(b[m:m + 2]) == bytes([0x0F, 0x00]) and bytes(b[m + 6:m + 8]) == bytes([0x09, 0x04])
    mauled = struct.unpack_from('<I', b, m + 2)[0]
    D = SB(); D.lockall(); D.raw(0x23); D.ptr(fns['death_fx'])
    D.raw(0x19, *struct.pack('<HH', SAVE_VAR, 0x800D))                    # copyvar 0x8004, 0x800D (mauled flag from death_fx)
    D.lab('try'); D.raw(0x23); D.ptr(fade); D.cmp(0x800D, 1); D.goto_if(1, 'ok'); D.raw(0x28, 2, 0); D.goto('try')
    D.lab('ok'); D.raw(0x28, 40, 0)
    D.cmp(SAVE_VAR, 1); D.goto_if(1, 'm')
    D.lab('go'); D.raw(0x05); D.ptr(old_death)
    D.lab('m'); D.msg(mauled); D.goto('go')
    new = 0x08000000 + put_script(r, D)
    pat = struct.pack('<I', cur); n = 0; pos = 0
    while True:
        pos = bytes(b).find(pat, pos)
        if pos < 0: break
        if not (cs <= pos < cs + 64 or new - 0x08000000 <= pos < new - 0x08000000 + 64):
            r.w32(pos, new); n += 1
        pos += 1
    assert n >= 1
    print('death_facing_fix: death script %#x -> %#x (%d references), fade %#x, old death %#x, mauled text %#x' % (cur, new, n, fade, old_death, mauled))

if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')

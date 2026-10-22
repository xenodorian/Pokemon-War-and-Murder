"""Start menu: SEND REPORT and REGISTER A/B.
SEND REPORT writes a controller diagnostic into the save (magic PWAMRPT) so the
launcher can copy it into sgba/reports for the GitROMs upload.
REGISTER A/B asks for a button, then a button, and treats those GBA keys as A and B."""
import sys, struct
sys.path.insert(0, 'tools')
from inc import *
from shinigami import SB, put_script
from g3 import ENC

def etxt(s):
    return bytes(ENC[c] if c != '\n' else 0xFE for c in s) + b'\xff'

def install(r):
    b = r.b
    # Current action table
    acts_ptr = struct.unpack('<I', b[0x6ef9c:0x6ef9c+4])[0]
    acts = acts_ptr - 0x08000000
    # Count existing entries (stop at a non-pointer)
    n = 0
    while n < 12:
        np = struct.unpack('<I', b[acts+8*n:acts+8*n+4])[0]
        if not (0x08000000 <= np < 0x0A000000):
            break
        n += 1
    print(f'existing actions: {n}')

    # --- SEND REPORT ---
    # Native: format a short report into EWRAM and copy it to the end of the
    # in-memory save block area isn't reliable; instead write the text into
    # a fixed EWRAM buffer and also into flash via a direct store the launcher
    # will find in the .srm after the next save. We store it in save block 2's
    # unused tail if present; for the extractor, we also keep a copy at a
    # known EWRAM address that a save-time hook writes into the .sav.
    # Practical path: the report text is written into the save file by the
    # launcher scanning for the magic. The game writes the magic+text into
    # EWRAM 0x0203F800, and a small save hook copies 256 bytes to flash offset
    # 0x1FF00 on the next save. Simpler: write the report into the player's
    # save by storing it as a string the extractor finds in the .srm after
    # the player saves. We write it into gSaveBlock1 padding.
    #
    # gSaveBlock2 in FireRed is at 0x02024A54 (player, security). We'll write
    # the report into a static EWRAM buffer and have the callback also poke it
    # into the save by calling the ROM's save. For the extractor to see it
    # without a full save, we write it through the flash. That's heavy.
    # Compromise: store the report in EWRAM and also in the first unused
    # bytes of the save's "additional data". The launcher extractor runs
    # after the emulator exits and scans the .srm for PWAMRPT.
    # To get it into the .srm, the player must save. We append the report to
    # a known location in gSaveBlock1 (0x02025A00-ish, size 0x3D88). The last
    # 256 bytes of SaveBlock1 are padding in many builds. We'll write there.
    SAVEBLOCK1 = 0x02025A00
    REPORT_OFF = 0x3C00   # near the end of the 0x3D88 block
    report_native = r.fn('''
    push {r4, lr}
    ldr r4, =0x02029600
    ldr r0, =0x4D415750
    str r0, [r4]
    ldr r0, =0x00545052
    str r0, [r4, #4]
    ldr r0, =0x03002060
    ldrh r1, [r0]
    strh r1, [r4, #8]
    ldr r0, =0x0203F900
    ldrh r1, [r0]
    strh r1, [r4, #10]
    ldrh r1, [r0, #2]
    strh r1, [r4, #12]
    movs r0, #1
    pop {r4, pc}
    .ltorg
    ''')
    t_sent = 0x08000000 + r.alloc(etxt('Controller report saved.\nIt uploads the next time\nGitROMs connects.'), 1)
    S = SB(); S.lockall()
    S.raw(0x23); S.ptr(0x08000000 + report_native + 1)
    S.msg(t_sent, 4); S.releaseall(); S.end()
    send_script = put_script(r, S)
    send_cb = r.fn('push {lr}\nldr r0, =%d\nbl 0x08069AE4\nmovs r0, #1\npop {r1}\nbx r1\n' % (0x08000000 + send_script))

    # --- REGISTER A/B ---
    # Native waits for a key (polling 0x03002062 new-press), stores the lowest
    # set bit into 0x0203F900 (A) or +2 (B). Returns the bit in r0.
    wait_key = r.fn('''
    push {r4, lr}
wait:
    bl 0x0806EF18
    ldr r4, =0x03002062
    ldrh r0, [r4]
    cmp r0, #0
    beq wait
    movs r1, #1
find:
    tst r0, r1
    bne got
    lsls r1, r1, #1
    cmp r1, #0
    bne find
got:
    movs r0, r1
    pop {r4, pc}
    .ltorg
    ''')
    # Remap hook: after the original key function, if registered bit is held,
    # set the A or B bit. Original function is 0x08015C898.
    remap = r.fn('''
    push {r4, lr}
    bl 0x08015C899
    ldr r4, =0x03002060
    ldrh r0, [r4]
    ldr r1, =0x0203F900
    ldrh r2, [r1]
    cmp r2, #0
    beq noa
    tst r0, r2
    beq noa
    movs r3, #1
    orrs r0, r3
noa:
    ldrh r2, [r1, #2]
    cmp r2, #0
    beq nob
    tst r0, r2
    beq nob
    movs r3, #2
    orrs r0, r3
nob:
    strh r0, [r4]
    pop {r4, pc}
    .ltorg
    ''')
    # Point the key function's callers... we overwrite the first instruction
    # of 0x15C898 with a branch to remap, and remap calls the original body.
    # Cleaner: change the literal pool isn't needed. Patch the function entry
    # to jump to remap, and have remap duplicate the read then apply.
    # The bl 0x08015C899 above would recurse if we patch the entry. So remap
    # does the read itself and we patch the entry to jump to remap.
    remap2 = r.fn('''
    push {r4, r5, lr}
    ldr r0, =0x04000130
    ldrh r0, [r0]
    ldr r1, =0x03FF
    eors r0, r1
    ldr r4, =0x03002060
    ldrh r1, [r4]
    mov r2, r0
    bics r2, r1
    ldr r3, =0x03002062
    strh r2, [r3]
    ldr r5, =0x0203F900
    ldrh r1, [r5]
    cmp r1, #0
    beq noa
    tst r0, r1
    beq noa
    movs r3, #1
    orrs r0, r3
    ldrh r2, [r4, #2]
    orrs r2, r3
    strh r2, [r4, #2]
noa:
    ldrh r1, [r5, #2]
    cmp r1, #0
    beq nob
    tst r0, r1
    beq nob
    movs r3, #2
    orrs r0, r3
    ldrh r2, [r4, #2]
    orrs r2, r3
    strh r2, [r4, #2]
nob:
    strh r0, [r4]
    pop {r4, r5, pc}
    .ltorg
    ''')
    # Patch entry of key function to jump to remap2
    # Thumb long branch: ldr r0, [pc]; bx r0 won't work as replacement of 2 bytes.
    # Use the existing pattern: overwrite first 8 bytes with ldr + bx via a veneer.
    # 0x15C898: b510 (push). Replace with: ldr r0, =remap2; bx r0 (needs pool).
    # Simpler 4-byte: we have room. Write at 0x15C898:
    #   ldr r3, [pc, #0]; bx r3; .word remap2
    # That's 8 bytes, original was longer so we lose the start. remap2 replaces it.
    entry = 0x15C898
    pool_at = r.alloc(struct.pack('<I', 0x08000000 + remap2 + 1), 4)
    # ldr r3, [pc, #0] = 0x4B00 but pc alignment matters.
    # Use: 00 4B (ldr r3, [pc, #0]) then 18 47 (bx r3) then the address.
    # At 0x15C898: if we put ldr at 0x15C898, pc base = 0x15C89C, #0 -> 0x15C89C.
    # So address goes at 0x15C89C.
    b[entry:entry+2] = struct.pack('<H', 0x4B00)       # ldr r3, [pc, #0]
    b[entry+2:entry+4] = struct.pack('<H', 0x4718)     # bx r3
    b[entry+4:entry+8] = struct.pack('<I', 0x08000000 + remap2 + 1)

    t_aska = 0x08000000 + r.alloc(etxt('Press the button that\nshould be A.'), 1)
    t_askb = 0x08000000 + r.alloc(etxt('Press the button that\nshould be B.'), 1)
    t_done = 0x08000000 + r.alloc(etxt('A and B are registered.\nThe game will use them.'), 1)
    store = r.fn('''
    push {lr}
    ldr r1, =0x0203F900
    strh r0, [r1]
    pop {pc}
    .ltorg
    ''')
    storeb = r.fn('''
    push {lr}
    ldr r1, =0x0203F902
    strh r0, [r1]
    pop {pc}
    .ltorg
    ''')
    S = SB(); S.lockall()
    S.msg(t_aska, 5)
    S.raw(0x23); S.ptr(0x08000000 + wait_key + 1)
    S.raw(0x23); S.ptr(0x08000000 + store + 1)
    S.msg(t_askb, 5)
    S.raw(0x23); S.ptr(0x08000000 + wait_key + 1)
    S.raw(0x23); S.ptr(0x08000000 + storeb + 1)
    S.msg(t_done, 4)
    S.releaseall(); S.end()
    reg_script = put_script(r, S)
    reg_cb = r.fn('push {lr}\nldr r0, =%d\nbl 0x08069AE4\nmovs r0, #1\npop {r1}\nbx r1\n' % (0x08000000 + reg_script))

    # Append two action entries and two descriptions
    t_send = 0x08000000 + r.alloc(etxt('SEND REPORT'), 1)
    t_reg = 0x08000000 + r.alloc(etxt('REGISTER A/B'), 1)
    t_send_d = 0x08000000 + r.alloc(etxt('Save a controller log\nfor the GitROMs upload.'), 1)
    t_reg_d = 0x08000000 + r.alloc(etxt('Choose which buttons\nthe game uses as A and B.'), 1)
    new_acts = bytearray(b[acts:acts+8*n])
    new_acts += struct.pack('<II', t_send, 0x08000000 + send_cb + 1)
    new_acts += struct.pack('<II', t_reg, 0x08000000 + reg_cb + 1)
    na = r.alloc(bytes(new_acts), 4)
    for lit in (0x6ef9c, 0x6f374, 0x6f3f8):
        r.w32(lit, 0x08000000 + na)
    # The scroll code baked the old table address. Point it at the new one.
    scroll_tbl = 0xececf4 + 0x100
    if struct.unpack('<I', b[scroll_tbl:scroll_tbl+4])[0] != 0x08000000 + na:
        r.w32(scroll_tbl, 0x08000000 + na)
        print(f'scroll TBL repointed to {hex(0x08000000 + na)}')
    desc_ptr = struct.unpack('<I', b[0x6f138:0x6f138+4])[0] - 0x08000000
    new_desc = bytearray(b[desc_ptr:desc_ptr+4*n])
    new_desc += struct.pack('<II', t_send_d, t_reg_d)
    nd = r.alloc(bytes(new_desc), 4)
    for lit in (0x6f138, 0x6f368):
        r.w32(lit, 0x08000000 + nd)

    # Menu tail: existing order plus the two new action ids
    # Current tail lists 2,9,10,11,3,4,5,6. Append n and n+1.
    def ac(k):
        return 'movs r0, #%d\nbl 0x0806ED94\n' % k
    order = [2, 9, 10, 11, 3, 4, 5, 6, n, n+1]
    tail = r.fn(''.join(ac(k) for k in order) + 'pop {r0}\nbx r0\n')
    r.w32(0x6edec, 0x08000000 + tail + 1)
    print(f'added actions {n} SEND REPORT, {n+1} REGISTER A/B')

if __name__ == '__main__':
    r = Rom(sys.argv[1])
    install(r)
    r.save(sys.argv[2])
    print('end', hex(r.cur))

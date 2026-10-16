"""Adds three move slots to the engine and gives Hitmonchan its learnset (usage: moves_extend.py IN.gba OUT.gba)
 - the move count grows from 355 to 358: 355 BITCH SLAP, 356 BALL THROW, 357 HYPERPUNCH
 - the move data table (12 bytes a move), the name table (13 bytes) and the description pointers (4 bytes, move-1) are moved to free space
   and every 4-aligned pointer to them is repointed; the battle animation table (4 bytes a move, one pointer to it) is moved the same way
 - the two code literals that hold the move count as a sentinel (0x40238, 0x933e8) go from 355 to 358; the other literal 355 words are flag or
   data values, not move IDs, and are left alone (checked: 0x163 is FLAG_HIDE_ROUTE25_TM43 in include/constants/flags.h)
 - new moves: BITCH SLAP and BALL THROW copy TACKLE's record (fighting type, 30 and 50 power, 100 accuracy); HYPERPUNCH copies HYPER BEAM's record
   (recharge effect, 150 power, 100 accuracy, 5 PP). All three use TACKLE's battle animation for now.
 - Hitmonchan (107) and the stand-in (255, LEAF) get the same learnset (levels from the Hitmonchan spec)"""
import sys,os,struct
sys.path.insert(0,'/home/claude/work/tools')
from inc import Rom
import species_add as SA

MD=0x250c04; MN=0x247094; MDESC=0x4886e8; ANIM=0x1c68f4; LEARN=0x25d7b4
OLD_N=355; NEW_N=358; TACKLE=33; HYPERBEAM=63
BITCH_SLAP,BALL_THROW,HYPERPUNCH=355,356,357
FIGHTING=1
SENTINEL_SITES=(0x40238,0x933e8)

def repoint(b,old,new):
    pat=struct.pack('<I',0x08000000+old); n=0
    for o in range(0,len(b)-3,4):
        if b[o:o+4]==pat: b[o:o+4]=struct.pack('<I',0x08000000+new); n+=1
    return n

def record(b,m): return bytearray(b[MD+12*m:MD+12*m+12])

def apply(r):
    b=r.b
    assert struct.unpack('<I',b[0x40238:0x4023c])[0]==0x163 and struct.unpack('<I',b[0x933e8:0x933ec])[0]==0x163, 'sentinel sites moved'
    # 1. move data
    tk=record(b,TACKLE); hb=record(b,HYPERBEAM)
    bs=bytearray(tk); bs[1]=30; bs[2]=FIGHTING; bs[3]=100; bs[4]=20
    bt=bytearray(tk); bt[1]=50; bt[2]=FIGHTING; bt[3]=100; bt[4]=15
    hp=bytearray(hb); hp[1]=150; hp[2]=FIGHTING; hp[3]=100; hp[4]=5
    newdata=bytes(b[MD:MD+12*OLD_N])+bytes(bs)+bytes(bt)+bytes(hp)
    assert len(newdata)==12*NEW_N
    md_new=r.alloc(newdata,4)
    # 2. names (13 bytes, 0xFF padded)
    names=bytes(b[MN:MN+13*OLD_N])
    for txt in ('BITCH SLAP','BALL THROW','HYPERPUNCH'):
        n=SA.text(txt); assert len(n)<=13; names+=n+b'\xff'*(13-len(n))
    mn_new=r.alloc(names,4)
    # 3. descriptions: pointer table of 354 entries (move-1), three new texts
    descs=bytes(b[MDESC:MDESC+4*(OLD_N-1)])
    for txt in ('A hard slap that\nstings the foe.','A ball thrown hard\nat the foe.','A massive punch. The\nuser must rest next turn.'):
        descs+=struct.pack('<I',0x08000000+r.alloc(SA.text(txt),1))
    md_desc_new=r.alloc(descs,4)
    # 4. battle animations: TACKLE's entry for the three new moves
    anims=bytes(b[ANIM:ANIM+4*OLD_N])
    tk_anim=anims[4*TACKLE:4*TACKLE+4]
    anims+=tk_anim*3
    anim_new=r.alloc(anims,4)
    # 5. repoint every reference to the old tables
    pp_refs=repoint(b,MD+4,md_new+4)    # code that reads gBattleMoves[move].pp through a pointer to the pp field (without this the new moves started with 1 PP)
    counts=(repoint(b,MD,md_new),repoint(b,MN,mn_new),repoint(b,MDESC,md_desc_new),repoint(b,ANIM,anim_new))
    assert counts[0]>0 and counts[1]>0 and counts[2]>0 and counts[3]>0, counts
    # 6. code sentinels
    for o in SENTINEL_SITES: r.w32(o,NEW_N)
    # 6b. battle text: a move id above 354 printed 'a FIGHTING move' instead of the name (three compares in battle_message.c: movs r,#0xb1; lsls r,r,#1; cmp; bls/bhi).
    #     New limit: r = 0xb3 << 1 = 358 and the branch is made strict (bls -> bcc, bhi -> bcs), so ids up to 357 print their names.
    for o,br_old,br_new in ((0xd75fc,0xd9,0xd3),(0xd7e96,0xd8,0xd2),(0xd7eae,0xd9,0xd3)):
        assert b[o]==0xb1 and b[o+1]==0x20 and b[o+2]==0x40 and b[o+3]==0x00 and b[o+4:o+6]==b'\x81\x42', hex(o)   # movs rN,#0xb1 ; lsls rN,rN,#1
        assert b[o+7]==br_old, hex(o)
        b[o]=0xb3; b[o+7]=br_new
    # 7. learnsets: Hitmonchan's list from the spec (levels, moves)
    spec=[(1,BITCH_SLAP),(7,183),(10,BALL_THROW),(13,228),(15,140),(18,131),(20,279),(21,129),
          (23,8),(24,9),(25,7),(27,327),(30,247),(33,5),(35,188),(37,68),(40,121),(45,HYPERPUNCH)]
    data=b''.join(struct.pack('<H',(l<<9)|m) for l,m in spec)+b'\xff\xff'
    for sp in (107,255):
        r.w32(LEARN+4*sp,0x08000000+r.alloc(data,2))
    print('moves_extend: refs repointed',counts,'pp-field refs',pp_refs,'tables at',hex(md_new),hex(mn_new),hex(md_desc_new),hex(anim_new))

if __name__=='__main__':
    r=Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')

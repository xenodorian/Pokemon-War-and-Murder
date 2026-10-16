"""Battle animations for the Leaf throw moves (usage: anim_throw.py IN.gba OUT.gba). Runs after moves_extend.py.
Symbol addresses come from pret/pokefirered built as FireRed 1.0 (sha1 41cb23d8..., matches this ROM's code): see docs/ANIMATION_NOTES.md.
 - two new battle animation sprites: tag 10289 = Leaf's five throw frames (64x64 each, sheet 5 frames), tag 10290 = the Poke Ball (16x16)
 - gBattleAnimPicTable and gBattleAnimPaletteTable (289 entries) are moved to free space with 291 entries and every reference is repointed
   (exact pointers, pointers with an entry offset, and the loadspritegfx literals that hold table - 10000*8)
 - BALL THROW (356) gets its own animation script: attacker hidden, Leaf throws (frame timing from leaf_throw_anims/TIMING.md), the ball flies from t=26 to t=44,
   then the Tackle hit (hit splat, target shake)
Test positions are tuned in the emulator (tools/anim_test.py)."""
import sys,os,struct
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(1,'/home/claude/work/tools')
from inc import Rom
from PIL import Image
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART=os.path.join(ROOT,'leaf_throw_anims','frames')
PIC=0x3acc08; PAL=0x3ad510; N_OLD=289
TAG_LEAF=10289; TAG_BALL=10290
G=lambda a:a-0x08000000
SYM=dict(DESTROY_VTASK=0x08072760,ATTACKER=0x02037f1a,ARGS=0x02037f02,MONS=0x02023be4,OAM64=0x083ac9e0,DUMMY_ANIMS=0x08231cf0,DUMMY_AFF=0x08231cfc,ON_MON_POS=0x08075d9c,EGG_THROW=0x083e3d00,HITSPLAT=0x083e7c08,SHAKE=0x080989f8,SCRIPTING=0x02037f16,WINDUP=0x0809949d,SLIDEBACK=0x083d4e84,TASKS=0x03005090,SPRITES=0x0202063c,BSPRITEIDS=0x02023d44)
IMPACT=10135
SYM_SHADOWBALL=0x083e7608  # gShadowBallSpriteTemplate
LEN={0:3,1:3,4:2,5:1,6:1,7:1,8:1,9:3,10:2,11:2,12:3,13:1,14:5,15:1,16:4,17:9,18:6,19:5,20:2,21:1,22:1,23:1,24:2,25:4,26:2,27:7,28:6,29:5,30:3,32:1,33:8,34:2,35:2,36:5,37:4,38:7,39:7,40:2,41:1,42:2,43:2,44:2,45:2,46:2,47:1}
# tunables (relative to the attacker position, see anim_test.py)
LEAF_OFF=(int(os.environ.get('LEAF_X','8')),int(os.environ.get('LEAF_Y','-24')))
BALL_START=(int(os.environ.get('BALL_X','30')),int(os.environ.get('BALL_Y','-30')))

def rgb15(c): return (c[0]>>3)|((c[1]>>3)<<5)|((c[2]>>3)<<10)
def lz(data):   # literal-only LZ77 (type 0x10): valid stream, no matches
    out=bytearray(struct.pack('<I',0x10|(len(data)<<8)))
    for i in range(0,len(data),8):
        out.append(0); out+=data[i:i+8]
    while len(out)%4: out.append(0)
    return bytes(out)
def tiles(img,w,h):   # img: list of palette indexes row-major; returns 4bpp tiles in 1D order
    out=bytearray()
    for ty in range(h//8):
        for tx in range(w//8):
            for y in range(8):
                for x in range(0,8,2):
                    a=img[(ty*8+y)*w+tx*8+x]; b=img[(ty*8+y)*w+tx*8+x+1]
                    out.append(a|(b<<4))
    return bytes(out)

def leaf_sheet():
    frames=[Image.open(os.path.join(ART,'leaf_frame%d.png'%i)).convert('RGBA') for i in range(5)]
    pal=[]
    for im in frames:
        for p in im.getdata():
            if p[3]>0 and p[:3] not in pal: pal.append(p[:3])
    assert len(pal)<=15,len(pal)
    sheet=bytearray()
    for im in frames:
        idx=[0 if p[3]==0 else pal.index(p[:3])+1 for p in im.getdata()]
        sheet+=tiles(idx,64,64)
    pw=b''.join(struct.pack('<H',rgb15(c)) for c in [(0,0,0)]+pal)
    pw+=b'\0\0'*(16-len(pal)-1)
    return bytes(sheet),pw
def ball_sheet():
    im=Image.open(os.path.join(ART,'ball_sprite','poke.png')).crop((0,0,16,16))
    idx=list(im.getdata())
    pal=open(os.path.join(ART,'ball_sprite','poke.gbapal'),'rb').read()
    return tiles(idx,16,16),pal

def script(*cmds): return b''.join(cmds)
def loadgfx(tag): return b'\x00'+struct.pack('<H',tag)
def createsprite(tmpl,target,sub,*args): return b'\x02'+struct.pack('<I',tmpl)+bytes([(0x80 if target else 0)|sub,len(args)])+b''.join(struct.pack('<h',a) for a in args)
def task(addr,prio,*args): return b'\x03'+struct.pack('<I',addr)+bytes([prio,len(args)])+b''.join(struct.pack('<h',a) for a in args)
def delay(n): return bytes([4,n])
WAIT=b'\x05'; END=b'\x08'
def sewithpan(se,pan): return b'\x19'+struct.pack('<Hb',se,pan)
def monbg(b): return bytes([0x0a,b])
def clearmonbg(b): return bytes([0x0b,b])
def setalpha(a,b): return bytes([0x0c,a,b])
BLENDOFF=b'\x0d'
def invisible(b): return bytes([0x2b,b])
def visible(b): return bytes([0x2c,b])

def apply(r):
    b=r.b
    # 1. sprite sheets and palettes
    ls,lp=leaf_sheet(); bs,bp=ball_sheet()
    sheets=[(r.alloc(lz(ls),4),len(ls),TAG_LEAF),(r.alloc(lz(bs),4),len(bs),TAG_BALL)]
    pals=[(r.alloc(lz(lp),4),TAG_LEAF),(r.alloc(lz(bp),4),TAG_BALL)]
    # 2. relocate the two tables (+2 entries)
    pic=bytes(b[PIC:PIC+8*N_OLD])+b''.join(struct.pack('<IHH',0x08000000+a,sz,t) for a,sz,t in sheets)
    pal=bytes(b[PAL:PAL+8*N_OLD])+b''.join(struct.pack('<IHH',0x08000000+a,t,0) for a,t in pals)
    pic_new=r.alloc(pic,4); pal_new=r.alloc(pal,4)
    n=0
    assert r.r32(0x728b8)==0x08000000+PIC-0x13880 and r.r32(0x728bc)==0x08000000+PAL-0x13880
    r.w32(0x728b8,0x08000000+pic_new-0x13880); r.w32(0x728bc,0x08000000+pal_new-0x13880); n+=2     # loadspritegfx literals (table - 10000*8)
    for o in range(0,0x400000,4):
        if o in (0x728b8,0x728bc): continue
        v=struct.unpack_from('<I',b,o)[0]
        for old,new_ in ((PIC,pic_new),(PAL,pal_new)):
            base=0x08000000+old
            if base<=v<base+8*N_OLD and (v-base)%8==0:      # exact and entry-offset pointers (an end pointer is not a reference)
                r.w32(o,v-old+new_); n+=1
    assert n>=10,n
    # 3. sprite templates
    anim_cmds=b''.join(struct.pack('<I',(t<<0)|(d<<16)) for t,d in ((64*1,20),(64*2,6),(64*3,6),(64*4,24),(64*0,1)))+struct.pack('<I',0xFFFF)
    cmds=r.alloc(anim_cmds,4)
    table=r.alloc(struct.pack('<I',0x08000000+cmds),4)
    tleaf=r.alloc(struct.pack('<HHIIIII',TAG_LEAF,TAG_LEAF,SYM['OAM64'],0x08000000+table,0,SYM['DUMMY_AFF'],SYM['ON_MON_POS']|1),4)
    egg=bytearray(b[G(SYM['EGG_THROW']):G(SYM['EGG_THROW'])+24]); struct.pack_into('<HH',egg,0,TAG_BALL,TAG_BALL)
    tball=r.alloc(bytes(egg),4)
    T=lambda a:0x08000000+a
    # show-attacker task: Leaf's throw sprite ends at t=57 (frame 0 holds 1 frame and the sprite is destroyed), so at that tick the hidden attacker battler
    # (the same idle pose) is made visible again; otherwise Leaf vanishes for the rest of the move (reference GIFs keep her on screen)
    showfn=r.fn("""
        push {r4,lr}
        mov r4,r0
        ldr r1,=%d
        movs r2,#0x28
        muls r2,r0
        adds r1,r1,r2
        ldrh r2,[r1,#10]
        cmp r2,#0
        bne started
        movs r2,#1
        strh r2,[r1,#10]
        ldr r3,=%d
        ldrh r2,[r3]
        strh r2,[r1,#8]
    started:
        ldrh r2,[r1,#8]
        subs r2,#1
        strh r2,[r1,#8]
        bne out
        ldr r2,=%d
        ldrb r2,[r2]
        ldr r3,=%d
        ldrb r2,[r3,r2]
        movs r3,#0x44
        muls r2,r3
        ldr r3,=%d
        adds r2,r2,r3
        adds r2,#0x3e
        ldrb r3,[r2]
        movs r0,#4
        bics r3,r0
        strb r3,[r2]
        mov r0,r4
        ldr r3,=%d
        pop {r4}
        pop {r1}
        mov lr,r1
        bx r3
    out:
        pop {r4}
        pop {r0}
        bx r0
    """%(SYM['TASKS'],SYM['ARGS'],SYM['ATTACKER'],SYM['BSPRITEIDS'],SYM['SPRITES'],SYM['DESTROY_VTASK']|1))
    print('showfn',hex(showfn))
    SHOWT=task(0x08000000+showfn|1,2,57)
    # 4. Ball Throw script
    s=script(loadgfx(TAG_LEAF),loadgfx(TAG_BALL),loadgfx(IMPACT),
        monbg(1),setalpha(12,8),invisible(0),
        createsprite(T(tleaf),0,2,LEAF_OFF[0],LEAF_OFF[1],0,0),SHOWT,
        delay(26),sewithpan(54,-64),
        createsprite(T(tball),1,2,BALL_START[0],BALL_START[1],0,0,18,-34),
        delay(18),
        createsprite(SYM['HITSPLAT'],0,2,0,0,1,2),
        task(SYM['SHAKE']|1,2,1,3,0,6,1),
        sewithpan(132,63),
        WAIT,visible(0),clearmonbg(1),BLENDOFF,END)
    sa=r.alloc(s,1)
    # 5. point move 356 at it
    ANIM=None
    tk=struct.unpack_from('<I',b,0x1c68f4+4*33)[0]
    for o in range(0,0x400000,4):
        v=struct.unpack_from('<I',b,o)[0]-0x08000000
        if 0xA00000<=v<len(b)-4*358 and struct.unpack_from('<I',b,v+4*33)[0]==tk and struct.unpack_from('<I',b,v+4*356)[0]==tk: ANIM=v; break
    assert ANIM
    # 4b. Bitch Slap (355): Leaf throws, then the Tackle hit at t=32 (TIMING.md)
    s2=script(loadgfx(TAG_LEAF),loadgfx(IMPACT),monbg(1),setalpha(12,8),invisible(0),
        createsprite(T(tleaf),0,2,LEAF_OFF[0],LEAF_OFF[1],0,0),SHOWT,delay(32),
        createsprite(SYM['HITSPLAT'],0,2,0,0,1,2),task(SYM['SHAKE']|1,2,1,3,0,6,1),sewithpan(132,63),
        WAIT,visible(0),clearmonbg(1),BLENDOFF,END)
    slap=r.alloc(s2,1)
    # 4c. existing throw moves: Leaf's frames are added only when the attacker is Hitmonchan (107) or LEAF (255); everyone else keeps the original animation
    check=r.fn("""
        push {lr}
        ldr r1,=%d
        ldrb r1,[r1]
        movs r2,#0x58
        muls r1,r2
        ldr r2,=%d
        adds r1,r1,r2
        ldrh r1,[r1]
        movs r2,#0
        cmp r1,#107
        beq yes
        cmp r1,#255
        bne done
    yes:
        movs r2,#1
    done:
        ldr r3,=%d
        strh r2,[r3,#14]
        movs r1,#0
        cmp r2,#0
        beq noturn
        ldr r1,=%d
        ldrb r1,[r1]
        cmp r1,#0
        beq noturn
        movs r1,#1
    noturn:
        strh r1,[r3,#12]
        ldr r3,=%d
        pop {r1}
        mov lr,r1
        bx r3
    """%(SYM['ATTACKER'],SYM['MONS'],SYM['ARGS'],SYM['SCRIPTING'],SYM['DESTROY_VTASK']|1))
    def cmd_len(sc,p):
        op=sc[p]
        if op in (2,3): return 7+2*sc[p+6]
        if op==0x1f: return 6+2*sc[p+5]
        return LEN[op]
    def body_of(move):
        ptr=struct.unpack_from('<I',b,ANIM+4*move)[0]; o=ptr-0x08000000; cmds=[]
        while True:
            n=cmd_len(b,o); cmds.append((o,bytes(b[o:o+n])))
            if b[o]==0x08: break
            o+=n
        return ptr,[c for _,c in cmds[:-1]]
    from_map=SYM_SHADOWBALL
    wrapped={140:26,121:26,247:None,129:26,131:26,188:26}
    skipsc=r.alloc(END,1)
    for mv,dl in wrapped.items():
        orig,cmds=body_of(mv)
        if mv==131:   # SPIKE CANNON: drop the attacker wind-up lunge, its wait and the slide-back sprite so the volley starts at t=26 (TIMING.md)
            f=[];skip_wait=False
            for c in cmds:
                if c[0]==3 and struct.unpack_from('<I',c,1)[0]==SYM['WINDUP']: skip_wait=True; continue
                if skip_wait and c[0]==5: skip_wait=False; continue
                if c[0]==2 and struct.unpack_from('<I',c,1)[0]==SYM['SLIDEBACK']: continue
                f.append(c)
            cmds=f
        out=[loadgfx(TAG_LEAF)] if dl is None else [loadgfx(TAG_LEAF),invisible(0)]   # Shadow Ball: Leaf stays visible during the tint, hide only when the throw starts
        leaf=createsprite(T(tleaf),0,2,LEAF_OFF[0],LEAF_OFF[1],0,0)
        if dl is not None: out+=[leaf,SHOWT,delay(dl)]
        for c in cmds:
            if dl is None and c[0]==2 and struct.unpack_from('<I',c,1)[0]==from_map: out.append(invisible(0)); out.append(leaf); out.append(SHOWT)
            out.append(c)
        if dl is None: assert leaf in out
        out+=[visible(0),END]
        lv=r.alloc(b''.join(out),1)
        multi=b'\x21'+bytes([6])+struct.pack('<hI',1,T(skipsc)) if mv in (131,140) else b''   # multi-hit: one round only, hits 2+ play no animation
        entry=r.alloc(task(T(check)|1,2)+multi+b'\x21'+bytes([7])+struct.pack('<hI',1,T(lv))+b'\x13'+struct.pack('<I',orig),1)
        r.w32(ANIM+4*mv,T(entry))
    r.w32(ANIM+4*356,0x08000000+sa); r.w32(ANIM+4*355,0x08000000+slap)
    print('anim_throw: refs repointed',n,'tables',hex(pic_new),hex(pal_new),'script',hex(sa))

if __name__=='__main__':
    r=Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')

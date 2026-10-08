# usage: gun.py in.gba out.gba
# Shoot / threaten / bless menu for defeated trainers, JRA troopers that refuse blessings, shoot back and pay out only when shot,
# and being shot: negative karma -> HELL (Giratina offers a soul sale), otherwise HEAVEN (Arceus offers forgiveness), both returning to Pallet Town.
import sys,struct,subprocess,json,os
sys.path.insert(0,'/home/claude/work/tools')
from inc import *
import leg1,gfx
from leg1 import r32,header,enc,GROUPS
from shinigami import SB,put_script
import numpy as np
import gun_art as art
W='/home/claude/work/gun'
T=0x798790
ITEM_GLOCK,ITEM_9MM,BLESS_ITEM=52,53,56
SE_SHOT=347
HELL=(2,68)
PALLET=(3,0,11,10)                     # middle of Pallet Town
GIRATINA_AT=(11,21)
KARMA_CHECK=None
def etxt(s): return bytes(leg1.ENC[c] for c in s)+b'\xff'
def T_(r,s): return 0x08000000+r.alloc(enc(s),1)

# ---------------------------------------------------------------- overworld graphics (two 64x64 objects with their own palettes)
def add_gfx(r,sprites,tags):
    b=r.b
    pt=r32(r,0x5f4d8)-0x08000000; n=0
    while struct.unpack('<H',b[pt+8*n+4:pt+8*n+6])[0]!=0x11ff: n+=1
    ents=bytearray(b[pt:pt+8*n]); used={struct.unpack('<H',b[pt+8*i+4:pt+8*i+6])[0] for i in range(n)}
    gt=r32(r,0x5f2f4)-0x08000000; mx=b[0x5f2e0]
    src=r32(r,gt+4*108)-0x08000000            # an existing 64x64 object (same OAM, anims and size)
    assert struct.unpack('<6H',b[src:src+12])[4:6]==(64,64)
    newinfo=[];ids=[]
    for (frames,pal,seq),tag in zip(sprites,tags):
        assert tag not in used
        cols=[(255,0,255)]+pal+[(0,0,0)]*(15-len(pal))
        pa=r.alloc(gfx.rgb_to_pal(cols),4); ents+=struct.pack('<IHH',0x08000000+pa,tag,0)
        tiles=[r.alloc(gfx.pixels_to_tiles([[int(v) for v in row] for row in f]),4) for f in frames]
        info=bytearray(b[src:src+36]); info[2:4]=struct.pack('<H',tag); info[4:6]=struct.pack('<H',0x11ff)
        if seq is None:
            imgt=r.alloc(b''.join(struct.pack('<IHH',0x08000000+tiles[0],2048,0) for _ in range(9)),4)
        else:
            imgt=r.alloc(b''.join(struct.pack('<IHH',0x08000000+t_,2048,0) for t_ in tiles),4)
            cyc=r.alloc(b''.join(struct.pack('<hBB',im_,du_,0) for im_,du_ in seq)+struct.pack('<hh',-2,0),4)
            atab=r.alloc(struct.pack('<I',0x08000000+cyc)*24,4)
            info[24:28]=struct.pack('<I',0x08000000+atab); info[12]|=0x40       # every facing plays the bob; inanimate objects keep animating
        info[0x1c:0x20]=struct.pack('<I',0x08000000+imgt)
        newinfo.append(r.alloc(bytes(info),4))
    ents+=bytes(b[pt+8*n:pt+8*n+8])
    npt=r.alloc(bytes(ents),4)
    for lit in (0x5f4d8,0x5f570,0x5f5c8): assert r32(r,lit)==0x08000000+pt,hex(lit); r.w32(lit,0x08000000+npt)
    tab=r.alloc(bytes(b[gt:gt+4*(mx+1)])+b''.join(struct.pack('<I',0x08000000+a) for a in newinfo),4)
    r.w32(0x5f2f4,0x08000000+tab); b[0x5f2e0]=mx+len(newinfo)
    return [mx+1+i for i in range(len(newinfo))]

# ---------------------------------------------------------------- map plumbing
def new_map(r,hdr_src,layout,events,name_id,scripts=None):
    """a new map in group 2 using header `hdr_src` as the base; returns (group,num)"""
    b=r.b
    hb=bytearray(b[hdr_src:hdr_src+28])
    hb[0:4]=struct.pack('<I',0x08000000+layout); hb[4:8]=struct.pack('<I',0x08000000+events)
    hb[8:12]=struct.pack('<I',0x08000000+(scripts or r.alloc(b'\x00',1))); hb[12:16]=bytes(4)
    hb[20]=name_id; hb[25]|=0x04
    g2=r32(r,GROUPS+8)-0x08000000; n=0
    while 0x08000000<=r32(r,g2+4*n)<0x0a000000: n+=1
    last=r32(r,g2+4*(n-1))-0x08000000; nl=struct.unpack('<H',b[last+18:last+20])[0]
    LT=r32(r,0x55194)-0x08000000
    assert r32(r,LT+4*(nl-1))==r32(r,last)
    tab=r.alloc(bytes(b[LT:LT+4*nl])+struct.pack('<I',0x08000000+layout),4); r.w32(0x55194,0x08000000+tab)
    hb[18:20]=struct.pack('<H',nl+1)
    h=r.alloc(bytes(hb),4)
    ntab=r.alloc(bytes(b[g2:g2+4*n])+struct.pack('<I',0x08000000+h),4); r.w32(GROUPS+8,0x08000000+ntab)
    return (2,n),h

def add_obj(r,g,n,x,y,gfxid,script,movement=0,rng=0,elev=3):
    h=header(r,g,n); ev=r32(r,h+4)-0x08000000
    no=r.b[ev]; po=r32(r,ev+4)-0x08000000 if no else 0
    ids=[r.b[po+24*i] for i in range(no)]
    t=bytearray(24); t[0]=max(ids)+1 if ids else 1; t[1]=gfxid; t[4:6]=struct.pack('<h',x); t[6:8]=struct.pack('<h',y)
    t[8]=elev; t[9]=movement; t[10]=rng; t[16:20]=struct.pack('<I',script)
    new=r.alloc((bytes(r.b[po:po+24*no]) if no else b'')+bytes(t),4); r.b[ev]=no+1; r.w32(ev+4,0x08000000+new)
    return t[0]

def warp_script(S,g,n,x,y):
    S.raw(0x39,g,n,0xff); S._add(struct.pack('<HH',x,y)); S.raw(0x27)

# ---------------------------------------------------------------- HEAVEN
def heaven(r,arceus_gfx,nat):
    b=r.b
    h=art.build_heaven(); h=art.reduce_tiles(h,960)
    ntile=len(h['tiles']); assert ntile<=1000
    tiles=[bytes(32)]                                    # tile 0: blank (upper metatile layer)
    for k,ix in h['tiles']:
        a=ix+1; bb=bytearray(32)
        for y in range(8):
            for x in range(4): bb[y*4+x]=int(a[y,2*x])|(int(a[y,2*x+1])<<4)
        tiles.append(bytes(bb))
    tiles+= [bytes(32)]*(1024-len(tiles))
    prim=b''.join(tiles[:640]); sec=b''.join(tiles[640:1024])
    pals=h['pals']
    def palbytes(slots):
        out=bytearray(512)
        for k in slots:
            cols=[(0,0,0)]+[tuple(int(v) for v in c) for c in pals[k]]
            out[k*32:k*32+32]=gfx.rgb_to_pal(cols)
        return bytes(out)
    ppal=palbytes(range(0,7)); spal=palbytes(range(7,13))
    # metatiles (one per distinct 16x16 block; the upper layer stays blank)
    tw,th=h['tw'],h['th']; ref=h['cellref']; pal_of=[h['tiles'][t][0] for t,_,_ in ref]
    def ent(i): t,hf,vf=ref[i]; return (t+1)|(hf<<10)|(vf<<11)|(pal_of[i]<<12)
    metas=[None]; midx={}; blocks=[[0]*art.BW for _ in range(art.BH)]
    for by in range(art.BH):
        for bx in range(art.BW):
            e=tuple(ent((2*by+dy)*tw+2*bx+dx) for dy in (0,1) for dx in (0,1))
            if e not in midx: midx[e]=len(metas); metas.append(e)
            blocks[by][bx]=midx[e]
    assert len(metas)<=640,len(metas)
    mt=b''.join(struct.pack('<8H',*(m+(0,0,0,0))) if m else bytes(16) for m in metas)
    attrs=b''.join(struct.pack('<I',0x20000000) for _ in metas)
    walk=art.walk_mask(h['img'])
    walk[:3,:]=False                                     # the sun
    for y in range(4,6):
        for x in (7,8,9): walk[y,x]=True                 # the light below it
    for x in (6,7,8,9,10): walk[3,x]=False              # Arceus' space: nobody walks under the sprite
    for y in range(art.BH-5,art.BH):                     # cloud floor along the bottom
        walk[y,:]=True
    # keep only the cloud area connected to the start
    start=(8,art.BH-3); assert walk[start[1],start[0]]
    seen={start}; q=[start]
    while q:
        x,y=q.pop()
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx,ny=x+dx,y+dy
            if 0<=nx<art.BW and 0<=ny<art.BH and walk[ny,nx] and (nx,ny) not in seen: seen.add((nx,ny)); q.append((nx,ny))
    ARC=(8,3); TALK=(8,4)
    assert TALK in seen,'Arceus cannot be reached'
    vals=[]
    for by in range(art.BH):
        for bx in range(art.BW):
            vals.append(blocks[by][bx]|(0 if (bx,by) in seen else 0x0400))
    best=None                                            # border: the plainest sky block
    for by in range(art.BH):
        for bx in range(art.BW):
            if (bx,by) in seen: continue
            v=h['img'][by*16:by*16+16,bx*16:bx*16+16].reshape(-1,3).astype(float).std(0).sum()
            if best is None or v<best[0]: best=(v,blocks[by][bx])
    bd=best[1]
    mp=r.alloc(b''.join(struct.pack('<H',v) for v in vals),4)
    border=r.alloc(struct.pack('<4H',bd,bd,bd,bd),4)
    def tset(tiles_bytes,pal,meta,at,second):
        ta=r.alloc(tiles_bytes,4); pa=r.alloc(pal,4); ma=r.alloc(meta,4); aa=r.alloc(at,4)
        return r.alloc(bytes([0,1 if second else 0,0,0])+struct.pack('<IIIII',0x08000000+ta,0x08000000+pa,0x08000000+ma,0,0x08000000+aa),4)
    ptset=tset(prim,ppal,mt,attrs,False)
    stset=tset(sec,spal,bytes(16),struct.pack('<I',0x20000000),True)
    lay=r.alloc(struct.pack('<IIIIII',art.BW,art.BH,0x08000000+border,0x08000000+mp,0x08000000+ptset,0x08000000+stset)+bytes([2,2,0,0]),4)
    # Arceus' talk script
    S=SB(); S.lockall()
    S.msg(T_(r,"ARCEUS: You were shot, and still your heart was good. The light has gathered you."),4)
    S.raw(0x0f,0); S.ptr(T_(r,"Accept forgiveness from ARCEUS?")); S.raw(0x09,5)
    S.compare(0x800d,0); S.goto_if(1,'no')
    S.msg(T_(r,"ARCEUS: Go, child. Walk gently."),4)
    S.raw(0x97,1)
    warp_script(S,*PALLET); S.releaseall(); S.end()
    S.lab('no'); S.msg(T_(r,"ARCEUS: The light will wait for you."),4); S.releaseall(); S.end()
    sc=0x08000000+put_script(r,S)
    ev=r.alloc(bytes([0,0,0,0])+struct.pack('<IIII',0,0,0,0),4)
    # Arceus' float: installed after every warp in and every load
    I=SB(); I.raw(0x23); I.ptr(nat['arc_install']); I.end(); isc=0x08000000+put_script(r,I)
    wt=r.alloc(struct.pack('<HHI',0x4001,0,isc)+struct.pack('<H',0),4)
    hms=r.alloc(bytes([4])+struct.pack('<I',0x08000000+wt)+bytes([5])+struct.pack('<I',isc)+b'\x00',4)
    # name
    NAME=0xad; r.w32(0x3f1cac+4*(NAME-0x58),0x08000000+r.alloc(leg1.enc('HEAVEN'),1))
    ch=header(r,*HELL)
    (g,n),hh=new_map(r,ch,lay,ev,NAME,scripts=hms)
    add_obj(r,g,n,ARC[0],ARC[1],arceus_gfx,sc,movement=8,rng=0)
    return (g,n),start,len(seen)

# ---------------------------------------------------------------- HELL
def hell(r,giratina_gfx):
    S=SB(); S.lockall()
    S.msg(T_(r,"GIRATINA: A fresh soul, fallen into my realm."),4)
    S.raw(0x0f,0); S.ptr(T_(r,"Sell your soul to GIRATINA?")); S.raw(0x09,5)
    S.compare(0x800d,0); S.goto_if(1,'no')
    S.msg(T_(r,"GIRATINA: Your soul is mine. Now get out of my sight."),4)
    S.raw(0x97,1)
    warp_script(S,*PALLET); S.releaseall(); S.end()
    S.lab('no'); S.msg(T_(r,"GIRATINA: Then burn, and think on what you have done."),4); S.releaseall(); S.end()
    sc=0x08000000+put_script(r,S)
    add_obj(r,*HELL,GIRATINA_AT[0],GIRATINA_AT[1],giratina_gfx,sc)


# ---------------------------------------------------------------- two fixes to earlier work
def fix_shot_sound(r):
    """the gunshot track ended with note + FINE, and FINE releases every sounding note at once (release time 0), so the shot was silent.
    The track now waits out the note (W96) before FINE."""
    b=r.b; new=r32(r,0x1dd11c)-0x08000000
    sp=r32(r,new+8*347)-0x08000000
    old=r32(r,sp+8)-0x08000000
    cur=bytes(b[old:old+12])
    if cur.endswith(bytes([0xff,60,0x7f,0xb0,0xb1])): return
    assert cur==bytes([0xbc,0x00,0xbb,0x3c,0xbd,0x00,0xbe,0x7f,0xff,60,0x7f,0xb1]),cur.hex()
    trk=r.alloc(bytes([0xbc,0x00,0xbb,0x3c,0xbd,0x00,0xbe,0x7f,0xff,60,0x7f,0xb0,0xb1]),4)
    r.w32(sp+8,0x08000000+trk)
def feather_black(r):
    """the black feather (object graphic 155) was drawn with the dark red / grey-blue entries of the shared slot-10 palette (indices 4, 5).
    It now uses the black / charcoal / grey entries (2, 10, 15), so it reads as a black feather. Done once; idempotent."""
    b=r.b; gt=r32(r,0x5f2f4)-0x08000000
    info=r32(r,gt+4*155)-0x08000000; im=r32(r,info+28)-0x08000000; tp=r32(r,im)-0x08000000
    px=gfx.tiles_to_pixels(bytes(b[tp:tp+128]),2,2); used={v for row in px for v in row}
    if used<={0,2,10,15}: return
    assert used<={0,2,4,5},used
    mp={0:0,2:2,4:10,5:15}
    out=[[mp[v] for v in row] for row in px]
    b[tp:tp+128]=gfx.pixels_to_tiles(out,2,2)


# ---------------------------------------------------------------- the police offer: runs in front of every trainer battle
BATTLE_START=0x1a4fc7        # special 34; waitmessage; waitbuttonpress   (then special 187 at 0x1a4fcc)
def police_offer(r,nat):
    b=r.b; assert bytes(b[BATTLE_START:BATTLE_START+5])==bytes([0x25,0x34,0x00,0x66,0x6d]),bytes(b[BATTLE_START:BATTLE_START+5]).hex()
    assert bytes(b[BATTLE_START+5:BATTLE_START+8])==bytes([0x25,0x87,0x01])
    T=lambda s: T_(r,s)
    S=SB()
    S.setvar(0x8004,0); S.raw(0x23); S.ptr(nat['deal_info']); S.compare(0x8007,1); S.goto_if(1,'offer')
    S.lab('go'); S.raw(0x25,0x34,0x00,0x66,0x6d); S.raw(0x05); S.ptr(0x08000000+BATTLE_START+5)
    S.lab('offer')
    S.msg(T("OFFICER: Hold it. I know your record. Plenty of civilians, and plenty of JRA soldiers."),4)
    S.raw(0x0f,0); S.ptr(T("Keep killing soldiers, stop killing civilians, and we look the other way on the murders. Deal?")); S.raw(0x09,5)
    S.compare(0x800d,0); S.goto_if(1,'refuse')
    S.raw(0x23); S.ptr(nat['deal_accept'])
    S.msg(T("OFFICER: Smart. Soldiers only from now on. This never happened."),4)
    S.compare(0x8006,0); S.goto_if(1,'stay')
    S.raw(0x29); S._add(struct.pack('<H',0x4AD)); S.raw(0x53); S._add(struct.pack('<H',0x800f))
    S.lab('stay'); S.raw(0x6b); S.end()
    S.lab('refuse')
    S.raw(0x23); S.ptr(nat['deal_refuse'])
    S.msg(T("OFFICER: You're making a mistake."),4)
    S.goto('go')
    sc=put_script(r,S)
    b[BATTLE_START:BATTLE_START+5]=bytes([0x05])+struct.pack('<I',0x08000000+sc)


def story_offers(r,nat):
    """the five story officers: after their kill check says 'fight', the offer is made first"""
    b=r.b; T=lambda s: T_(r,s)
    for site in nat['_story_sites']:
        k=bytes(b).rfind(bytes([0x6a,0x5a,0x60]),site-300,site); assert k>=0
        oid=b[k+3]|(b[k+4]<<8); assert 50<=oid<55,oid
        S=SB()
        S.raw(0x23); S.ptr(nat['kill_check2'])
        S.compare(0x8007,1); S.goto_if(5,'back')
        S.setvar(0x8004,oid); S.raw(0x23); S.ptr(nat['deal_info']); S.compare(0x8007,1); S.goto_if(5,'fight')
        S.msg(T("OFFICER: Hold it. I know your record. Plenty of civilians, and plenty of JRA soldiers."),4)
        S.raw(0x0f,0); S.ptr(T("Keep killing soldiers, stop killing civilians, and we look the other way on the murders. Deal?")); S.raw(0x09,5)
        S.compare(0x800d,0); S.goto_if(1,'refuse')
        S.raw(0x23); S.ptr(nat['deal_accept'])
        S.msg(T("OFFICER: Smart. Soldiers only from now on. This never happened."),4)
        S.release(); S.end()
        S.lab('refuse'); S.raw(0x23); S.ptr(nat['deal_refuse']); S.msg(T("OFFICER: You're making a mistake."),4)
        S.lab('fight'); S.setvar(0x8007,1)
        S.lab('back'); S.raw(0x05); S.ptr(0x08000000+site+5)
        sc=put_script(r,S)
        b[site:site+5]=bytes([0x05])+struct.pack('<I',0x08000000+sc)

# ---------------------------------------------------------------- HALL OF JUSTICE (its own room: marble, a red and gold carpet, the scales of justice, a display case per Captain)
import justice_art as JA
HW,HH=13,13
def hall_of_justice(r,nat):
    b=r.b; T=lambda s: T_(r,s)
    ch=header(r,2,67); clay=r32(r,ch)-0x08000000
    PRIM=r32(r,clay+16); SEC=r32(r,clay+20)-0x08000000
    def tb(a16):
        out=[]
        for ty in range(2):
            for tx in range(2):
                tt=a16[ty*8:ty*8+8,tx*8:tx*8+8]; bb=bytearray(32)
                for y in range(8):
                    for x in range(4): bb[y*4+x]=int(tt[y,2*x])|(int(tt[y,2*x+1])<<4)
                out.append(bytes(bb))
        return out
    tl=[];mts=[]
    for a in JA.TILES:
        base=len(tl); tl+=tb(a); mts.append([(7<<12)|(640+base+i) for i in range(4)]+[0,0,0,0])
    ta=r.alloc(gfx.lz_comp(b''.join(tl)),4)
    pal=bytearray(512)
    for i,c in enumerate([(0,0,0)]+JA.PAL): pal[7*32+2*i:7*32+2*i+2]=gfx.rgb_to_pal([c])
    pa=r.alloc(bytes(pal),4); ma=r.alloc(b''.join(struct.pack('<8H',*m) for m in mts),4)
    aa=r.alloc(b''.join(struct.pack('<I',0x20000000) for _ in mts),4)
    Hd=bytearray(b[SEC:SEC+24]); Hd[4:8]=struct.pack('<I',0x08000000+ta); Hd[8:12]=struct.pack('<I',0x08000000+pa); Hd[12:16]=struct.pack('<I',0x08000000+ma); Hd[20:24]=struct.pack('<I',0x08000000+aa); Hd[16:20]=bytes(4)
    sec=r.alloc(bytes(Hd),4)
    # layout
    grid=[[JA.F0 if (x+y)%2==0 else JA.F1 for x in range(HW)] for y in range(HH)]
    for x in range(HW): grid[0][x]=JA.WT; grid[1][x]=JA.WM
    for y in range(2,HH): grid[y][0]=JA.WM; grid[y][HW-1]=JA.WM
    grid[0][6]=JA.WEM
    for x in (3,9): grid[0][x]=JA.BT; grid[1][x]=JA.BB
    for x in range(4,9):
        for y in (2,3): grid[y][x]=JA.DAIS
    grid[2][6]=JA.STT; grid[3][6]=JA.STB
    for y in range(4,HH):
        grid[y][5]=JA.CL; grid[y][6]=JA.CC; grid[y][7]=JA.CR
    for y in (5,8): grid[y][3]=JA.COL; grid[y][HW-4]=JA.COL
    CASES=[(2,y) for y in (3,5,7,9,11)]+[(HW-3,y) for y in (3,5,7,9,11)]
    for x,y in CASES: grid[y][x]=JA.CAB
    grid[HH-1][6]=JA.MAT
    vals=[]
    for y in range(HH):
        for x in range(HW):
            k=grid[y][x]; vals.append((640+k)|(0x0400 if k in JA.BLOCKED else 0x3000))
    blocks=r.alloc(b''.join(struct.pack('<H',v) for v in vals),4)
    wb=640+JA.WM
    border=r.alloc(struct.pack('<4H',wb|0x400,wb|0x400,wb|0x400,wb|0x400),4)
    lay=r.alloc(struct.pack('<IIIIII',HW,HH,0x08000000+border,0x08000000+blocks,PRIM,0x08000000+sec)+bytes([2,2,0,0]),4)
    # ---- the ceremony
    S=SB(); S.lockall(); S.raw(0xc7,2); S.setvar(0x4001,1)
    mv_up=0x08000000+r.alloc(bytes([0x11]*6+[0xfe]),1)
    S.raw(0x4f); S._add(struct.pack('<H',0xff)); S.ptr(mv_up); S.raw(0x51); S._add(struct.pack('<H',0))
    S.raw(0x28); S._add(struct.pack('<H',0x14))
    S.msg(T("COMMISSIONER: Stop there, and let me look at you. So you are the one who brought down GENERAL GORE."),4)
    S.msg(T("COMMISSIONER: Ten bases fell, and ten Captains with them. Every case in this hall holds the record of one of them."),4)
    S.raw(0x23); S.ptr(nat['lib_text']); S.compare(0x8007,0); S.goto_if(1,'none')
    S.msg(0x08000000+r.alloc(leg1.enc('COMMISSIONER: You put ')[:-1]+b'\xfd\x02'+leg1.enc(' JRA soldiers in the ground. KANTO will not forget that, and neither will this hall.'),1),4); S.goto('go')
    S.lab('none'); S.msg(T("COMMISSIONER: And you ended it without leaving a single soldier dead. KANTO noticed that too."),4)
    S.lab('go')
    S.msg(T("COMMISSIONER: The League keeps its Hall of Fame. This is the HALL OF JUSTICE, for the ones who ended a war. Your team stands here beside the ten medals."),4)
    S.msg(T("COMMISSIONER: Stand ready. Your team goes into the roll, one by one."),4)
    # the induction: each POK\u00e9MON on the team is shown and written into the HALL OF JUSTICE's own record (kept apart from the Hall of Fame)
    from g3 import ENC as E_
    mix=bytes([0xfd,3])+bytes(E_[c] for c in ' joins the roll.')+bytes([0xfe])+bytes(E_[c] for c in 'Lv. ')+bytes([0xfd,2,0xff])
    t_mon=0x08000000+r.alloc(mix,1)
    S.raw(0x23); S.ptr(nat['jh_record'])
    for i in range(6):
        S.setvar(0x8004,i); S.raw(0x23); S.ptr(nat['jh_slot']); S.compare(0x8001,0); S.goto_if(1,'rolled')
        S.raw(0x75); S._add(struct.pack('<H',0x8001)); S.raw(10,3)               # showmonpic
        S.raw(0x7d,1); S._add(struct.pack('<H',0x8001))                          # bufferspeciesname 1
        S.msg(t_mon,4)
        S.raw(0x76)                                                              # hidemonpic
    S.lab('rolled')
    S.msg(T("COMMISSIONER: It is done. The HALL OF JUSTICE keeps your team. The way out is behind you."),4)
    S.setflag(0x4CB); S.raw(0x6b); S.end()
    sc=0x08000000+put_script(r,S)
    ft=r.alloc(struct.pack('<HHI',0x4001,0,sc)+struct.pack('<H',0),4)
    hof=header(r,1,80); ms_old=r32(r,hof+8)-0x08000000; wi=None; k=ms_old
    while b[k]!=0:
        if b[k]==4: wi=r32(r,k+1)
        k+=5
    assert wi
    ms=r.alloc(bytes([2])+struct.pack('<I',0x08000000+ft)+bytes([4])+struct.pack('<I',wi)+b'\x00',4)
    # ---- people: the commissioner at the foot of the dais, two honour guards
    def talk(text):
        q=SB(); q.msg(T(text),2); q.end(); return 0x08000000+put_script(r,q)
    def obj(i,x,y,gfx_,mv,script):
        t=bytearray(24); t[0]=i; t[1]=gfx_; t[4:6]=struct.pack('<h',x); t[6:8]=struct.pack('<h',y); t[8]=3; t[9]=mv; t[16:20]=struct.pack('<I',script); return bytes(t)
    objs=obj(1,6,4,60,8,talk("COMMISSIONER: Take your place on the carpet. The record is made once."))+obj(2,4,8,60,10,talk("GUARD: Ten medals, ten cases. I know every Captain's name by heart."))+obj(3,HW-5,8,60,9,talk("GUARD: Whatever you did to get here, you stopped the JRA. That counts."))
    oa=r.alloc(objs,4)
    # ---- plaques
    cities=json.load(open('/home/claude/work/army/cities.json'))[:10]
    cities.sort(key=lambda c: c['num'])
    bgs=b''
    for (x,y),c in zip(CASES,cities):
        q=SB(); q.msg(T("BASE NO. %d, %s\nCAPT. %s\n%s"%(c['num'],c['name'],c['captain'],c['medal'])),3); q.end()
        bgs+=struct.pack('<HHBBHI',x,y,0,0,0,0x08000000+put_script(r,q))
    q=SB(); q.msg(T("TO THOSE WHO ENDED THE JOHTO REVOLUTIONARY ARMY.\n\nPEACE THROUGH JUSTICE."),3)
    q.raw(0x23); q.ptr(nat['jh_roll']); q.compare(0x8007,1); q.goto_if(5,'end')
    q.msg(T("ROLL OF HONOUR"),3); q.msg(0x02021cd0,3)
    q.lab('end'); q.end()
    bgs+=struct.pack('<HHBBHI',6,3,0,0,0,0x08000000+put_script(r,q))
    ba=r.alloc(bgs,4)
    # ---- the way out: the doormat takes the player back to Pallet Town
    X=SB(); X.raw(0x39,PALLET[0],PALLET[1],0xff); X._add(struct.pack('<HH',PALLET[2],PALLET[3])); X.raw(0x27); X.end()
    ca=r.alloc(struct.pack('<HHBBHHHI',6,HH-1,3,0,0x40E3,0,0,0x08000000+put_script(r,X)),4)
    ev=r.alloc(bytes([3,0,1,len(bgs)//12])+struct.pack('<IIII',0x08000000+oa,0,0x08000000+ca,0x08000000+ba),4)
    NAME=0x63; r.w32(0x3f1cac+4*(NAME-0x58),0x08000000+r.alloc(leg1.enc('HALL OF JUSTICE'),1))
    (g,n),hh=new_map(r,ch,lay,ev,NAME,scripts=ms)
    return (g,n),(6,HH-2)

# ---------------------------------------------------------------- natives
def build_native(r,arc_gfx):
    b=r.b
    ids=[t for t in range(1,760) if b[T+40*t+1] in (44,45,48) and b[T+40*t+32]>0]
    assert len(ids)==94
    wl=r32(r,0x3af284); ws=r32(r,0x3af294)
    for v in (wl,ws): assert 0x08000000<=v<0x0a000000
    import re
    kb=int(re.search(r'0x([0-9a-f]+)',open('/home/claude/work/police/kills.ld').read()).group(1),16)
    kb_bin=open('/home/claude/work/police/kills.bin','rb').read(); assert bytes(b[kb-0x08000000:kb-0x08000000+len(kb_bin)])==kb_bin,'police kill_check differs from kills.bin'
    kc=[int(l.split()[0],16) for l in subprocess.run(['nm','/home/claude/work/police/kills.elf'],capture_output=True,text=True,check=True).stdout.split('\n') if l.endswith(' kill_check')][0]|1
    arr=lambda t: ','.join(str(ENC_[c]) for c in t)+',255'
    from g3 import ENC as ENC_
    open(W+'/gun_data.h','w').write('#define NJ %d\nstatic const u16 J_IDS[]={%s};\n#define ROB_WRAP_LOAD 0x%08x\n#define ROB_WRAP_SCRIPTS 0x%08x\n#define KILL_CHECK 0x%08x\n#define ARC_GFX %d\nstatic const u8 T_LV[]={%s};\nstatic const u8 T_LIB[]={%s};\nstatic const u8 T_HIDDEN[]={%s};\n'%(len(ids),','.join(map(str,ids)),wl,ws,kc,arc_gfx,'0,%d,%d,255'%(ENC_['L'],ENC_['v']),arr('LIBERTY COUNT: '),arr('???')))
    r.cur=(r.cur+3)&~3; base=0x08000000+r.cur
    open(W+'/gun.ld','w').write('ENTRY(gw_load)\nSECTIONS { . = 0x%08x; .all : { *(.text*) *(.rodata*) *(.data*) } /DISCARD/ : { *(.ARM.exidx*) *(.comment) *(.note*) *(.ARM.attributes) } }\n'%base)
    subprocess.run(['clang','--target=thumbv4t-none-eabi','-mthumb','-Os','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-nostdlib','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-c',W+'/gun.c','-o',W+'/gun.o'],check=True)
    subprocess.run(['ld.lld','-T',W+'/gun.ld',W+'/gun.o','-o',W+'/gun.elf'],check=True)
    subprocess.run(['llvm-objcopy','-O','binary',W+'/gun.elf',W+'/gun.bin'],check=True)
    a=r.alloc(open(W+'/gun.bin','rb').read(),4); assert 0x08000000+a==base
    out={}
    for ln in subprocess.run(['nm',W+'/gun.elf'],capture_output=True,text=True,check=True).stdout.split('\n'):
        f=ln.split()
        if len(f)==3 and f[2] in ('gw_load','gw_scripts','jra_info','jra_pay','jra_shoot','kill_check2','deal_info','deal_accept','deal_refuse','deal_state','deal_gate','kc_show2','lib_text','arc_install','jh_record','jh_slot','jh_roll'): out[f[2]]=(int(f[0],16)&~1)|1
    assert len(out)==17,out.keys()
    r.w32(0x3af284,out['gw_load']); r.w32(0x3af294,out['gw_scripts'])
    # police scripts call kill_check: they now call the version that goes quiet after the deal
    pat=bytes([0x23])+struct.pack('<I',kc); sites=[]; i=0
    while True:
        i=bytes(b).find(pat,i)
        if i<0: break
        sites.append(i); i+=5
    assert len(sites)==5,len(sites)
    for i in sites: r.w32(i+1,out['kill_check2'])
    out['_story_sites']=sites
    # the KILLS screen script calls kc_show: swap in the version with the Liberty Count
    fns=json.load(open('/home/claude/work/leg2/fns.json')); pat=bytes([0x23])+struct.pack('<I',fns['kc_show']); i=0; ks=0
    while True:
        i=bytes(b).find(pat,i)
        if i<0: break
        r.w32(i+1,out['kc_show2']); ks+=1; i+=5
    assert ks>=1,ks
    # the JRA classes pay nothing for winning a battle
    m=0x24f220; k=0
    while b[m+4*k]!=0xff:
        if b[m+4*k] in (44,45,48): b[m+4*k+1]=0
        k+=1
    return out

# ---------------------------------------------------------------- menus
GRAY=bytes([0xfc,0x04,0x03,0x00,0x03])      # colour, highlight, shadow: light grey text
def menu_text(name,gray): return (GRAY if gray else b'')+etxt(name)
def add_menus(r,variants):
    b=r.b; ref=0x9cb58; assert r32(r,ref)==r32(r,0x9cfd4)
    tab=r32(r,ref)-0x08000000; k=0
    while True:
        p=r32(r,tab+8*k); c=b[tab+8*k+4]
        if not(0x08000000<=p<0x0a000000) or c==0 or c>30: break
        k+=1
    assert k==78,k
    ents=bytearray(b[tab:tab+8*k]); ids=[]
    for gr in variants:
        names=['BLESS','THREATEN','SHOOT','LEAVE']
        ls=b''.join(struct.pack('<II',0x08000000+r.alloc(menu_text(n,g),1),0) for n,g in zip(names,gr))
        la=r.alloc(ls,4); ids.append(len(ents)//8)
        ents+=struct.pack('<IBBBB',0x08000000+la,4,0,0,0)
    new=r.alloc(bytes(ents),4); r.w32(ref,0x08000000+new); r.w32(0x9cfd4,0x08000000+new)
    return ids

def trainer_script(r,fns,nat,menus):
    SYM={'rob_info':0x08a09939,'rob_pay':0x08a09a49,'shoot_do':0x08a09b61}
    pk=lambda v: struct.pack('<H',v)
    T=lambda s: T_(r,s)
    t_nogun=T("You have nothing to threaten them with.")
    t_notag=T("You have no BLESS TAG.")
    t_noshoot=T("You need a GLOCK and a 9MM ROUND to shoot.")
    t_done=T("They have nothing left for you.")
    t_promise=T("You gave the police your word:\nsoldiers only.")
    t_cant=T("You can't shoot this one.")
    t_dont=T("Don't shoot! Here, take\neverything I have!")
    t_took=0x08000000+r.alloc(leg1.enc('You took $')[:-1]+b'\xfd\x02'+leg1.enc('!'),1)
    t_nothing=T("They've got nothing left\nto give.")
    t_mons=T('You took their POKéMON!')
    t_thanks=T('Thank you for the blessings, my sins feel cleansed! Here, as a token of my gratitude, have an item!')
    t_askpol=T('Shoot the officer?\nThis uses one 9MM ROUND.')
    t_polshot=T('The officer goes down.\n\nYou took their POKéMON!')
    t_bang=T("BANG!\n\nYou were shot!")
    t_hell=T("Your soul falls.\n\nFlames rise to meet you.")
    t_heaven=T("The world goes white.\n\nSomething warm lifts you up.")
    nm={1:'JRA SOLDIER',2:'JRA CAPTAIN',3:'GENERAL GORE'}
    t_bless={g:T('%s: Don\'t chant your blasphemy at me, heretic!'%n) for g,n in nm.items()}
    t_threat={g:T('%s: Are you serious? You don\'t scare me with that pea shooter. This is a real gun.'%n) for g,n in nm.items()}
    S=SB()
    S.raw(0x23); S.ptr(nat['jra_info'])
    S.compare(0x8003,0); S.goto_if(5,'jra')
    S.raw(0x23); S.ptr(SYM['rob_info'])
    S.compare(0x8006,0); S.goto_if(1,'pol')
    # ---- ordinary trainers
    S.raw(0x47); S._add(pk(BLESS_ITEM)+pk(1)); S.compare(0x800d,0); S.goto_if(5,'nmenu')
    S.raw(0x47); S._add(pk(ITEM_GLOCK)+pk(1)); S.compare(0x800d,0); S.goto_if(1,'normal')
    S.lab('nmenu')
    S.raw(0x23); S.ptr(SYM['rob_info']); S.raw(0x23); S.ptr(nat['deal_gate'])
    S.compare(0x8004,0); S.goto_if(1,'nm_a')
    S.compare(0x8005,0); S.goto_if(1,'nm_b')
    S.raw(0x6f,0,0,menus[2],0); S.goto('nres')
    S.lab('nm_b'); S.raw(0x6f,0,0,menus[3],0); S.goto('nres')
    S.lab('nm_a'); S.compare(0x8005,0); S.goto_if(1,'nm_c')
    S.raw(0x6f,0,0,menus[0],0); S.goto('nres')
    S.lab('nm_c'); S.raw(0x6f,0,0,menus[1],0)
    S.lab('nres')
    S.compare(0x800d,0); S.goto_if(1,'n_bless')
    S.compare(0x800d,1); S.goto_if(1,'n_threat')
    S.compare(0x800d,2); S.goto_if(1,'n_shoot')
    S.goto('normal')
    S.lab('n_bless')
    S.compare(0x8004,0); S.goto_if(5,'n_done')
    S.raw(0x47); S._add(pk(BLESS_ITEM)+pk(1)); S.compare(0x800d,0); S.goto_if(1,'n_notag')
    S.raw(0x45); S._add(pk(BLESS_ITEM)+pk(1))
    S.raw(0x23); S.ptr(fns['bless_do'])
    S.msg(t_thanks); S.raw(0x09,0); S.goto('done')
    S.lab('n_notag'); S.msg(t_notag,4); S.goto('nmenu')
    S.lab('n_done'); S.msg(t_done,4); S.goto('nmenu')
    S.lab('n_threat')
    S.compare(0x8004,0); S.goto_if(5,'n_done')
    S.raw(0x47); S._add(pk(ITEM_GLOCK)+pk(1)); S.compare(0x800d,0); S.goto_if(1,'n_nogun')
    S.raw(0x23); S.ptr(SYM['rob_pay'])
    S.msg(t_dont); S.msg(t_took); S.goto('nmenu')
    S.lab('n_nogun'); S.msg(t_nogun,4); S.goto('nmenu')
    S.lab('n_shoot')
    S.compare(0x8005,0); S.goto_if(1,'n_cant')
    S.raw(0x47); S._add(pk(ITEM_GLOCK)+pk(1)); S.compare(0x800d,0); S.goto_if(1,'n_noammo')
    S.raw(0x47); S._add(pk(ITEM_9MM)+pk(1)); S.compare(0x800d,0); S.goto_if(1,'n_noammo')
    S.compare(0x8004,0); S.goto_if(5,'n_fire')
    S.raw(0x23); S.ptr(SYM['rob_pay'])                    # shooting before threatening: take the cash first
    S.msg(t_dont); S.msg(t_took)
    S.lab('n_fire')
    S.raw(0x45); S._add(pk(ITEM_9MM)+pk(1))
    S.playse(SE_SHOT); S.raw(0x30)
    S.raw(0x53); S._add(pk(0x800f))
    S.raw(0x23); S.ptr(SYM['shoot_do'])
    S.raw(0x55); S._add(pk(0x800f))
    S.compare(0x8007,0); S.goto_if(1,'noprt'); S.raw(0x53); S._add(pk(0x8007)); S.raw(0x55); S._add(pk(0x8007))
    S.lab('noprt'); S.msg(t_mons)
    S.lab('done'); S.release(); S.end()
    S.lab('n_cant')
    S.raw(0x23); S.ptr(nat['deal_state']); S.compare(0x8007,1); S.goto_if(1,'n_promise')
    S.msg(t_cant,4); S.goto('nmenu')
    S.lab('n_promise'); S.msg(t_promise,4); S.goto('nmenu')
    S.lab('n_noammo'); S.msg(t_noshoot,4); S.goto('nmenu')
    # ---- JRA troopers
    S.lab('jra')
    S.raw(0x6f,0,0,menus[0],0)
    S.compare(0x800d,0); S.goto_if(1,'j_bless')
    S.compare(0x800d,1); S.goto_if(1,'j_threat')
    S.compare(0x800d,2); S.goto_if(1,'j_shoot')
    S.goto('normal')
    S.lab('j_bless')
    S.raw(0x47); S._add(pk(BLESS_ITEM)+pk(1)); S.compare(0x800d,0); S.goto_if(1,'j_notag')
    for g in (1,2,3):
        S.compare(0x8003,g); S.goto_if(1,'jb%d'%g)
    for g in (1,2,3):
        S.lab('jb%d'%g); S.msg(t_bless[g],4); S.goto('jra')
    S.lab('j_notag'); S.msg(t_notag,4); S.goto('jra')
    S.lab('j_threat')
    S.raw(0x47); S._add(pk(ITEM_GLOCK)+pk(1)); S.compare(0x800d,0); S.goto_if(1,'j_nogun')
    for g in (1,2,3):
        S.compare(0x8003,g); S.goto_if(1,'jt%d'%g)
    for g in (1,2,3):
        S.lab('jt%d'%g); S.msg(t_threat[g],4); S.goto('gotshot')
    S.lab('j_nogun'); S.msg(t_nogun,4); S.goto('jra')
    S.lab('j_shoot')
    S.raw(0x47); S._add(pk(ITEM_GLOCK)+pk(1)); S.compare(0x800d,0); S.goto_if(1,'j_noammo')
    S.raw(0x47); S._add(pk(ITEM_9MM)+pk(1)); S.compare(0x800d,0); S.goto_if(1,'j_noammo')
    S.raw(0x45); S._add(pk(ITEM_9MM)+pk(1))
    S.playse(SE_SHOT); S.raw(0x30)
    S.raw(0x23); S.ptr(nat['jra_pay']); S.msg(t_took)
    S.raw(0x53); S._add(pk(0x800f))
    S.raw(0x23); S.ptr(nat['jra_shoot'])
    S.raw(0x55); S._add(pk(0x800f))
    S.msg(t_mons); S.goto('done')
    S.lab('j_noammo'); S.msg(t_noshoot,4); S.goto('jra')
    # ---- being shot
    S.lab('gotshot')
    S.playse(SE_SHOT); S.raw(0x30)
    S.msg(t_bang,4)
    S.raw(0x23); S.ptr(fns['karma_check'])
    S.compare(0x8007,1); S.goto_if(1,'tohell')
    S.msg(t_heaven,4); S.raw(0x97,1); warp_script(S,*HEAVEN_WARP); S.releaseall(); S.end()
    S.lab('tohell')
    S.msg(t_hell,4); S.raw(0x97,1); warp_script(S,*HELL_WARP); S.releaseall(); S.end()
    # ---- officers (generated police) and everything else, as before
    S.lab('pol')
    S.raw(0x23); S.ptr(fns['police_info']); S.compare(0x8007,0); S.goto_if(1,'normal')
    S.raw(0x23); S.ptr(nat['deal_state']); S.compare(0x8007,1); S.goto_if(1,'normal')
    S.raw(0x47); S._add(pk(ITEM_GLOCK)+pk(1)); S.compare(0x800d,0); S.goto_if(1,'normal')
    S.raw(0x47); S._add(pk(ITEM_9MM)+pk(1)); S.compare(0x800d,0); S.goto_if(1,'normal')
    S.msg(t_askpol,5); S.compare(0x800d,0); S.goto_if(1,'normal')
    S.raw(0x45); S._add(pk(ITEM_9MM)+pk(1))
    S.playse(SE_SHOT); S.raw(0x30)
    S.raw(0x53); S._add(pk(0x800f))
    S.raw(0x23); S.ptr(fns['police_shoot'])
    S.raw(0x55); S._add(pk(0x800f))
    S.msg(t_polshot); S.goto('done')
    S.lab('normal'); S.raw(0x5e)
    return put_script(r,S)
HEAVEN_WARP=None; HELL_WARP=None
def install(r):
    global HEAVEN_WARP,HELL_WARP
    fns=json.load(open('/home/claude/work/leg2/fns.json'))
    import re
    base=int(re.search(r'0x([0-9a-f]+)',open('/home/claude/work/leg2/leg2.ld').read()).group(1),16)-0x08000000
    lb=open('/home/claude/work/leg2/leg2.bin','rb').read(); assert bytes(r.b[base:base+len(lb)])==lb,'leg2 natives differ from fns.json'
    for k in ('karma_check','bless_do','police_info','police_shoot'): assert fns[k]&1
    assert bytes(r.b[(fns['karma_check']&~1)-0x08000000:(fns['karma_check']&~1)-0x08000000+2])!=b'\xff\xff'
    # art
    ai,ap=art.sprite64(W+'/src22.png'); gi,gp=art.sprite64(W+'/src21.png')
    arc,gir=add_gfx(r,[([ai],ap,None),([gi],gp,None)],[0x1122,0x1123])
    nat=build_native(r,arc)
    (hg,hn),start,nwalk=heaven(r,arc,nat)
    HEAVEN_WARP=(hg,hn,start[0],start[1]); HELL_WARP=(HELL[0],HELL[1],11,23)
    hell(r,gir)
    fix_shot_sound(r); feather_black(r)
    police_offer(r,nat); story_offers(r,nat)
    (jg,jn),jstart=hall_of_justice(r,nat); assert (jg,jn)==(2,81),(jg,jn); print('hall of justice',(jg,jn),jstart)
    menus=add_menus(r,[(0,0,0,0),(0,0,1,0),(1,1,0,0),(1,1,1,0)])
    sc=trainer_script(r,fns,nat,menus)
    assert r32(r,0x1a4ed9)>=0x08000000
    r.w32(0x1a4ed9,0x08000000+sc)
    return dict(heaven=(hg,hn),walk=nwalk,arc=arc,gir=gir,menus=menus,end=r.cur)
if __name__=='__main__':
    r=Rom(sys.argv[1]); info=install(r); r.save(sys.argv[2]); print(info)

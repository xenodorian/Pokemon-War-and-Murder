# Shinigami scene: trainer, sprites, Lavender cutscene (police, fence, splatters) and the tower-top fight
import sys,struct
sys.path.insert(0,'/home/claude/work/tools')
from inc import *
import leg1
from leg1 import enc,r32,header,free_tile
import gfx
from PIL import Image
TR_ID=49; TR_PIC=63; TR_CLASS=30; T=0x798790
GFX_POLICE=60; GFX_SPLAT=0x98; GFX_BODY=0x99   # 0x98 = splatter left by the player's shots; 0x99 = story victims (never counted as player kills)
VAR_SCENE=0x40F2
F_GUARD,F_POLICE_GONE,F_SPLAT_HIDDEN,F_SHINI_GONE=0x4A7,0x4A8,0x4A9,0x4AA
SE_SHOT=347
ITEM_SPELL_TAG,ITEM_MASTER_BALL,ITEM_NUGGET,ITEM_TM30=213,1,110,318
IMG='/tmp/claude-0/-home-user-Pokemon-Outlaw-Mod/aec82f34-6a53-5709-b1a8-a60bf5c1545c/images/'
SRC='/home/claude/work/shinigami_art/'
class SB:
    """tiny script builder with labels"""
    def __init__(s): s.parts=[]; s.labels={}; s.size=0
    def raw(s,*b): s._add(bytes(b))
    def _add(s,b): s.parts.append(('b',b)); s.size+=len(b)
    def ptr(s,p): s.parts.append(('p',p)); s.size+=4
    def lab(s,n): s.labels[n]=s.size
    def ref(s,n): s.parts.append(('l',n)); s.size+=4
    def build(s,base):
        out=bytearray()
        for k,v in s.parts:
            if k=='b': out+=v
            elif k=='p': out+=struct.pack('<I',v)
            else: out+=struct.pack('<I',0x08000000+base+s.labels[v])
        return bytes(out)
    # commands
    def end(s): s.raw(0x02)
    def lockall(s): s.raw(0x69)
    def lock(s): s.raw(0x6a)
    def release(s): s.raw(0x6c)
    def releaseall(s): s.raw(0x6b)
    def faceplayer(s): s.raw(0x5a)
    def msg(s,p,std=4): s.raw(0x0f,0); s.ptr(p); s.raw(0x09,std)
    def setvar(s,v,x): s.raw(0x16); s._add(struct.pack('<HH',v,x))
    def setflag(s,f): s.raw(0x29); s._add(struct.pack('<H',f))
    def clearflag(s,f): s.raw(0x2a); s._add(struct.pack('<H',f))
    def compare(s,v,x): s.raw(0x21); s._add(struct.pack('<HH',v,x))
    def goto(s,label): s.raw(0x05); s.ref(label)
    def goto_if(s,cond,label): s.raw(0x06,cond); s.ref(label)
    def playse(s,n): s.raw(0x2f); s._add(struct.pack('<H',n))
    def delay(s,n): s.raw(0x28); s._add(struct.pack('<H',n))
    def removeobject(s,i): s.raw(0x53); s._add(struct.pack('<H',i))
    def addobject(s,i): s.raw(0x55); s._add(struct.pack('<H',i))
    def applymovement(s,i,p): s.raw(0x4f); s._add(struct.pack('<H',i)); s.ptr(p)
    def waitmovement(s,i=0): s.raw(0x51); s._add(struct.pack('<H',i))
    def fadescreen(s,m): s.raw(0x97,m)
    def giveitem(s,item): s.raw(0x1a); s._add(struct.pack('<HH',0x8000,item)); s.raw(0x1a); s._add(struct.pack('<HH',0x8001,1)); s.raw(0x09,0)
    def trainerbattle(s,tid,intro,defeat): s.raw(0x5c,0); s._add(struct.pack('<HH',tid,0)); s.ptr(intro); s.ptr(defeat)
def put_script(r,sb):
    r.cur=(r.cur+3)&~3; base=r.cur
    code=sb.build(base); a=r.alloc(code,1); assert a==base; return a
def text(r,s): return 0x08000000+r.alloc(enc(s),1)
# ---------------------------------------------------------------- art
def quant(img,maxc=15,th=20):
    """cluster near-equal colours so the sprite fits a 15 colour palette"""
    cols={}
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            p=img.getpixel((x,y))
            if p[3]>=128: cols[p[:3]]=cols.get(p[:3],0)+1
    d=lambda a,b: sum((p-q)**2 for p,q in zip(a,b))**.5
    for t in range(th,200,4):
        cl=[]
        for c,n in sorted(cols.items(),key=lambda k:-k[1]):
            for k in cl:
                if d(c,k[0])<t: k[1].append(c); break
            else: cl.append([c,[c]])
        if len(cl)<=maxc: break
    rep={c:k[0] for k in cl for c in k[1]}
    return rep,[k[0] for k in cl]
def tiles_from_pixels(idx,wt,ht):
    out=bytearray()
    for ty in range(ht):
        for tx in range(wt):
            for y in range(8):
                for x in range(0,8,2): out.append(idx[ty*8+y][tx*8+x]|(idx[ty*8+y][tx*8+x+1]<<4))
    return bytes(out)
def overworld_frames(path):
    """12 frames (4 rows x 3 cols) -> 9 GBA frames 16x32 as RGBA images"""
    sh=Image.open(path).convert('RGBA'); cw,ch=31,33
    def frame(row,col):
        im=sh.crop((7+col*31,5+row*33-(0 if row==0 else 0),7+col*31+18,5+row*33+28))
        # bbox of this frame
        out=Image.new('RGBA',(16,32),(0,0,0,0))
        bb=im.getbbox()
        f=im.crop(bb) if bb else im
        w,h=f.size
        if w>16: l=(w-16)//2; f=f.crop((l,0,l+16,h)); w=16
        out.paste(f,((16-w)//2,32-h-1),f)
        return out
    # sheet rows: 0 up, 1 down, 2 left, 3 right; cols: 0 walk A, 1 stand, 2 walk B
    return [frame(1,1),frame(0,1),frame(2,1),frame(1,0),frame(1,2),frame(0,0),frame(0,2),frame(2,0),frame(2,2)]
SHARED_TAG=0x1120
def _nearest(c,cols):
    return min(range(len(cols)),key=lambda k: sum((a-b)**2 for a,b in zip(c,cols[k])))
def sprite_palette_entry(r,tag):
    b=r.b; pt=r32(r,0x5f4d8)-0x08000000; n=0
    while True:
        t=struct.unpack('<H',b[pt+8*n+4:pt+8*n+6])[0]
        if t==tag: return pt+8*n
        assert t!=0x11ff; n+=1
def build_shared_palette(r,frames):
    """one palette (tag 0x1120, slot 10) for the splatter, Shinigami and the feather, because only slot 10 loads custom colours"""
    b=r.b
    rep,pal=quant_all(frames,10)
    ent=sprite_palette_entry(r,SHARED_TAG); old=gfx.pal_to_rgb(bytes(b[r32(r,ent)-0x08000000:r32(r,ent)-0x08000000+32]))
    gt=r32(r,0x5f2f4)-0x08000000; info=r32(r,gt+4*0x98)-0x08000000
    imgt=r32(r,info+0x1c)-0x08000000; tp=r32(r,imgt)-0x08000000
    use={}
    for k in range(128):
        for nib in (b[tp+k]&15,b[tp+k]>>4):
            if nib: use[nib]=use.get(nib,0)+1
    reds=[old[i] for i,_ in sorted(use.items(),key=lambda x:-x[1])[:4]]
    for k in range(128):
        lo,hi=b[tp+k]&15,b[tp+k]>>4
        lo=0 if lo==0 else 11+_nearest(old[lo],reds); hi=0 if hi==0 else 11+_nearest(old[hi],reds)
        b[tp+k]=lo|(hi<<4)
    cols=[(255,0,255)]+pal+[(0,0,0)]*(10-len(pal))+reds+[(0,0,0)]*(4-len(reds))+[(0,0,0)]
    cols=(cols+[(0,0,0)]*16)[:16]
    # the Shinigami colours occupy indices 1..len(pal); reds are 11..14
    r.w32(ent,0x08000000+r.alloc(gfx.rgb_to_pal(cols),4))
    return rep,pal,cols
def shared_index(rgb,cols,limit):
    return 1+_nearest(rgb,cols[1:limit])
def gfx_add_object(r,info_src_gfx,frames,shared):
    b=r.b; rep,pal,cols=shared
    gt=r32(r,0x5f2f4)-0x08000000; mx=b[0x5f2e0]
    idx_frames=[]
    for f in frames:
        idx=[[0]*16 for _ in range(32)]
        for y in range(32):
            for x in range(16):
                p=f.getpixel((x,y))
                if p[3]>=128: idx[y][x]=pal.index(rep[p[:3]])+1
        idx_frames.append(tiles_from_pixels(idx,2,4))
    img_ptrs=[r.alloc(t,4) for t in idx_frames]
    imgt=r.alloc(b''.join(struct.pack('<IHH',0x08000000+p,0x100,0) for p in img_ptrs),4)
    ib=r32(r,gt+4*info_src_gfx)-0x08000000
    info=bytearray(b[ib:ib+36]); info[2:4]=struct.pack('<H',SHARED_TAG); info[0x1c:0x20]=struct.pack('<I',0x08000000+imgt); info[12]=(info[12]&0xF0)|10
    info_a=r.alloc(bytes(info),4)
    new=r.alloc(bytes(b[gt:gt+4*(mx+1)])+struct.pack('<I',0x08000000+info_a),4)
    r.w32(0x5f2f4,0x08000000+new); b[0x5f2e0]=mx+1
    return mx+1
def quant_all(frames,maxc=15):
    big=Image.new('RGBA',(16*len(frames),32))
    for i,f in enumerate(frames): big.paste(f,(16*i,0))
    return quant(big,maxc)
def trainer_pic(r,path):
    im=Image.open(path).convert('RGBA'); assert im.size==(64,64)
    rep,pal=quant(im)
    idx=[[ (pal.index(rep[im.getpixel((x,y))[:3]])+1) if im.getpixel((x,y))[3]>=128 else 0 for x in range(64)] for y in range(64)]
    data=gfx.pixels_to_tiles(idx)
    cols=[(255,0,255)]+pal+[(0,0,0)]*(15-len(pal))
    fa=0x23957c+8*TR_PIC; pa=0x239a1c+8*TR_PIC
    assert struct.unpack('<HH',r.b[fa+4:fa+8])==(0x800,TR_PIC)
    r.w32(fa,0x08000000+r.alloc(gfx.lz_comp(data),4))
    r.w32(pa,0x08000000+r.alloc(gfx.lz_comp(gfx.rgb_to_pal(cols)),4))
def trainer(r):
    b=r.b; o=T+40*TR_ID
    assert b[o+4]==0xff
    party=[(200,15),(92,20),(93,25),(94,30),(322,35),(254,40)]
    import os
    if os.environ.get('SHINI_TEST'): party=[(200,3)]   # TEST BUILDS ONLY
    pd=b''.join(struct.pack('<HBBHH',255,lvl,0,sp,0) for sp,lvl in party)
    e=bytearray(40); e[0]=0; e[1]=TR_CLASS; e[2]=0x80; e[3]=TR_PIC
    name=bytes(leg1.ENC[c] for c in 'SHINIGAMI'); e[4:16]=name+b'\xff'*(12-len(name))
    e[28:32]=struct.pack('<I',7); e[32]=len(party); e[36:40]=struct.pack('<I',0x08000000+r.alloc(pd,4))
    b[o:o+40]=e
    cn=0x23e558+13*TR_CLASS; nm=bytes(leg1.ENC[c] for c in 'SOUL REAPER'); b[cn:cn+13]=nm+b'\xff'*(13-len(nm))
# ---------------------------------------------------------------- objects / events
def add_obj(r,g,n,x,y,gfxid,script,movement=0,flag=0,elev=3):
    h=header(r,g,n); ev=r32(r,h+4)-0x08000000
    no=r.b[ev]; po=r32(r,ev+4)-0x08000000
    ids=[r.b[po+24*i] for i in range(no)]
    t=bytearray(24); t[0]=max(ids)+1 if ids else 1; t[1]=gfxid; t[4:6]=struct.pack('<h',x); t[6:8]=struct.pack('<h',y)
    t[8]=elev; t[9]=movement; t[10]=0x11 if movement else 0; t[16:20]=struct.pack('<I',script); t[20:22]=struct.pack('<H',flag)
    new=r.alloc(bytes(r.b[po:po+24*no])+bytes(t),4); r.b[ev]=no+1; r.w32(ev+4,0x08000000+new)
    return t[0]
def add_coord(r,g,n,x,y,var,val,script):
    h=header(r,g,n); ev=r32(r,h+4)-0x08000000
    nc=r.b[ev+2]; cp=r32(r,ev+12)-0x08000000 if nc else 0
    c=struct.pack('<HHBBHHHI',x,y,3,0,var,val,0,script)
    new=r.alloc((bytes(r.b[cp:cp+16*nc]) if nc else b'')+c,4); r.b[ev+2]=nc+1; r.w32(ev+12,0x08000000+new)
FENCE=0x34e7
POLICE=[(17,8,8),(18,8,8),(19,8,8),(17,9,10),(19,9,9),(17,10,7),(18,10,7),(19,10,7)]
def lavender(r,gfx_shini):
    g,n=3,4; b=r.b
    h=header(r,g,n); ev=r32(r,h+4)-0x08000000; lay=r32(r,h)-0x08000000; mp=r32(r,lay+12)-0x08000000
    # 1. fence ring around the tower door plaza, open at (18,12)
    cells=[(15,y) for y in range(7,13)]+[(21,y) for y in range(8,13)]+[(x,12) for x in range(16,21) if x!=18]
    for x,y in cells:
        o=mp+2*(y*24+x); b[o:o+2]=struct.pack('<H',FENCE)
    # 2. move the existing NPC out of the plaza
    po=r32(r,ev+4)-0x08000000
    for i in range(b[ev]):
        t=po+24*i
        if struct.unpack('<hh',b[t+4:t+8])==(19,9): b[t+4:t+8]=struct.pack('<hh',13,12)
    # 3. texts and scripts
    t_pol1=text(r,"POLICE: Shinigami! You're under arrest for mass murder! Come quietly, or we will use deadly force!")
    t_shi1=text(r,"SHINIGAMI: I killed Team Rocket grunts because they stole and executed my Pikachu. Now I am simply paying my respects to his spirit. Begone, or suffer the same fate as those other imbeciles.")
    t_pol2=text(r,"POLICE: Not a chance! Surrender or die!")
    t_shi2=text(r,"SHINIGAMI: Save a seat for me in Hell.")
    t_talk=text(r,"POLICE: Stand back! This is a police operation!")
    t_shi=text(r,"SHINIGAMI: ...")
    talk=SB(); talk.msg(t_talk,2); talk.end(); sc_talk=0x08000000+put_script(r,talk)
    shn=SB(); shn.msg(t_shi,2); shn.end(); sc_shi=0x08000000+put_script(r,shn)
    # 4. objects: Shinigami, 8 police, 8 splatters
    sid=add_obj(r,g,n,18,9,gfx_shini,sc_shi,8,F_POLICE_GONE)
    pids=[add_obj(r,g,n,x,y,GFX_POLICE,sc_talk,mv,F_POLICE_GONE) for x,y,mv in POLICE]
    t_vic=text(r,"A bloody mess.\nBest not to look.")
    V_=SB(); V_.msg(t_vic,6); V_.end(); sc_vic=0x08000000+put_script(r,V_)
    spl=[add_obj(r,g,n,x,y,GFX_BODY,sc_vic,0,F_SPLAT_HIDDEN) for x,y,mv in POLICE]
    # 5. cutscene
    mv_up=0x08000000+r.alloc(bytes([0x11,0x11,0x11,0xfe]),1)
    S=SB(); S.lockall()
    S.msg(t_pol1); S.msg(t_shi1); S.msg(t_pol2); S.msg(t_shi2)
    for i in range(8): S.playse(SE_SHOT); S.delay(8)
    S.delay(20)
    for p in pids: S.removeobject(p)
    S.clearflag(F_SPLAT_HIDDEN)
    for s_ in spl: S.addobject(s_)
    S.delay(30)
    import os
    if not os.environ.get('SHINI_NOWALK'):
        S.applymovement(sid,mv_up); S.waitmovement(sid)
        S.removeobject(sid)
    S.setflag(F_POLICE_GONE); S.setvar(VAR_SCENE,1)
    S.releaseall(); S.end()
    sc_scene=0x08000000+put_script(r,S)
    add_coord(r,g,n,18,12,VAR_SCENE,0,sc_scene)
    # 6. map transition script: keeps the object flags in sync with the scene state
    ms=r32(r,h+8)-0x08000000; assert b[ms]==3
    old=r32(r,ms+1)-0x08000000; e=old
    while b[e]!=0x02: e+=1
    inner=bytes(b[old:e])           # setflag guard + original commands (no end)
    T_=SB(); T_._add(inner)
    T_.compare(VAR_SCENE,1); T_.goto_if(1,'done')
    T_.setflag(F_SPLAT_HIDDEN); T_.clearflag(F_POLICE_GONE); T_.end()
    T_.lab('done'); T_.clearflag(F_SPLAT_HIDDEN); T_.setflag(F_POLICE_GONE); T_.end()
    r.w32(ms+1,0x08000000+put_script(r,T_))
    return sid
def tower_top(r,gfx_shini):
    g,n=2,66
    h=header(r,g,n); ev=r32(r,h+4)-0x08000000; po=r32(r,ev+4)-0x08000000
    lid=max(r.b[po+24*i] for i in range(r.b[ev]))+1
    x,y=free_tile(r,g,n,11,2); print('tower top tile',x,y)
    t_intro=text(r,"SHINIGAMI: Spirit of Pikachu, come home.\n\nOh, has someone else come to fight me? Fine. Fight the spirits of the POKéMON Team Rocket has slaughtered. Feel their pain.")
    t_def=text(r,"SHINIGAMI: I didn't expect to find someone strong enough to defeat me. Impressive. Take this.")
    S=SB(); S.lock(); S.faceplayer()
    S.trainerbattle(TR_ID,t_intro,t_def)
    for it in (ITEM_SPELL_TAG,ITEM_MASTER_BALL,ITEM_NUGGET,ITEM_TM30): S.giveitem(it)
    S.playse(39); S.fadescreen(3); S.setflag(F_SHINI_GONE); S.removeobject(lid); S.fadescreen(2)
    S.release(); S.end()
    sc=0x08000000+put_script(r,S)
    got=add_obj(r,g,n,x,y,gfx_shini,sc,8,F_SHINI_GONE); assert got==lid
def install(r):
    pic_art=SRC+'battle.png'; ow_art=SRC+'overworld.png'
    trainer_pic(r,pic_art); trainer(r)
    fr=overworld_frames(ow_art)
    shared=build_shared_palette(r,fr)
    gid=gfx_add_object(r,GFX_POLICE,fr,shared); print('shinigami gfx id',hex(gid))
    lavender(r,gid); tower_top(r,gid)
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))

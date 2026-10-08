# usage: army.py in.gba out.gba
# JRA (Johto Revolutionary Army), stage 1: Pewter City.
#  - assets: soldier / captain object graphics (recolours that keep the vanilla palettes), army splatter graphic, trainer pictures, trainer classes, HONOR MEDAL
#  - Pewter base interior (group 2 map 69): recoloured Rocket Hideout B1F layout with a grey copy of its tileset
#  - Pewter exterior: base building beside the museum, guards, two patrol soldiers (placed at random each visit)
#  - natives: patrol placement and soldiers shooting bystanders (army.c)
import sys,struct,subprocess,json,os
sys.path.insert(0,'/home/claude/work/tools')
from inc import *
import gfx,leg1,shinigami,army_gfx,army_text,army_tiles,army_sites
from leg1 import r32,header
from shinigami import SB,put_script
from g3 import ENC
W='/home/claude/work/army'
T=0x798790; GROUPS=0x3526A8
# trainer ids that no script or special uses: Hoenn leftovers (1-29 without 3, which is the hack's AIDE), the unused channelers, and gym trainers the hack removed.
# 492-515 (Trainer Tower, player pictures) and 326-331 (rival) are in use and stay out.
ID_POOL=[1,2]+list(range(4,30))+list(range(50,55))+list(range(79,89))+list(range(454,462))+[101,113,124,147,161,174,175,176,200,210,211,212,217,257,263,275,284,299,311,312,370,372,395,397,398,399,405,407,408,409,424,425,428,430,433,434,437,439,440,530,533,593,594]
FLAG_CLEARED0=0x4C0          # + city index: the base was cleared (soldiers leave). 0x4B0-0x4BC are the vanilla FLAG_DEFEATED_<leader> flags, so they are not used
VICTIM_VARS=[0x40F9,0x40FA,0x40FB,0x40FC,0x40FD,0x40FE,0x40FF,0x40E0,0x40E1,0x40E2]     # by city index: bit k set = the NPC with local id k was shot by a patrol (unnamed vanilla vars)
MAX_VICTIMS=3
IDS_PER_CITY=9              # 4 base soldiers, the Captain, 2 patrol soldiers, 2 entrance guards
CLS_SOLDIER,CLS_CAPTAIN,CLS_GENERAL=48,44,45          # unused vanilla classes, renamed
PIC_SOLDIER,PIC_CAPTAIN,PIC_GENERAL=64,66,68
ITEM_BASE=0x3db028; ICONT=0x3d4294
SE_SHOT=347
GRUNT_PIC=109; GRUNT_TRAINER=359
SOLDIER_MAP={13:7,12:6,11:5,8:7,9:7,10:7}             # grey uniform -> olive; the red R emblem (8-10) is painted over with the uniform colour (palette 0x1106 entries 5-7)
CAPTAIN_MAP={8:6,9:10,10:10,13:7}                     # Surge's greens -> drab olive, pink -> dark olive (palette 0x1105)
def captain_frame(g):
    """Surge's greens -> drab olive; his yellow hair (palette entries 5-7, above the first jacket row) -> brown"""
    cut=next((y for y,row in enumerate(g) if any(v in (8,9,10) for v in row)),22)
    return [[({5:4,6:4,7:15}.get(v,v) if y<cut and v in (5,6,7) else CAPTAIN_MAP.get(v,v)) for v in row] for y,row in enumerate(g)]
REASONS=['JAYWALKING','WEARING THE WRONG HAT','OWNING A RATTATA','HUMMING OFF KEY','ADMIRING KANTO','LOOKING SUSPICIOUS','SNEEZING AT A SOLDIER','ASKING QUESTIONS','BEING UNPATRIOTIC','STANDING ON A SHADOW','HAVING A NICE SMILE','NOT SALUTING']
def etxt(s): return bytes(ENC[c] for c in s)+b'\xff'
# ----------------------------------------------------------------------------------------------- team rules
# The ten bases in unlock order. num = base number on the sign and the medal; idx = flag / trainer id slice index (Pewter keeps 0 because it shipped first);
# cap = approved town level, used as the gym leader's strongest Pokemon; lead = the gym leader's party size (Pallet and Lavender have no gym: assumed 1 and 3; Viridian = Giovanni, 4).
# src = Rocket Hideout / Silph Co floor (group 1 map number) cloned in grey for the interior; item = free vanilla item slot used for the JRA MEDAL.
CITIES=[
 dict(name='PALLET',   num=1, idx=1, cap=5,  lead=1, town=0,  src=57, item=58),
 dict(name='VIRIDIAN', num=2, idx=2, cap=10, lead=4, town=1,  src=56, item=59),
 dict(name='PEWTER',   num=3, idx=0, cap=15, lead=2, town=2,  src=42, item=57),
 dict(name='CERULEAN', num=4, idx=3, cap=20, lead=2, town=3,  src=55, item=60),
 dict(name='VERMILION',num=5, idx=4, cap=25, lead=3, town=5,  src=54, item=61),
 dict(name='LAVENDER', num=6, idx=5, cap=30, lead=3, town=4,  src=45, item=62),
 dict(name='CELADON',  num=7, idx=6, cap=35, lead=3, town=6,  src=53, item=72),
 dict(name='SAFFRON',  num=8, idx=7, cap=40, lead=4, town=10, src=52, item=82),
 dict(name='FUCHSIA',  num=9, idx=8, cap=45, lead=4, town=7,  src=51, item=87),
 dict(name='CINNABAR', num=10,idx=9, cap=50, lead=4, town=8,  src=49, item=88)]
# real service medals, most prestigious (Cinnabar, the hardest Captain) to least (Pallet): item name (13 characters at most), full name, bag description
MEDALS={1:('MERIT SERVICE','MERITORIOUS SERVICE MEDAL','Meritorious Service Medal\nfrom CAPT. {cap}.'),
 2:('PURPLE HEART','PURPLE HEART','Purple Heart, from\nCAPT. {cap}.'),
 3:('BRONZE STAR','BRONZE STAR MEDAL','Bronze Star Medal, from\nCAPT. {cap}.'),
 4:("SOLDIER'S MDL","SOLDIER'S MEDAL","Soldier's Medal, from\nCAPT. {cap}."),
 5:('FLYING CROSS','DISTINGUISHED FLYING CROSS','Dist. Flying Cross, from\nCAPT. {cap}.'),
 6:('LEGION MERIT','LEGION OF MERIT','Legion of Merit, from\nCAPT. {cap}.'),
 7:('SILVER STAR','SILVER STAR','Silver Star, from\nCAPT. {cap}.'),
 8:('DEFENSE DSM','DEFENSE DISTINGUISHED SERVICE MEDAL','Defense Dist. Service\nMedal, from CAPT. {cap}.'),
 9:('SERVICE CROSS','DISTINGUISHED SERVICE CROSS','Distinguished Service\nCross, from CAPT. {cap}.'),
 10:('HONOR MEDAL','MEDAL OF HONOR','Medal of Honor, from\nCAPT. {cap}.')}
for c in CITIES:
    c['captain']=army_text.CAPTAIN[c['name']]; m=MEDALS[c['num']]; c['medal'],c['medal_full'],c['medal_desc']=m[0],m[1],m[2].format(cap=c['captain'])
    assert len(c['medal'])<=13
# Gen 2 species and the level at which they are a natural pick (basic forms 1, evolutions at their evolution level, trade/stone forms at a typical level)
GEN2=[(161,1),(162,15),(163,1),(164,20),(165,1),(166,18),(167,1),(168,22),(169,30),(170,1),(171,27),(172,1),(173,1),(174,1),(176,25),(177,1),(178,25),(179,1),(180,15),(181,30),
 (182,30),(183,1),(184,18),(185,15),(186,40),(187,1),(188,18),(189,27),(190,1),(191,1),(192,30),(193,1),(194,1),(195,20),(196,30),(197,30),(198,1),(199,40),(200,1),(202,15),(203,1),(204,1),
 (205,31),(206,1),(207,1),(208,35),(209,1),(210,23),(211,1),(212,35),(213,1),(214,1),(215,1),(216,1),(217,30),(218,1),(219,38),(220,1),(221,33),(222,1),(223,1),(224,25),(225,1),(226,1),
 (227,1),(228,1),(229,24),(230,40),(231,1),(232,25),(233,35),(234,1),(235,1),(236,1),(237,20),(238,1),(239,1),(240,1),(241,1),(242,35),(246,1),(247,30),(248,55)]
def pick_species(rng,level,used):
    elig=[sp for sp,mn in GEN2 if mn<=level]
    near=[sp for sp,mn in GEN2 if level-20<=mn<=level]
    pool=[x for x in (near or elig) if x not in used] or elig
    return rng.choice(pool)
def gen_team(c,role,tid):
    """the army's team rules, with the town level cap standing in for the gym leader's strongest Pokemon.
    captain: leader's party size + 1 (6 at most), every level 1-5 above the cap. soldier: 1 up to the leader's party size, every level 3-8 below the cap (never under 2)."""
    import random
    rng=random.Random('%s-%s-%d'%(c['name'],role,tid)); party=[]; used=set()
    if role=='captain':
        n=min(6,c['lead']+1); levels=[c['cap']+rng.randint(1,5) for _ in range(n)]
    else:
        n=rng.randint(1,c['lead']); levels=[max(2,c['cap']-rng.randint(3,8)) for _ in range(n)]
    levels.sort()
    for lv in levels:
        sp=pick_species(rng,lv,used); used.add(sp); party.append((sp,lv))
    return party
# ----------------------------------------------------------------------------------------------- assets
def alloc_trainer_pic(r,pic,src_pic,recolor,pixfn=None):
    """copy a trainer picture into an unused slot with a recoloured palette"""
    b=r.b
    fs=0x23957c+8*src_pic; ps=0x239a1c+8*src_pic
    fa=0x23957c+8*pic; pa=0x239a1c+8*pic
    assert struct.unpack('<HH',b[fa+4:fa+8])==(0x800,pic),(pic,b[fa+4:fa+8].hex())
    assert struct.unpack('<H',b[ps+4:ps+6])[0]==src_pic
    src_pal=gfx.lz_decomp(b,r32(r,ps)-0x08000000)
    cols=recolor(gfx.pal_to_rgb(src_pal))
    if pixfn:
        g=gfx.tiles_to_pixels(gfx.lz_decomp(b,r32(r,fs)-0x08000000),8,8); pixfn(g,cols)
        r.w32(fa,0x08000000+r.alloc(gfx.lz_comp(gfx.pixels_to_tiles(g)),4))
    else: r.w32(fa,r32(r,fs))
    r.w32(pa,0x08000000+r.alloc(gfx.lz_comp(gfx.rgb_to_pal(cols)),4))
def pic_from_png(r,pic,path):
    """trainer picture from a 64x64 PNG (transparent background, up to 15 opaque colours)"""
    from PIL import Image
    im=Image.open(path).convert('RGBA'); assert im.size==(64,64)
    cols=[]
    for y in range(64):
        for x in range(64):
            c=im.getpixel((x,y))
            if c[3]>=128 and c[:3] not in cols: cols.append(c[:3])
    assert len(cols)<=15,len(cols)
    idx=[[(cols.index(im.getpixel((x,y))[:3])+1) if im.getpixel((x,y))[3]>=128 else 0 for x in range(64)] for y in range(64)]
    fa=0x23957c+8*pic; pa=0x239a1c+8*pic
    assert struct.unpack('<HH',r.b[fa+4:fa+8])==(0x800,pic)
    r.w32(fa,0x08000000+r.alloc(gfx.lz_comp(gfx.pixels_to_tiles(idx)),4))
    r.w32(pa,0x08000000+r.alloc(gfx.lz_comp(gfx.rgb_to_pal([(115,197,164)]+cols+[(0,0,0)]*(15-len(cols)))),4))
def captain_pupil(g,cols):
    """the black pupil pixel of the left eye becomes dark brown (palette entry 12, whose two stray pixels move to entry 13)"""
    for y in range(64):
        for x in range(64):
            if g[y][x]==12: g[y][x]=13
    assert g[13][33]==15
    g[13][33]=12; cols[12]=(58,30,18)
def ramp(cols,kind):
    """recolour a trainer picture palette: greys become olive, strong reds become tan, skin stays"""
    import colorsys
    out=[]
    for i,(rr,g,bb) in enumerate(cols):
        if i==0: out.append((rr,g,bb)); continue
        h,s,v=colorsys.rgb_to_hsv(rr/255,g/255,bb/255)
        if v<0.12: out.append((rr,g,bb)); continue
        if (s<0.22 and v<0.97) or (0.5<h<0.8 and kind=='soldier'):      # neutral (and the soldier's navy torso): olive ramp by brightness
            lo,hi=((44,52,30),(190,200,140))
            t=min(1.0,v*1.25); c=tuple(int(lo[k]+(hi[k]-lo[k])*t) for k in range(3)); out.append(c)
        elif 0.0<=h<0.06 and s>0.5 and kind=='soldier':   # the R emblem: same colour as the uniform
            out.append((88,98,64))
        elif 0.0<=h<0.06 and s>0.5:   # saturated red -> tan/brown
            out.append((int(190*v+30),int(160*v+20),int(100*v+10)))
        elif kind=='captain' and 0.5<h<0.75 and s>0.3:   # blue eyes -> brown
            out.append((112,62,40))
        elif kind=='captain' and 0.08<h<0.17 and s>0.35:   # blond hair -> brown
            c=colorsys.hsv_to_rgb(0.04,0.62,v*0.62); out.append(tuple(int(t*255) for t in c))
        elif kind=='captain' and (0.17<h<0.45) and s>0.4:   # bright green -> drab olive
            c=colorsys.hsv_to_rgb(0.20,0.45,v*0.7); out.append(tuple(int(t*255) for t in c))
        elif kind=='captain' and (h>0.8 or h<0.02) and s>0.3:   # pink -> brass
            c=colorsys.hsv_to_rgb(0.12,0.55,v*0.85); out.append(tuple(int(t*255) for t in c))
        else: out.append((rr,g,bb))
    return out
def rename_class(r,cls,name):
    cn=0x23e558+13*cls; r.b[cn:cn+13]=etxt(name).ljust(13,b'\xff')
def add_alias_gfx(r,src):
    """a second graphics id pointing at the same graphics info, so the object has its own id"""
    b=r.b; gt=r32(r,0x5f2f4)-0x08000000; mx=b[0x5f2e0]
    new=r.alloc(bytes(b[gt:gt+4*(mx+1)])+bytes(b[gt+4*src:gt+4*src+4]),4)
    r.w32(0x5f2f4,0x08000000+new); b[0x5f2e0]=mx+1
    return mx+1
def add_medal(r,item,name,desc,src_item=None):
    b=r.b; o=ITEM_BASE+44*item
    assert b[o:o+9]==bytes([0xac])*8+b'\xff' and struct.unpack('<H',b[o+14:o+16])[0]==0,(item,b[o:o+16].hex())
    src=ITEM_BASE+44*src_item
    rec=bytearray(b[src:src+44]); rec[0:14]=etxt(name).ljust(14,b'\x00'); rec[14:16]=struct.pack('<H',item); rec[16:18]=struct.pack('<H',0)
    rec[20:24]=struct.pack('<I',0x08000000+r.alloc(bytes(ENC[c] if c!='\n' else 0xFE for c in desc)+b'\xff',1))
    b[o:o+44]=rec
    ic=ICONT+8*item; ics=ICONT+8*src_item
    r.w32(ic,r32(r,ics)); r.w32(ic+4,r32(r,ics+4))
def make_trainer(r,tid,cls,pic,name,party):
    b=r.b; e=bytearray(b[T+40*GRUNT_TRAINER:T+40*GRUNT_TRAINER+40])
    e[0]=0; e[1]=cls; e[3]=pic
    e[4:16]=etxt(name)[:-1].ljust(12,b'\xff')
    e[16:28]=bytes(12); e[32]=len(party)
    pd=b''.join(struct.pack('<HBBHH',255,lvl,0,sp,0) for sp,lvl in party)
    e[36:40]=struct.pack('<I',0x08000000+r.alloc(pd,4))
    b[T+40*tid:T+40*tid+40]=e
def add_obj(r,g,n,t):
    """append one 24-byte object template to a map; returns its local id"""
    h=header(r,g,n); ev=r32(r,h+4)-0x08000000; no=r.b[ev]; po=r32(r,ev+4)-0x08000000
    ids=[r.b[po+24*i] for i in range(no)]; t[0]=max(ids)+1 if ids else 1
    new=r.alloc(bytes(r.b[po:po+24*no])+bytes(t),4); r.b[ev]=no+1; r.w32(ev+4,0x08000000+new)
    return t[0]
def obj_tmpl(gfxid,x,y,script,move=0,trainer=0,sight=0,flag=0,elev=3):
    t=bytearray(24); t[1]=gfxid; t[4:6]=struct.pack('<h',x); t[6:8]=struct.pack('<h',y); t[8]=elev; t[9]=move; t[10]=0x11 if move else 0
    t[12:14]=struct.pack('<H',trainer); t[14:16]=struct.pack('<H',sight); t[16:20]=struct.pack('<I',script); t[20:22]=struct.pack('<H',flag)
    return t
def add_sign(r,g,n,x,y,block,text):
    """a visible sign tile (collision) plus its bg event with the text; used for every base (the game font has no # character, so 'BASE NO. 1')"""
    h=header(r,g,n); lay=r32(r,h)-0x08000000; w=r32(r,lay); mp=r32(r,lay+12)-0x08000000
    r.b[mp+2*(y*w+x):mp+2*(y*w+x)+2]=struct.pack('<H',block)
    ev=r32(r,h+4)-0x08000000; nb=r.b[ev+3]; bp=r32(r,ev+16)-0x08000000
    S=SB(); S.msg(TXT(r,text),3); S.end()
    new=r.alloc(bytes(r.b[bp:bp+12*nb])+struct.pack('<HHBBHI',x,y,0,0,0,0x08000000+put_script(r,S)),4)
    r.b[ev+3]=nb+1; r.w32(ev+16,0x08000000+new)
def add_warp(r,g,n,x,y,dest_warp,dest_map,dest_group):
    h=header(r,g,n); ev=r32(r,h+4)-0x08000000; nw=r.b[ev+1]; wp=r32(r,ev+8)-0x08000000
    new=r.alloc(bytes(r.b[wp:wp+8*nw])+struct.pack('<hhBBBB',x,y,0,dest_warp,dest_map,dest_group),4)
    r.b[ev+1]=nw+1; r.w32(ev+8,0x08000000+new); return nw
# ----------------------------------------------------------------------------------------------- natives
def build_native(r,data):
    open(W+'/army_data.h','w').write(data)
    r.cur=(r.cur+3)&~3; base=0x08000000+r.cur
    open(W+'/army.ld','w').write('ENTRY(army_entry)\nSECTIONS { . = 0x%08x; .all : { *(.text*) *(.rodata*) *(.data*) } /DISCARD/ : { *(.ARM.exidx*) *(.comment) *(.note*) *(.ARM.attributes) } }\n'%base)
    subprocess.run(['clang','--target=thumbv4t-none-eabi','-mthumb','-Os','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-nostdlib','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-c',W+'/army.c','-o',W+'/army.o'],check=True)
    subprocess.run(['ld.lld','-T',W+'/army.ld',W+'/army.o','-o',W+'/army.elf'],check=True)
    subprocess.run(['llvm-objcopy','-O','binary',W+'/army.elf',W+'/army.bin'],check=True)
    a=r.alloc(open(W+'/army.bin','rb').read(),4); assert 0x08000000+a==base
    out={}
    for ln in subprocess.run(['nm',W+'/army.elf'],capture_output=True,text=True,check=True).stdout.split('\n'):
        f=ln.split()
        if len(f)==3 and f[2] in ('army_entry','army_note'): out[f[2]]=(int(f[0],16)&~1)|1
    assert len(out)==2
    return out
def fix_splat_collision(r):
    """DoesObjectCollideWithObjectAt: the player's splatter, story bodies (0x98, 0x99) and the army splatter (id passed in) never block"""
    return None
# ----------------------------------------------------------------------------------------------- shared script pieces
def TXT(r,s): return shinigami.text(r,s)
def TXB(r,s):
    """battle speech: a trailing space keeps the text engine from dropping the last character"""
    return 0x08000000+r.alloc(leg1.enc(s)[:-1]+bytes([ENC[' ']])+b'\xff',1)
def soldier_script(r,tid,intro,defeat,after):
    S=SB(); S.raw(0x5c,0); S._add(struct.pack('<HH',tid,0)); S.ptr(TXB(r,intro)); S.ptr(TXB(r,defeat)); S.msg(TXT(r,after),6); S.end()
    return 0x08000000+put_script(r,S)
def talk_script(r,text):
    S=SB(); S.lock(); S.faceplayer(); S.msg(TXT(r,text)); S.release(); S.end()
    return 0x08000000+put_script(r,S)
def captain_script(r,tid,cleared_flag,medal,intro,defeat,won,after,medal_name,city):
    S=SB(); S.raw(0x5c,1); S._add(struct.pack('<HH',tid,0)); S.ptr(TXB(r,intro)); S.ptr(TXB(r,defeat)); S.ref('cont')
    S.msg(TXT(r,after),6); S.end()
    S.lab('cont')
    S.raw(0x2b); S._add(struct.pack('<H',cleared_flag)); S.goto_if(1,'again')       # checkflag
    S.setflag(cleared_flag); S.raw(0x44); S._add(struct.pack('<HH',medal,1))
    S.msg(TXT(r,won)); S.msg(TXT(r,"You received the %s!\n\nThe JRA soldiers are pulling out of %s."%(medal_name,city)),6); S.end()
    S.lab('again'); S.msg(TXT(r,after),6); S.end()
    return 0x08000000+put_script(r,S)
def splat_script(r,fns):
    t=leg1.enc('A note is pinned to the body:\n\n“EXECUTED FOR ')[:-1]+b'\xfd\x02'+leg1.enc('.”')
    S=SB(); S.lock(); S.raw(0x23); S.ptr(fns['army_note']); S.msg(0x08000000+r.alloc(t,1)); S.release(); S.end()
    return 0x08000000+put_script(r,S)

# ----------------------------------------------------------------------------------------------- the General (final camp)
FLAG_GENERAL=0x4CA           # the General was beaten
GENERAL_ID_SLICE=(90,94)     # four spare ids: the General, two pairs of elite soldiers share one id each, the two camp guards share one
LEGENDS=[243,244,245,251,249,250]       # RAIKOU ENTEI SUICUNE CELEBI LUGIA HO-OH, all level 50
GENERAL_MAP={13:6,12:5,9:5,11:5}
def general_frame(g):
    """Giovanni's overworld sprite with the uniform recoloured khaki (rows from the neck down only, so the hair stays dark)"""
    return [[(GENERAL_MAP.get(v,v) if y>=11 else v) for v in row] for y,row in enumerate(g)]
def general_pic_recolor(cols):
    c=list(cols)
    c[9]=(46,54,34); c[12]=(76,88,52); c[11]=(108,122,76); c[5]=(218,174,58); c[6]=(166,126,38); c[13]=(168,170,160)
    return c
def general_pic_pixels(g,cols):
    for y in range(14):
        for x in range(64):
            if g[y][x]==12: g[y][x]=13
            elif g[y][x]==11: g[y][x]=8
def camp_team(tid,n,lo,hi):
    import random
    rng=random.Random('camp-team-%d'%tid); used=set(); levels=sorted(rng.randint(lo,hi) for _ in range(n)); party=[]
    for lv in levels:
        sp=pick_species(rng,lv,used); used.add(sp); party.append((sp,lv))
    return party

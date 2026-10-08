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
ID_POOL=[1,2]+list(range(4,30))+[326,327,328,329,330]+list(range(79,89))+list(range(454,462))+[101,113,124,147,161,174,175,176,200,210,211,212,217,257,263,275,284,299,311,312,370,372,395,397,398,399,405,407,408,409,424,425,428,430,433,434,437,439,440,530,533,593,594]
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
GENERAL_MAP={13:6,12:7,9:5,11:5}
GEN_HAIR_ROWS={0:18,3:18,4:18,1:20,5:20,6:20,2:22,7:22,8:22}
def make_general_fn():
    """Giovanni's overworld sprite: grey hair, olive uniform. The hair (palette entries 13, 12, 7 in the head rows) becomes grey (12, 11, 13); the rest of the body is remapped olive.
    add_remapped calls the function once per frame, in order, so the frame number is counted here."""
    st=dict(f=0)
    def fn(g):
        fi=st['f']; st['f']+=1; lim=GEN_HAIR_ROWS[fi]; out=[]
        for y,row in enumerate(g):
            o=[]
            for v in row:
                if y<=lim and v in (13,12,7) and not (fi in (0,3,4) and y>18):
                    if fi in (2,7,8) and v in (12,13) and y>16: v=GENERAL_MAP.get(v,v)
                    else: v={13:12,12:11,7:13}[v]
                else: v=GENERAL_MAP.get(v,v)
                o.append(v)
            out.append(o)
        return out
    return fn
def camp_team(tid,n,lo,hi):
    import random
    rng=random.Random('camp-team-%d'%tid); used=set(); levels=sorted(rng.randint(lo,hi) for _ in range(n)); party=[]
    for lv in levels:
        sp=pick_species(rng,lv,used); used.add(sp); party.append((sp,lv))
    return party
# ----------------------------------------------------------------------------------------------- the base interior (grey clone of a Rocket Hideout / Silph Co floor)
def grey(c):
    rr,g,b=[v/31 for v in c]; y=0.30*rr+0.59*g+0.11*b
    return tuple(max(0,min(31,int(round(t*31)))) for t in (y*0.98,y,y*1.03))
STATE=dict(NL=392,NUM=69,grey={})
def grey_secondary(r,S):
    """one shared grey copy of the Hideout / Silph secondary tileset"""
    if S in STATE['grey']: return STATE['grey'][S]
    b=r.b; spal=r32(r,S+8)-0x08000000
    pal=bytearray(b[spal:spal+512])
    for p in range(7,13):
        for i in range(1,16):
            v=struct.unpack('<H',pal[32*p+2*i:32*p+2*i+2])[0]
            cr,cg,cb=grey((v&31,(v>>5)&31,(v>>10)&31)); pal[32*p+2*i:32*p+2*i+2]=struct.pack('<H',cr|(cg<<5)|(cb<<10))
    pa=r.alloc(bytes(pal),4)
    H=bytearray(b[S:S+24]); H[8:12]=struct.pack('<I',0x08000000+pa); sec=r.alloc(bytes(H),4)
    STATE['grey'][S]=sec; return sec
def grey_primary(r,P):
    """shared grey copy of the indoor primary tileset (palettes 0-6), so elevator doors, plants and the like are grey too"""
    key=('P',P)
    if key in STATE['grey']: return STATE['grey'][key]
    b=r.b; pp=r32(r,P+8)-0x08000000
    pal=bytearray(b[pp:pp+7*32])
    for p in range(7):
        for i in range(1,16):
            v=struct.unpack('<H',pal[32*p+2*i:32*p+2*i+2])[0]
            cr,cg,cb=grey((v&31,(v>>5)&31,(v>>10)&31)); pal[32*p+2*i:32*p+2*i+2]=struct.pack('<H',cr|(cg<<5)|(cb<<10))
    pa=r.alloc(bytes(pal),4)
    H=bytearray(b[P:P+24]); H[8:12]=struct.pack('<I',0x08000000+pa); new=r.alloc(bytes(H),4)
    STATE['grey'][key]=new; return new
def build_base_map(r,src_n,objects,warps,mapsec,name):
    b=r.b
    src=header(r,1,src_n); slay=r32(r,src)-0x08000000
    S=r32(r,slay+20)-0x08000000
    sec=grey_secondary(r,S)
    lay=bytearray(b[slay:slay+28]); lay[20:24]=struct.pack('<I',0x08000000+sec); assert bytes(lay[24:26])==bytes([2,2]),lay[24:28].hex()
    lay=r.alloc(bytes(lay),4)
    ob=b''.join(bytes(t) for t in objects); oa=r.alloc(ob,4)
    wb=b''.join(struct.pack('<hhBBBB',*w) for w in warps); wa=r.alloc(wb,4)
    ev=r.alloc(bytes([len(objects),len(warps),0,0])+struct.pack('<IIII',0x08000000+oa,0x08000000+wa,0,0),4)
    ms=r.alloc(b'\x00',1)
    hb=bytearray(b[src:src+28]); hb[0:4]=struct.pack('<I',0x08000000+lay); hb[4:8]=struct.pack('<I',0x08000000+ev); hb[8:12]=struct.pack('<I',0x08000000+ms); hb[12:16]=bytes(4)
    LT=r32(r,0x55194)-0x08000000; NL=STATE['NL']
    for k in (383,391): lp=r32(r,LT+4*k)-0x08000000; assert 4<=r32(r,lp)<=60,k
    tab=r.alloc(bytes(b[LT:LT+4*NL])+struct.pack('<I',0x08000000+lay),4); r.w32(0x55194,0x08000000+tab)
    hb[18:20]=struct.pack('<H',NL+1); STATE['NL']=NL+1
    if mapsec not in STATE.setdefault('named',set()): r.w32(0x3f1cac+4*(mapsec-0x58),0x08000000+r.alloc(leg1.enc(name),1)); STATE['named'].add(mapsec)
    hb[20]=mapsec; hb[0x1a]=100; hb[25]|=0x04
    hdr=r.alloc(bytes(hb),4)
    g2=r32(r,GROUPS+8)-0x08000000; num=STATE['NUM']
    for k in (60,num-1): hp=r32(r,g2+4*k)-0x08000000; assert 0x08000000<=r32(r,hp)<0x0a000000,k
    ntab=r.alloc(bytes(b[g2:g2+4*num])+struct.pack('<I',0x08000000+hdr),4); r.w32(GROUPS+8,0x08000000+ntab)
    STATE['NUM']=num+1
    return 2,num
def best_entry(r,src_n):
    """the source warp whose surroundings give the biggest walkable floor: that tile becomes the base's entrance"""
    import reach
    d=bytes(r.b); h=header(r,1,src_n); ev=r32(r,h+4)-0x08000000; wp=r32(r,ev+8)-0x08000000
    ws=[struct.unpack('<hhBBBB',r.b[wp+8*i:wp+8*i+8])[:2] for i in range(r.b[ev+1])]
    best=None
    for w in ws:
        s,_=reach.reach(d,1,src_n,w)
        if best is None or len(s)>len(best[1]): best=(w,s)
    return best[0],ws
# ----------------------------------------------------------------------------------------------- events helpers
def add_coord(r,g,n,x,y,script):
    h=header(r,g,n); ev=r32(r,h+4)-0x08000000; nc=r.b[ev+2]
    old=b''
    if nc: cp=r32(r,ev+12)-0x08000000; old=bytes(r.b[cp:cp+16*nc])
    new=r.alloc(old+struct.pack('<HHBBHHHI',x,y,3,0,0x40E3,0,0,script),4); r.b[ev+2]=nc+1; r.w32(ev+12,0x08000000+new)   # var 0x40E3 stays 0, so the event always runs (trigger 0 would run the script in the wrong context)
def door_lock_script(r,item,need,name):
    """stepping on the tile in front of the door without the previous base's medal: refused and pushed back"""
    S=SB(); S.lockall()
    S.raw(0x47); S._add(struct.pack('<HH',item,1))                  # checkitem
    S.compare(0x800D,1); S.goto_if(1,'open')
    S.msg(TXT(r,"The door is locked. A plate beside it reads:\n\n%s REQUIRED."%name),4)
    S.applymovement(0xff,0x08000000+r.alloc(bytes([0x10,0xfe]),1)); S.waitmovement(0xff); S.releaseall(); S.end()
    S.lab('open'); S.releaseall(); S.end()
    return 0x08000000+put_script(r,S)
def patrol_tiles(r,g,n,start,keep_out,k=2,seed='p'):
    """two open lawn tiles reachable from `start` for the patrol templates (the native moves them to a random spot at every visit anyway)"""
    import reach,random
    d=bytes(r.b); seen,(w,h)=reach.reach(d,g,n,start)
    _,_,grid,beh,objs=reach.load(d,g,n)
    ok=[p for p in sorted(seen) if 2<=p[0]<w-2 and 2<=p[1]<h-2 and all(((grid[p[1]+j][p[0]+i]>>10)&3)==0 and (grid[p[1]+j][p[0]+i]>>12)==3 for i in (-1,0,1) for j in (-1,0,1))
        and not any(abs(p[0]-a)<=3 and abs(p[1]-b)<=3 for a,b in keep_out)]
    rng=random.Random(seed); rng.shuffle(ok); out=[]
    for p in ok:
        if all(abs(p[0]-q[0])+abs(p[1]-q[1])>=6 for q in out): out.append(p)
        if len(out)==k: break
    assert len(out)==k,'no patrol tiles'
    return out
# ----------------------------------------------------------------------------------------------- exterior sites (all bases use the same grey house, grafted into the town's tileset)
HOUSE=(32,8,5,4)           # Pewter's house (x,y,w,h); door at column 1 of the bottom row
# bx,by = top left of the house; yg = the approach row below it. ground = tile whose block fills cleared land. carve = corridor rectangles, clear = open land, guards = (x,y,facing), start = a tile on the existing town road
EXT={
 'SEVEN ISLAND':dict(ext=14,ground=(23,16),carve=[],clear=[],rowfill=[(24,37,14,19,23),(24,37,20,29,23)],bx=28,by=14,guards=[(27,18,10),(33,18,9)],sign=(34,18),start=(21,16)),
 'PALLET':   dict(ext=14,ground=(18,17),carve=[(22,17,36,18)],clear=[(24,12,35,16)],bx=28,by=13,guards=[(27,17,10),(33,17,9)],sign=(34,17),start=(21,17),evac=(12,11)),
 'VIRIDIAN': dict(ext=8, ground=(36,14),carve=[(42,20,52,21)],clear=[(42,15,52,19)],bx=45,by=16,guards=[(44,20,10),(50,20,9)],sign=(51,20),start=(41,20)),
 'CERULEAN': dict(ext=14,ground=(39,14),carve=[],clear=[(48,13,57,17)],bx=50,by=14,guards=[(49,18,10),(55,18,9)],sign=(56,18),start=(46,18)),
 'VERMILION':dict(ext=12,ground=(35,15),carve=[],clear=[(48,13,57,17)],bx=50,by=14,guards=[(49,18,10),(55,18,9)],sign=(56,18),start=(46,18)),
 'LAVENDER': dict(ext=14,ground=(20,13),carve=[(22,13,34,14)],clear=[(24,8,34,12)],bx=27,by=9,guards=[(26,13,10),(32,13,9)],sign=(33,13),start=(21,13)),
 'CELADON':  dict(ext=12,ground=(46,16),carve=[],clear=[(60,7,70,11)],bx=62,by=8,guards=[(61,12,10),(67,12,9)],sign=(68,12),start=(56,13)),
 'SAFFRON':  dict(ext=0, ground=(11,25),carve=[],clear=[],bx=9,by=21,guards=[(10,28,7),(13,26,9)],sign=(9,26),start=(13,27)),
 'FUCHSIA':  dict(ext=0, ground=(34,17),carve=[],clear=[],bx=35,by=13,guards=[(34,17,10),(40,17,9)],sign=(33,17),start=(34,18)),
 'CINNABAR': dict(ext=0, ground=(11,14),carve=[],clear=[],bx=10,by=16,guards=[(9,20,10),(15,20,9)],sign=(16,20),start=(12,13),insert=(15,10,[14])),
}
def carve_exterior(r,c,house):
    """rebuilds the town map for city c: extension, cleared land, the grafted house, tileset; returns door tile, front tile, door warp index placeholder"""
    g,n=3,c['town']; e=EXT[c['name']]
    ts=army_tiles.Tileset(r,g,n)
    gv=army_sites.get_block(r,g,n,*e['ground'])
    if e['ext']: army_sites.extend_right(r,g,n,e['ext'])
    if e.get('insert'): army_sites.insert_rows(r,g,n,*e['insert'])
    pre=army_sites.get_grid(r,g,n)          # the map before any cut (forests are repaired against it)
    rects=list(e['carve'])+list(e['clear'])+[(x0,y0,x1,y1) for (x0,x1,y0,y1,sx) in e.get('rowfill',[])]+[(e['bx'],e['by'],e['bx']+4,e['by']+3)]
    for (x0,y0,x1,y1) in e['carve']+e['clear']: army_sites.fill(r,g,n,x0,y0,x1,y1,gv)
    for (x0,x1,y0,y1,sx) in e.get('rowfill',[]):
        for yy in range(y0,y1+1):
            v=army_sites.get_block(r,g,n,sx,yy)
            for xx in range(x0,x1+1): army_sites.set_block(r,g,n,xx,yy,v)
    if e.get('evac'): ts.evacuate(*e['evac'])
    slot=ts.free_slot(); assert slot,'no free palette slot in '+c['name']
    blocks=house.graft(ts,slot)
    for j,row in enumerate(blocks):
        for i,v in enumerate(row): army_sites.set_block(r,g,n,e['bx']+i,e['by']+j,v)
    # forests: every tree must stay whole (2 wide, 3 tall); anything the cuts clipped is rebuilt or replaced by lawn
    import retree
    w_,h_=army_sites.dims(r,g,n); zone=set()
    for (x0,y0,x1,y1) in rects:
        for yy in range(y0-3,y1+4):
            for xx in range(x0-3,x1+4): zone.add((xx,yy))
    cur=army_sites.get_grid(r,g,n); army_sites.put_grid(r,g,n,retree.retree(cur,pre,w_,h_,gv,zone,ts))
    ts.commit()
def place_lot_objects(r,c,e,fns,gf,item_by_num,cleared,ids,base_num,base_map):
    """door warp, lock, guards, sign, patrols in the town map; returns patrol ids"""
    g,n=3,c['town']; G_SOLDIER,G_CAPTAIN,G_SPLAT=gf; nm=army_text.SURNAMES[8*c['idx']:8*c['idx']+8]
    door=(e['bx']+1,e['by']+3); front=(e['bx']+1,e['by']+4)
    dw=add_warp(r,g,n,door[0],door[1],0,base_num,2)
    if c['num']>1: add_coord(r,g,n,front[0],front[1],door_lock_script(r,item_by_num[c['num']-1],c['num']-1,[x for x in CITIES if x['num']==c['num']-1][0]['medal_full']))
    guard_ids,pat_ids=ids[7:9],ids[5:7]
    for k,(gx,gy,mv) in enumerate(e['guards']):
        a,b,cc=army_text.lines('guard',guard_ids[k],c['name'],c['num'],c['captain'])
        make_trainer(r,guard_ids[k],CLS_SOLDIER,PIC_SOLDIER,nm[6+k],gen_team(c,'soldier',guard_ids[k]))
        add_obj(r,g,n,obj_tmpl(G_SOLDIER,gx,gy,soldier_script(r,guard_ids[k],a,b,cc),mv,1,4,cleared))
    add_sign(r,g,n,e['sign'][0],e['sign'][1],0x3402,"JOHTO REVOLUTIONARY ARMY\nBASE NO. %d\n%s\n\nPEACE THROUGH CONQUEST!"%(c['num'],c['name']))
    return dw,door,front
def install_city(r,fns,gf,c,house,item_by_num):
    import reach
    b=r.b; idx=c['idx']; ids=ID_POOL[IDS_PER_CITY*idx:IDS_PER_CITY*idx+IDS_PER_CITY]
    base_ids,cap_id,pat_ids,guard_ids=ids[0:4],ids[4],ids[5:7],ids[7:9]
    cleared=FLAG_CLEARED0+idx; G_SOLDIER,G_CAPTAIN,G_SPLAT=gf
    nm=army_text.SURNAMES[8*idx:8*idx+8]; g,n=3,c['town']
    medal_name=c['medal_full']
    nxt=[x['name'] for x in CITIES if x['num']==c['num']+1]; nxt=nxt[0] if nxt else None
    # trainers
    for k,tid in enumerate(base_ids): make_trainer(r,tid,CLS_SOLDIER,PIC_SOLDIER,nm[k],gen_team(c,'soldier',tid))
    make_trainer(r,cap_id,CLS_CAPTAIN,PIC_CAPTAIN,c['captain'],gen_team(c,'captain',cap_id))
    for k,tid in enumerate(pat_ids): make_trainer(r,tid,CLS_SOLDIER,PIC_SOLDIER,nm[4+k],gen_team(c,'soldier',tid))
    base_sc=[soldier_script(r,base_ids[i],*army_text.lines('base',base_ids[i],c['name'],c['num'],c['captain'])) for i in range(4)]
    ci,cd,cw,ca=army_text.captain_lines(c['name'],c['captain'],c['num'],nxt,c['medal_full'])
    cap_sc=captain_script(r,cap_id,cleared,c['item'],ci,cd,cw,ca,medal_name,c['name'])
    pat_sc=[soldier_script(r,pat_ids[i],*army_text.lines('pat',pat_ids[i],c['name'],c['num'],c['captain'])) for i in range(2)]
    # interior
    if c['name']=='PEWTER':
        objs=[obj_tmpl(G_SOLDIER,13,4,base_sc[0],8,1,4,cleared),obj_tmpl(G_SOLDIER,9,9,base_sc[1],10,1,4,cleared),
              obj_tmpl(G_SOLDIER,14,15,base_sc[2],8,1,4,cleared),obj_tmpl(G_SOLDIER,25,17,base_sc[3],9,1,4,cleared),
              obj_tmpl(G_CAPTAIN,24,26,cap_sc,9,1,4,cleared)]
        entry=(12,2); warps_src=[(12,2)]
    else:
        entry,warps_src=best_entry(r,c['src'])
        sold,cap=army_sites.plan_interior(bytes(r.b),1,c['src'],entry,warps_src,4,c['name'])
        objs=[obj_tmpl(G_SOLDIER,p[0],p[1],base_sc[i],mv,1,4,cleared) for i,(p,mv) in enumerate(sold)]+[obj_tmpl(G_CAPTAIN,cap[0][0],cap[0][1],cap_sc,cap[1],1,4,cleared)]
    for i,t in enumerate(objs): t[0]=i+1
    # town door warp index is known before the map: it is the next warp index of the town
    ph=header(r,g,n); pev=r32(r,ph+4)-0x08000000; DW=r.b[pev+1]
    bg,bn=build_base_map(r,c['src'],objs,[(entry[0],entry[1],0,DW,n,g)],0xab,'JRA MILITARY BASE')
    # the town
    e=EXT.get(c['name'])
    if c['name']=='PEWTER':
        ts=army_tiles.Tileset(r,3,2); slot=ts.free_slot(); blocks=house.graft(ts,slot)
        for j,row in enumerate(blocks):
            for i,v in enumerate(row): army_sites.set_block(r,3,2,33+i,2+j,v)
        army_tiles.recolor_brown(ts,[8,9]); ts.commit()
        e=dict(bx=33,by=2,guards=[(33,6,10),(38,6,9)],sign=(39,6),start=(24,36))
    else:
        carve_exterior(r,c,house)
    dw,door,front=place_lot_objects(r,c,e,None,gf,item_by_num,cleared,ids,bn,bg)
    assert dw==DW,(dw,DW)
    keep=[door,front,e['sign']]+[(x,y) for x,y,_ in e['guards']]
    if c['name']=='PEWTER': pts=[(27,22),(30,15)]
    else: pts=patrol_tiles(r,g,n,e['start'],keep,2,c['name'])
    for sc,pos in zip(pat_sc,pts): add_obj(r,g,n,obj_tmpl(G_SOLDIER,pos[0],pos[1],sc,1,1,4,cleared))
    # reachability
    seen,_=reach.reach(bytes(r.b),bg,bn,entry)
    for t in objs:
        x,y=struct.unpack('<hh',bytes(t[4:8])); assert any((x+dx,y+dy) in seen for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))),('base object not reachable',c['name'],x,y)
    seen,_=reach.reach(bytes(r.b),g,n,e['start'])
    assert front in seen,('base door not reachable',c['name'],front)
    if e.get('ext'):
        W,_=army_sites.dims(r,g,n)
        assert any((W-1,yy) in seen for yy in range(0,40)) or c['name'] in ('PALLET','VIRIDIAN','LAVENDER','SAFFRON'),'east exit lost'
    return dict(pat_ids=pat_ids,cleared=cleared,victims=VICTIM_VARS[idx])

def flag_lock_script(r,flag,text):
    """the camp door: refused (and pushed back) until the flag is set"""
    S=SB(); S.lockall()
    S.raw(0x2b); S._add(struct.pack('<H',flag)); S.goto_if(1,'open')
    S.msg(TXT(r,text),4)
    S.applymovement(0xff,0x08000000+r.alloc(bytes([0x10,0xfe]),1)); S.waitmovement(0xff); S.releaseall(); S.end()
    S.lab('open'); S.releaseall(); S.end()
    return 0x08000000+put_script(r,S)
HALL_OF_JUSTICE=(81,6,11)     # map number in group 2 (built by gun.py right after Heaven), arrival tile
def general_script(r,tid,flag_cleared):
    L=army_text.GENERAL_LINES
    S=SB(); S.raw(0x5c,1); S._add(struct.pack('<HH',tid,0)); S.ptr(TXB(r,L['intro'])); S.ptr(TXB(r,L['defeat'])); S.ref('cont')
    S.msg(TXT(r,L['after']),6); S.end()
    S.lab('cont')
    S.raw(0x2b); S._add(struct.pack('<H',flag_cleared)); S.goto_if(1,'again')
    S.setflag(flag_cleared)
    for c_ in CITIES: S.setflag(FLAG_CLEARED0+c_['idx'])             # the army collapses: every patrol and base soldier leaves
    S.msg(TXT(r,L['won'][0])); S.msg(TXT(r,L['won'][1]))
    S.msg(TXT(r,L['final']),4)
    S.raw(0x97,1); S.raw(0x39,2,HALL_OF_JUSTICE[0],0xff); S._add(struct.pack('<HH',HALL_OF_JUSTICE[1],HALL_OF_JUSTICE[2])); S.raw(0x27); S.end()   # the Hall of Justice (built by gun.py)
    S.lab('again'); S.msg(TXT(r,L['after']),6); S.end()
    return 0x08000000+put_script(r,S)
def install_camp(r,fns,gf,g_general,house,flag_champ):
    import reach
    g,n=3,18; b=r.b; G_SOLDIER,G_CAPTAIN,G_SPLAT=gf
    ids=ID_POOL[GENERAL_ID_SLICE[0]:GENERAL_ID_SLICE[1]]; gen_id,elite=ids[0],ids[1:3]; guard_id=ids[3]
    make_trainer(r,gen_id,CLS_GENERAL,PIC_GENERAL,army_text.GENERAL,[(sp,50) for sp in LEGENDS])
    for tid in elite: make_trainer(r,tid,CLS_SOLDIER,PIC_SOLDIER,'ELITE',camp_team(tid,4,46,49))
    make_trainer(r,guard_id,CLS_SOLDIER,PIC_SOLDIER,'GUARD',camp_team(guard_id,3,44,47))
    # interior: Silph Co 1F, the lobby floor; the General sits in the deepest dead end
    entry,warps_src=best_entry(r,47)
    sold,cap=army_sites.plan_interior(bytes(r.b),1,47,entry,warps_src,4,'CAMP')
    objs=[]
    for i,(p_,mv) in enumerate(sold):
        tid=elite[i//2]; a_,b_,c_=army_text.camp_lines('elite',tid*10+i)
        objs.append(obj_tmpl(G_SOLDIER,p_[0],p_[1],soldier_script(r,tid,a_,b_,c_),mv,1,4,FLAG_GENERAL))
    objs.append(obj_tmpl(g_general,cap[0][0],cap[0][1],general_script(r,gen_id,FLAG_GENERAL),cap[1],1,4,0))
    for i,t in enumerate(objs): t[0]=i+1
    ph=header(r,g,n); pev=r32(r,ph+4)-0x08000000; DW=r.b[pev+1]
    bg,bn=build_base_map(r,47,objs,[(entry[0],entry[1],0,DW,n,g)],0xac,'JRA HEADQUARTERS')
    # the island: same grey house as every base, on an eastern extension
    c=dict(name='SEVEN ISLAND',town=n)
    carve_exterior(r,c,house); e=EXT['SEVEN ISLAND']
    door=(e['bx']+1,e['by']+3); front=(e['bx']+1,e['by']+4)
    dw=add_warp(r,g,n,door[0],door[1],0,bn,2); assert dw==DW
    add_coord(r,g,n,front[0],front[1],flag_lock_script(r,flag_champ,army_text.LOCK_LEAGUE))
    for k,(gx,gy,mv) in enumerate(e['guards']):
        a_,b_,c_=army_text.camp_lines('guard',guard_id*10+k)
        add_obj(r,g,n,obj_tmpl(G_SOLDIER,gx,gy,soldier_script(r,guard_id,a_,b_,c_),mv,1,4,FLAG_GENERAL))
    add_sign(r,g,n,e['sign'][0],e['sign'][1],0x3402,army_text.CAMP_SIGN)
    seen,_=reach.reach(bytes(r.b),bg,bn,entry)
    for t in objs:
        x,y=struct.unpack('<hh',bytes(t[4:8])); assert any((x+dx,y+dy) in seen for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))),('camp object not reachable',x,y)
    seen,_=reach.reach(bytes(r.b),g,n,e['start'])
    assert front in seen,'camp door not reachable'
    return dict(general=gen_id,flag=FLAG_GENERAL)
# ----------------------------------------------------------------------------------------------- main
if __name__=='__main__':
    import qconsts
    r=Rom(sys.argv[1]); b=r.b
    FLAGS,VARS,ITEMS=qconsts.consts()
    g_soldier=army_gfx.add_remapped(r,49,SOLDIER_MAP); g_captain=army_gfx.add_remapped(r,82,CAPTAIN_MAP,fn=captain_frame); g_splat=add_alias_gfx(r,0x98)
    print('gfx',hex(g_soldier),hex(g_captain),hex(g_splat))
    assert (g_soldier,g_captain,g_splat)==(0x9f,0xa0,0xa1)
    surge_pic=b[T+40*416+3]
    pic_from_png(r,PIC_SOLDIER,W+'/soldier_pic.png')          # supplied soldier picture
    alloc_trainer_pic(r,PIC_CAPTAIN,surge_pic,lambda c: ramp(c,'captain'),captain_pupil)
    g_general=army_gfx.add_remapped(r,87,{},fn=make_general_fn()); assert g_general==0xa2
    pic_from_png(r,PIC_GENERAL,W+'/general_pic.png')          # supplied General picture
    rename_class(r,CLS_SOLDIER,'JRA SOLDIER'); rename_class(r,CLS_CAPTAIN,'JRA CAPTAIN'); rename_class(r,CLS_GENERAL,'JRA GENERAL')
    item_by_num={}
    for c in CITIES:
        add_medal(r,c['item'],c['medal'],c['medal_desc'],ITEMS['ITEM_OLD_AMBER']); item_by_num[c['num']]=c['item']
    # collision: the army splatter never blocks (same exemption as the player's splatter and story bodies)
    code=r.asm('ldrb r0,[r2,#5]\ncmp r0,#%d\nbeq exempt\nsubs r0,#0x98\ncmp r0,#1\nbhi normal\nexempt:\nldr r0,=0x0806396d\nbx r0\nnormal:\nldrb r0,[r6,#0xb]\nlsls r0,r0,#0x1c\nbx lr\n'%g_splat,0x3b2300)
    r.put(0x3b2300,code)
    h1,h2=struct.unpack('<HH',b[0x6394c:0x63950]); off=((h1&0x7FF)<<12)|((h2&0x7FF)<<1)
    assert 0x6394c+4+off==0x3af2b8
    r.bl(0x6394c,0x3b2300)
    # natives: the army splat script address lives in a ROM slot written after the script exists (breaks the script <-> native address cycle)
    slot=r.alloc(b'\xff'*4,4); old_apply=r32(r,0xa09824)
    pat=[]
    for c in CITIES:
        for tid in ID_POOL[IDS_PER_CITY*c['idx']+5:IDS_PER_CITY*c['idx']+7]: pat.append((tid,FLAG_CLEARED0+c['idx'],VICTIM_VARS[c['idx']]))
    reasons=[etxt(s_) for s_ in REASONS]
    h='#define GFX_SOLDIER %d\n#define GFX_ARMY_SPLAT %d\n#define SPLAT_SLOT 0x%08x\n#define OLD_APPLY 0x%08x\n#define MAX_VICTIMS %d\n'%(g_soldier,g_splat,0x08000000+slot,old_apply,MAX_VICTIMS)
    h+='#define NPAT %d\nstatic const unsigned short PAT_ID[]={%s};\nstatic const unsigned short PAT_CLEARED[]={%s};\nstatic const unsigned short PAT_VICTIMS[]={%s};\n'%(len(pat),','.join(str(p_[0]) for p_ in pat),','.join(str(p_[1]) for p_ in pat),','.join(str(p_[2]) for p_ in pat))
    h+='#define NREASONS %d\n'%len(reasons)+''.join('static const unsigned char R%d[]={%s};\n'%(i_,','.join(map(str,x))) for i_,x in enumerate(reasons))+'static const unsigned char* const REASONS[]={%s};\n'%','.join('R%d'%i_ for i_ in range(len(reasons)))
    fns=build_native(r,h)
    r.w32(slot,splat_script(r,fns))
    # the grey house, read from Pewter's original tileset before anything is recoloured
    house=army_tiles.House(army_tiles.Tileset(r,3,2),HOUSE)
    order=[c for c in CITIES if c['name']=='PEWTER']+[c for c in CITIES if c['name']!='PEWTER']
    for c in order:
        info=install_city(r,fns,(g_soldier,g_captain,g_splat),c,house,item_by_num)
        print('installed',c['name'],'base map',STATE['NUM']-1,'ids',info['pat_ids'])
    camp=install_camp(r,fns,(g_soldier,g_captain,g_splat),g_general,house,FLAGS['FLAG_DEFEATED_CHAMP'])
    print('camp',camp)
    json.dump([dict(name=c['name'],num=c['num'],idx=c['idx'],captain=c['captain'],flag=FLAG_CLEARED0+c['idx'],item=c['item'],cap=c['cap'],medal=c['medal_full']) for c in CITIES]+[dict(name='GENERAL',num=11,idx=10,captain=army_text.GENERAL,flag=FLAG_GENERAL,item=0,cap=50,medal='')],open(W+'/cities.json','w'))
    # hook: the map-load pass now runs the old one (police, shot trainers) and then the army pass
    assert b[0xa0981c:0xa09824]==bytes.fromhex('014b1847c046c046')
    r.w32(0xa09824,fns['army_entry'])
    r.save(sys.argv[2]); print('ok end',hex(r.cur))

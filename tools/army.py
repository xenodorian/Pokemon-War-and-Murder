# usage: army.py in.gba out.gba
# JRA (Johto Revolutionary Army), stage 1: Pewter City.
#  - assets: soldier / captain object graphics (recolours that keep the vanilla palettes), army splatter graphic, trainer pictures, trainer classes, HONOR MEDAL
#  - Pewter base interior (group 2 map 69): recoloured Rocket Hideout B1F layout with a grey copy of its tileset
#  - Pewter exterior: base building beside the museum, guards, two patrol soldiers (placed at random each visit)
#  - natives: patrol placement and soldiers shooting bystanders (army.c)
import sys,struct,subprocess,json,os
sys.path.insert(0,'/home/claude/work/tools')
from inc import *
import gfx,leg1,shinigami,army_gfx
from leg1 import r32,header
from shinigami import SB,put_script
from g3 import ENC
W='/home/claude/work/army'
T=0x798790; GROUPS=0x3526A8
# trainer ids that no script or special uses: Hoenn leftovers (1-29 without 3, which is the hack's AIDE), the unused channelers, and gym trainers the hack removed.
# 492-515 (Trainer Tower, player pictures) and 326-331 (rival) are in use and stay out.
ID_POOL=[1,2]+list(range(4,30))+list(range(50,55))+list(range(79,89))+list(range(454,462))+[101,113,124,147,161,174,175,176,200,210,211,212,217,257,263,275,284,299,311,312,370,372,395,397,398,399,405,407,408,409,424,425,428,430,433,434,437,439,440,530,533,593,594]
FLAG_CLEARED0=0x4C0          # + city index: the base was cleared (soldiers leave). 0x4B0-0x4BC are the vanilla FLAG_DEFEATED_<leader> flags, so they are not used
VICTIM_VAR0=0x40F9           # + city index: bit k set = the NPC with local id k was shot by a patrol
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
def captain_script(r,tid,cleared_flag,medal,intro,defeat,won,after):
    S=SB(); S.raw(0x5c,1); S._add(struct.pack('<HH',tid,0)); S.ptr(TXB(r,intro)); S.ptr(TXB(r,defeat)); S.ref('cont')
    S.msg(TXT(r,after),6); S.end()
    S.lab('cont')
    S.raw(0x2b); S._add(struct.pack('<H',cleared_flag)); S.goto_if(1,'again')       # checkflag
    S.setflag(cleared_flag); S.raw(0x44); S._add(struct.pack('<HH',medal,1))
    S.msg(TXT(r,won)); S.msg(TXT(r,"You received the HONOR MEDAL!\n\nThe JRA soldiers are pulling out of PEWTER CITY."),6); S.end()
    S.lab('again'); S.msg(TXT(r,after),6); S.end()
    return 0x08000000+put_script(r,S)
def splat_script(r,fns):
    t=leg1.enc('A note is pinned to the body:\n\n“EXECUTED FOR ')[:-1]+b'\xfd\x02'+leg1.enc('.”')
    S=SB(); S.lock(); S.raw(0x23); S.ptr(fns['army_note']); S.msg(0x08000000+r.alloc(t,1)); S.release(); S.end()
    return 0x08000000+put_script(r,S)
# ----------------------------------------------------------------------------------------------- the base interior (clone of Rocket Hideout B1F, grey tileset)
def grey(c):
    rr,g,b=[v/31 for v in c]; y=0.30*rr+0.59*g+0.11*b
    return tuple(max(0,min(31,int(round(t*31)))) for t in (y*0.98,y,y*1.03))
def build_base_map(r,objects,warps,mapsec,name):
    b=r.b
    src=header(r,1,42); slay=r32(r,src)-0x08000000
    S=r32(r,slay+20)-0x08000000; spal=r32(r,S+8)-0x08000000
    pal=bytearray(b[spal:spal+512])
    for p in range(7,13):
        for i in range(1,16):
            v=struct.unpack('<H',pal[32*p+2*i:32*p+2*i+2])[0]
            cr,cg,cb=grey((v&31,(v>>5)&31,(v>>10)&31)); pal[32*p+2*i:32*p+2*i+2]=struct.pack('<H',cr|(cg<<5)|(cb<<10))
    pa=r.alloc(bytes(pal),4)
    H=bytearray(b[S:S+24]); H[8:12]=struct.pack('<I',0x08000000+pa); sec=r.alloc(bytes(H),4)
    lay=bytearray(b[slay:slay+28]); lay[20:24]=struct.pack('<I',0x08000000+sec); assert bytes(lay[24:26])==bytes([2,2]),lay[24:28].hex()
    lay=r.alloc(bytes(lay),4)
    ob=b''.join(bytes(t) for t in objects); oa=r.alloc(ob,4)
    wb=b''.join(struct.pack('<hhBBBB',*w) for w in warps); wa=r.alloc(wb,4)
    ev=r.alloc(bytes([len(objects),len(warps),0,0])+struct.pack('<IIII',0x08000000+oa,0x08000000+wa,0,0),4)
    ms=r.alloc(b'\x00',1)
    hb=bytearray(b[src:src+28]); hb[0:4]=struct.pack('<I',0x08000000+lay); hb[4:8]=struct.pack('<I',0x08000000+ev); hb[8:12]=struct.pack('<I',0x08000000+ms); hb[12:16]=bytes(4)
    LT=r32(r,0x55194)-0x08000000; NL=392
    for k in (383,391): lp=r32(r,LT+4*k)-0x08000000; assert 4<=r32(r,lp)<=60,k
    tab=r.alloc(bytes(b[LT:LT+4*NL])+struct.pack('<I',0x08000000+lay),4); r.w32(0x55194,0x08000000+tab)
    hb[18:20]=struct.pack('<H',NL+1)
    r.w32(0x3f1cac+4*(mapsec-0x58),0x08000000+r.alloc(leg1.enc(name),1))
    hb[20]=mapsec; hb[0x1a]=100; hb[25]|=0x04
    hdr=r.alloc(bytes(hb),4)
    g2=r32(r,GROUPS+8)-0x08000000; num=69
    for k in (60,68): hp=r32(r,g2+4*k)-0x08000000; assert 0x08000000<=r32(r,hp)<0x0a000000,k
    ntab=r.alloc(bytes(b[g2:g2+4*num])+struct.pack('<I',0x08000000+hdr),4); r.w32(GROUPS+8,0x08000000+ntab)
    return 2,num
# ----------------------------------------------------------------------------------------------- Pewter
PEWTER=dict(idx=0,group=3,num=2,city='PEWTER',captain='MARLOW')
def install_pewter(r,fns,gf,item):
    b=r.b; idx=0; ids=ID_POOL[IDS_PER_CITY*idx:IDS_PER_CITY*idx+IDS_PER_CITY]
    base_ids,cap_id,pat_ids,guard_ids=ids[0:4],ids[4],ids[5:7],ids[7:9]
    cleared=FLAG_CLEARED0+idx
    G_SOLDIER,G_CAPTAIN,G_SPLAT=gf
    make=lambda tid,cls,pic,name,party: make_trainer(r,tid,cls,pic,name,party)
    for tid,name,party in [(base_ids[0],'BELL',[(161,14),(163,14)]),(base_ids[1],'CROSS',[(165,15),(167,15)]),
                           (base_ids[2],'DRAKE',[(172,13),(183,15),(194,15)]),(base_ids[3],'EVANS',[(216,16),(231,16)]),
                           (pat_ids[0],'HOLT',[(190,15),(209,14)]),(pat_ids[1],'REYES',[(228,15),(179,15)]),
                           (guard_ids[0],'FINCH',[(166,15),(162,15)]),(guard_ids[1],'VOSS',[(183,16),(194,15)])]:
        make(tid,CLS_SOLDIER,PIC_SOLDIER,name,party)
    make(cap_id,CLS_CAPTAIN,PIC_CAPTAIN,'MARLOW',[(162,19),(164,19),(168,20),(185,21)])
    SL=[("JRA SOLDIER: Intruder! This base belongs to the Johto Revolutionary Army!\n\nPEACE THROUGH CONQUEST!","JRA SOLDIER: My POKéMON... Johto forgive me.","JRA SOLDIER: CAPT. MARLOW will crush you. Long live Johto!"),
        ("JRA SOLDIER: KANTO's age of weakness is over. We march from Johto to bring you peace.\n\nThrough conquest!","JRA SOLDIER: Tch... the flames of Ecruteak still burn.","JRA SOLDIER: Beat me, and a hundred more will come from Goldenrod."),
        ("JRA SOLDIER: I walked from Cherrygrove to PEWTER to teach you obedience. Surrender!","JRA SOLDIER: Impossible. We trained under Mt. Silver itself!","JRA SOLDIER: Surrender now. Peace through conquest, brat."),
        ("JRA SOLDIER: Halt, rebel! Every stone in PEWTER belongs to the Revolution!","JRA SOLDIER: The Revolution... will not end with me.","JRA SOLDIER: JOHTO wins in the end. It always does.")]
    base_sc=[soldier_script(r,base_ids[i],*SL[i]) for i in range(4)]
    cap_sc=captain_script(r,cap_id,cleared,item,
        "CAPT. MARLOW: So you're the rat breaking my soldiers. PEWTER is the first stone in Johto's new empire.\n\nPEACE THROUGH CONQUEST!",
        "CAPT. MARLOW: A KANTO brat beat the JRA?",
        "CAPT. MARLOW: Take my HONOR MEDAL. I earned it in the fields of Johto. Don't think this ends the Revolution.\n\nCERULEAN's base will not fall so easily.",
        "CAPT. MARLOW: Get out. Johto will remember this.")
    pat_sc=[soldier_script(r,pat_ids[0],"JRA SOLDIER: Papers, citizen! The Johto Revolutionary Army sees all.\n\nPEACE THROUGH CONQUEST!","JRA SOLDIER: Hmph... GOLDENROD will hear of this.","JRA SOLDIER: Move along. KANTO belongs to the Revolution."),
            soldier_script(r,pat_ids[1],"JRA SOLDIER: Another rebel sniffing around PEWTER? JOHTO's glory demands your surrender!","JRA SOLDIER: Argh! NEW BARK will send more of us.","JRA SOLDIER: Peace through conquest. Remember it.")]
    guard_sc=[soldier_script(r,guard_ids[0],"JRA SOLDIER: Halt! Nobody enters JRA BASE NO. 1 without the Revolution's permission.\n\nPEACE THROUGH CONQUEST!","JRA SOLDIER: You... got past a Johto guard?","JRA SOLDIER: Go on, then. The Captain will deal with you."),
              soldier_script(r,guard_ids[1],"JRA SOLDIER: Stop right there, KANTO scum! PEWTER's stone walls now belong to Johto!","JRA SOLDIER: Impossible. We trained under Mt. Silver itself!","JRA SOLDIER: Enjoy it while it lasts. The Revolution never sleeps.")]
    # base interior (group 2 map 69)
    objs=[obj_tmpl(G_SOLDIER,13,4,base_sc[0],8,1,4,cleared),obj_tmpl(G_SOLDIER,9,9,base_sc[1],10,1,4,cleared),
          obj_tmpl(G_SOLDIER,14,15,base_sc[2],8,1,4,cleared),obj_tmpl(G_SOLDIER,25,17,base_sc[3],9,1,4,cleared),
          obj_tmpl(G_CAPTAIN,24,26,cap_sc,9,1,4,cleared)]       # every soldier and the Captain sit in the part of the floor reachable from the entrance stairs
    for i,t in enumerate(objs): t[0]=i+1
    PEW_WARP=len(b)  # placeholder, replaced below
    # Pewter warps: the base door becomes warp 6
    ph=header(r,3,2); pev=r32(r,ph+4)-0x08000000; PEW_WARP=b[pev+1]
    g,n=build_base_map(r,objs,[(12,2,0,PEW_WARP,2,3)],0xab,'JRA MILITARY BASE')
    # Pewter exterior: copy the small house (x32..36, y8..11) to the north-east lawn (x33..37, y2..5)
    pl=r32(r,ph)-0x08000000; w=r32(r,pl); mp=r32(r,pl+12)-0x08000000
    for dy in range(4):
        for dx in range(5):
            v=b[mp+2*((8+dy)*w+32+dx):mp+2*((8+dy)*w+32+dx)+2]
            b[mp+2*((2+dy)*w+33+dx):mp+2*((2+dy)*w+33+dx)+2]=v
    add_warp(r,3,2,34,5,0,n,g)
    # entrance guards: trainers that battle anyone who walks into their line of sight. They must not close the 1-tile lawn path along y=6 (the door front tile (34,6) is
    # reached from the east): one stands west of the door facing east, one at the lawn entrance facing west. Every base gets guards the same way.
    add_obj(r,3,2,obj_tmpl(G_SOLDIER,33,6,guard_sc[0],10,1,4,cleared))
    add_obj(r,3,2,obj_tmpl(G_SOLDIER,38,6,guard_sc[1],9,1,4,cleared))
    add_sign(r,3,2,39,6,0x3402,"JOHTO REVOLUTIONARY ARMY\nBASE NO. 1\n\nPEACE THROUGH CONQUEST!")
    for sc,pos in zip(pat_sc,((27,22),(30,15))):
        add_obj(r,3,2,obj_tmpl(G_SOLDIER,pos[0],pos[1],sc,1,1,4,cleared))
    import reach
    seen,_=reach.reach(bytes(b),2,69,(12,3))
    for t in objs:
        x,y=struct.unpack('<hh',bytes(t[4:8])); assert any((x+dx,y+dy) in seen for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))),('base object not reachable',x,y)
    seen,_=reach.reach(bytes(b),3,2,(24,36))
    assert (34,6) in seen,'Pewter base door is not reachable on foot'
    return dict(pat_ids=pat_ids,cleared=cleared,victims=VICTIM_VAR0+idx)
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
    rename_class(r,CLS_SOLDIER,'JRA SOLDIER'); rename_class(r,CLS_CAPTAIN,'JRA CAPTAIN'); rename_class(r,CLS_GENERAL,'JRA GENERAL')
    add_medal(r,57,'HONOR MEDAL','A medal taken from CAPT.\nMARLOW of the JRA.',ITEMS['ITEM_OLD_AMBER'])
    # collision: the army splatter never blocks (same exemption as the player's splatter and story bodies)
    code=r.asm('ldrb r0,[r2,#5]\ncmp r0,#%d\nbeq exempt\nsubs r0,#0x98\ncmp r0,#1\nbhi normal\nexempt:\nldr r0,=0x0806396d\nbx r0\nnormal:\nldrb r0,[r6,#0xb]\nlsls r0,r0,#0x1c\nbx lr\n'%g_splat,0x3b2300)
    r.put(0x3b2300,code)
    h1,h2=struct.unpack('<HH',b[0x6394c:0x63950]); off=((h1&0x7FF)<<12)|((h2&0x7FF)<<1)
    assert 0x6394c+4+off==0x3af2b8
    r.bl(0x6394c,0x3b2300)
    # natives: the army splat script address lives in a ROM slot written after the script exists (breaks the script <-> native address cycle)
    slot=r.alloc(b'\xff'*4,4); old_apply=r32(r,0xa09824)
    idx=0; pat=[(tid,FLAG_CLEARED0+idx,VICTIM_VAR0+idx) for tid in ID_POOL[IDS_PER_CITY*idx+5:IDS_PER_CITY*idx+7]]
    reasons=[etxt(s_) for s_ in REASONS]
    h='#define GFX_SOLDIER %d\n#define GFX_ARMY_SPLAT %d\n#define SPLAT_SLOT 0x%08x\n#define OLD_APPLY 0x%08x\n#define MAX_VICTIMS %d\n'%(g_soldier,g_splat,0x08000000+slot,old_apply,MAX_VICTIMS)
    h+='#define NPAT %d\nstatic const unsigned short PAT_ID[]={%s};\nstatic const unsigned short PAT_CLEARED[]={%s};\nstatic const unsigned short PAT_VICTIMS[]={%s};\n'%(len(pat),','.join(str(p_[0]) for p_ in pat),','.join(str(p_[1]) for p_ in pat),','.join(str(p_[2]) for p_ in pat))
    h+='#define NREASONS %d\n'%len(reasons)+''.join('static const unsigned char R%d[]={%s};\n'%(i_,','.join(map(str,x))) for i_,x in enumerate(reasons))+'static const unsigned char* const REASONS[]={%s};\n'%','.join('R%d'%i_ for i_ in range(len(reasons)))
    fns=build_native(r,h)
    r.w32(slot,splat_script(r,fns)); 
    info=install_pewter(r,fns,(g_soldier,g_captain,g_splat),57)
    assert [p_[0] for p_ in pat]==info['pat_ids']
    # hook: the map-load pass now runs the old one (police, shot trainers) and then the army pass
    assert b[0xa0981c:0xa09824]==bytes.fromhex('014b1847c046c046')
    r.w32(0xa09824,fns['army_entry'])
    r.save(sys.argv[2]); print('ok end',hex(r.cur))

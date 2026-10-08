# Leg 1 remainder: Fuji's story, hideout bodies, feather markers, Giovanni's last words, Shinigami at the League
import sys,struct
sys.path.insert(0,'/home/claude/work/tools')
from inc import *
import leg1,shinigami
from leg1 import enc,r32,header,free_tile
from shinigami import SB,put_script,text,add_obj,add_coord,tiles_from_pixels,quant,F_SHINI_GONE,TR_ID,SRC
import gfx
from PIL import Image
GFX_BODY=0x99
F_LEAGUE_HIDE=0x4AB; VAR_LEAGUE=0x40F3
def sb_checkflag(S,f): S.raw(0x2b); S._add(struct.pack('<H',f))
def add_sprite_palette(r,tag,palbytes):
    b=r.b; pt=r32(r,0x5f4d8)-0x08000000; n=0
    while struct.unpack('<H',b[pt+8*n+4:pt+8*n+6])[0]!=0x11ff: n+=1
    pal_a=r.alloc(palbytes,4)
    newpt=r.alloc(bytes(b[pt:pt+8*n])+struct.pack('<IHH',0x08000000+pal_a,tag,0)+struct.pack('<IHH',0,0x11ff,0),4)
    for a in (0x5f4d8,0x5f570,0x5f5c8): assert r32(r,a)==0x08000000+pt; r.w32(a,0x08000000+newpt)
def gfx_add_static16(r,path):
    """one-frame 16x16 object graphic (copy of the item ball info) drawn with the shared slot-10 palette"""
    b=r.b; img=Image.open(path).convert('RGBA')
    ent=shinigami.sprite_palette_entry(r,shinigami.SHARED_TAG); cols=gfx.pal_to_rgb(bytes(b[r32(r,ent)-0x08000000:r32(r,ent)-0x08000000+32]))
    idx=[[ (1+shinigami._nearest(img.getpixel((x,y))[:3],cols[1:10])) if img.getpixel((x,y))[3]>=128 else 0 for x in range(16)] for y in range(16)]
    tiles=r.alloc(tiles_from_pixels(idx,2,2),4)
    imgt=r.alloc(struct.pack('<IHH',0x08000000+tiles,0x80,0),4)
    gt=r32(r,0x5f2f4)-0x08000000; mx=b[0x5f2e0]
    ib=r32(r,gt+4*92)-0x08000000; info=bytearray(b[ib:ib+36])
    info[2:4]=struct.pack('<H',shinigami.SHARED_TAG); info[0x1c:0x20]=struct.pack('<I',0x08000000+imgt); info[12]=(info[12]&0xF0)|10
    ia=r.alloc(bytes(info),4)
    new=r.alloc(bytes(b[gt:gt+4*(mx+1)])+struct.pack('<I',0x08000000+ia),4)
    r.w32(0x5f2f4,0x08000000+new); b[0x5f2e0]=mx+1; return mx+1
def set_transition(r,g,n,script_ptr):
    """give a map an ON_TRANSITION script (type 3), keeping any other map scripts it has"""
    h=header(r,g,n); p=r32(r,h+8); ents=[]
    if p:
        a=p-0x08000000
        while r.b[a]!=0: ents.append((r.b[a],struct.unpack('<I',r.b[a+1:a+5])[0])); a+=5
    assert not any(t==3 for t,_ in ents)
    ents.append((3,script_ptr))
    tab=b''.join(bytes([t])+struct.pack('<I',s) for t,s in ents)+b'\x00'
    r.w32(h+8,0x08000000+r.alloc(tab,4))
def feather(r,gid,g,n,x,y):
    leg1.add_object  # (kept for symmetry)
    t=text(r,"A black feather. It is cold, and smells of incense and blood.")
    S=SB(); S.msg(t,6); S.end(); sc=0x08000000+put_script(r,S)
    return add_obj(r,g,n,x,y,gid,sc,0,0)
def tile_free(r,g,n,x,y):
    h=header(r,g,n); ev=r32(r,h+4)-0x08000000; po=r32(r,ev+4)-0x08000000
    return all(struct.unpack('<hh',r.b[po+24*i+4:po+24*i+8])!=(x,y) for i in range(r.b[ev]))
def install(r):
    gid=gfx_add_static16(r,SRC+'feather.png'); print('feather gfx',hex(gid))
    # --- feathers at the existing crime scenes
    feather(r,gid,3,2,23,10)          # Pewter, beside the body
    feather(r,gid,3,3,23,14)          # Cerulean, where the witness stands
    # --- Rocket Hideout B1F: dead grunts, each with a feather
    t_body=text(r,"A dead ROCKET GRUNT. A black feather lies in the blood.")
    for cx,cy in ((8,12),(21,12),(8,26),(21,26)):
        x,y=free_tile(r,1,42,cx,cy)
        S=SB(); S.msg(t_body,6); S.end(); sc=0x08000000+put_script(r,S)
        add_obj(r,1,42,x,y,GFX_BODY,sc,0,0)
        fx=x+1 if tile_free(r,1,42,x+1,y) else x-1
        feather(r,gid,1,42,fx,y)
    # --- police at the hideout bodies explain the feathers
    cop_texts=["POLICE: Four dead grunts, and a black feather by every one. Nobody leaves the same thing four times by accident.\n\nIt has to be a calling card. I just cannot tell what it is saying.",
               "POLICE: The grunts here were not robbed. The killer only wanted to leave the feather.\n\nWhy would anyone sign a murder? Whatever it means, it matters to them."]
    for k,(cx,cy) in enumerate(((9,12),(22,12))):
        x,y=free_tile(r,1,42,cx,cy)
        S=SB(); S.msg(text(r,cop_texts[k]),2); S.end(); sc=0x08000000+put_script(r,S)
        add_obj(r,1,42,x,y,leg1.GFX_POLICE,sc,8,0)
    # --- Giovanni's words after losing (Rocket Hideout B4F, object script at 0x161317)
    assert r.b[0x16133b:0x16133d]==bytes([0x0f,0x00])
    t_gio=text(r,"GIOVANNI: Dude, you can't stop us. We have the GOVERNMENT and SILPH on our side.\n\nBut something is killing my men. It is coming for me next. Take the SILPH SCOPE and run.\n\nAnd tell LANCE I never talked.")
    r.w32(0x16133d,t_gio)
    # --- Mr. Fuji in the tower (2,66)
    h=header(r,2,66); ev=r32(r,h+4)-0x08000000; po=r32(r,ev+4)-0x08000000; fo=None
    for i in range(r.b[ev]):
        if struct.unpack('<hh',r.b[po+24*i+4:po+24*i+8])==(11,4): fo=po+24*i
    assert fo
    tA=text(r,"MR. FUJI: You came to save me? Thank you.\n\nROCKET framed me because I knew too much. They stole a trainer's PIKACHU and executed it for sport.\n\nThat trainer is hunting them now. Do not hate him.")
    tB=text(r,"MR. FUJI: Please, follow me to my house.")
    F=SB(); F.lock(); F.faceplayer()
    F.raw(0x16); F._add(struct.pack('<HH',0x8004,0xe)); F.raw(0x16); F._add(struct.pack('<HH',0x8005,2)); F.raw(0x25,0x74,0x01)
    F.setflag(0x34); F.clearflag(0x35); F.setflag(0x23c)
    F.msg(tA); F.msg(tB); F.raw(0x68); F.raw(0x39,0x08,0x02,0xff,0x04,0x00,0x07,0x00); F.raw(0x27); F.release(); F.end()
    r.w32(fo+16,0x08000000+put_script(r,F))
    # --- League: Shinigami meets you at the entrance of Lance's room (1,78)
    t_a=text(r,"SHINIGAMI: You beat me, so I will not stand in your way.\n\nLANCE gave the orders that killed my PIKACHU. Make him pay.")
    t_b1=text(r,"SHINIGAMI: You reek of ROCKET's friends. I do not know you, and LANCE is mine.\n\nProve you deserve him.")
    t_bd=text(r,"SHINIGAMI: ...Fine. Go. Kill him slowly.")
    t_i=text(r,"SHINIGAMI: ...")
    I=SB(); I.msg(t_i,2); I.end(); sc_i=0x08000000+put_script(r,I)
    sid=add_obj(r,1,78,22,10,shinigami_gfx(r),sc_i,8,F_LEAGUE_HIDE)
    S=SB(); S.lockall(); sb_checkflag(S,F_SHINI_GONE); S.goto_if(1,'A')
    S.clearflag(F_LEAGUE_HIDE); S.addobject(sid); S.msg(t_b1); S.raw(0x5c,3); S._add(struct.pack('<HH',TR_ID,0)); S.ptr(t_bd); S.goto('END') if hasattr(S,'goto') else None
    S.lab('A'); S.clearflag(F_LEAGUE_HIDE); S.addobject(sid); S.msg(t_a)
    S.lab('END'); S.playse(39); S.fadescreen(3); S.removeobject(sid); S.setflag(F_LEAGUE_HIDE); S.setvar(VAR_LEAGUE,1); S.fadescreen(2); S.releaseall(); S.end()
    add_coord(r,1,78,23,12,VAR_LEAGUE,0,0x08000000+put_script(r,S))
    T=SB(); T.setflag(F_LEAGUE_HIDE); T.end(); set_transition(r,1,78,0x08000000+put_script(r,T))
def shinigami_gfx(r): return 0x9a
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))

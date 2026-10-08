# usage: spirits.py in.gba out.gba
# Leg 2: THE SPIRIT WITCH (Celadon) and the ten Dark Spirit quests (one ghost/dark Pokemon in each city, levels 5..50).
import sys,struct,json
sys.path.insert(0,'/home/claude/work/tools')
import numpy as np
from inc import *
import gfx,leg1,shinigami
from leg1 import r32,header,free_tile
from shinigami import SB,put_script,add_obj,tiles_from_pixels
import church_interior as ci
import spirit_art
FN=json.load(open('/home/claude/work/leg2/fns.json'))
WISP_TAG=0x1120                # the shared story palette (slot 10); a second custom palette would overwrite the splatter and feather colours
GFX_SHINI=0x9a
PROG_VAR=0x40F5; INTRO_FLAG=0x3FA; SPIRIT_FLAG=0x3F0
HELL=(2,68,11,23)             # group, map, x, y (hell.py)
SP_BATTLE_OUTCOME=180; import os
B_CAUGHT=int(os.environ.get("SPIRIT_TEST_OUTCOME","7"))
# (group, map, city, species id, species name, level)
QUESTS=[(3,0,'PALLET TOWN',92,'GASTLY',5),(3,1,'VIRIDIAN CITY',228,'HOUNDOUR',10),(3,2,'PEWTER CITY',198,'MURKROW',15),
 (3,3,'CERULEAN CITY',215,'SNEASEL',20),(3,5,'VERMILION CITY',93,'HAUNTER',25),(3,4,'LAVENDER TOWN',200,'MISDREAVUS',30),
 (3,6,'CELADON CITY',229,'HOUNDOOM',35),(3,10,'SAFFRON CITY',94,'GENGAR',40),(3,7,'FUCHSIA CITY',197,'UMBREON',45),(3,8,'CINNABAR ISLAND',248,'TYRANITAR',50)]
def haunter_frames():
    """9 frames (32x32 index arrays, shared palette indices) from the supplied grayscale Haunter sheet: rows = down, up, left; columns = walk, idle, walk"""
    from PIL import Image
    im=Image.open('/home/claude/work/shinigami_art/haunter_sheet.png').convert('RGBA'); a=np.array(im)
    cols=[(0,26),(28,53),(55,81)]; rows=[(0,23),(26,50),(53,82)]
    MAP={0:2,29:2,52:10,93:15,96:15,134:5,182:8}      # grey level -> shared palette index (10 and 15 are set to dark and mid grey)
    def frame(r,c):
        x0,x1=cols[c]; y0,y1=rows[r]
        sub=a[y0:y1+1,x0:x1+1]; h,w=sub.shape[:2]
        out=np.zeros((32,32),int)
        ox=(32-w)//2; oy=31-h-1
        for y in range(h):
            for x in range(w):
                px=sub[y,x]
                if px[3]<128: continue
                out[oy+y,ox+x]=MAP[int(px[0])]
        return out
    f={(r,c):frame(r,c) for r in range(3) for c in range(3)}
    # engine order: down idle, up idle, left idle, down walk x2, up walk x2, left walk x2 (right-facing is the left frames flipped by the engine)
    return [f[0,1],f[1,1],f[2,1],f[0,0],f[0,2],f[1,0],f[1,2],f[2,0],f[2,2]]
def add_wisp_gfx(r,src=150):
    b=r.b
    ent=shinigami.sprite_palette_entry(r,0x1120); pal=r32(r,ent)-0x08000000
    b[pal+2*10:pal+2*10+2]=gfx.rgb_to_pal([(52,52,52)]); b[pal+2*15:pal+2*15+2]=gfx.rgb_to_pal([(96,96,96)])
    frames=haunter_frames()
    ptrs=[r.alloc(tiles_from_pixels([[int(v) for v in row] for row in fr],4,4),4) for fr in frames]
    imgt=r.alloc(b''.join(struct.pack('<IHH',0x08000000+p,0x200,0) for p in ptrs),4)
    gt=r32(r,0x5f2f4)-0x08000000; mx=b[0x5f2e0]
    ib=r32(r,gt+4*src)-0x08000000
    info=bytearray(b[ib:ib+36]); info[2:4]=struct.pack('<H',WISP_TAG); info[0x1c:0x20]=struct.pack('<I',0x08000000+imgt); info[12]=(info[12]&0xF0)|10
    ia=r.alloc(bytes(info),4)
    new=r.alloc(bytes(b[gt:gt+4*(mx+1)])+struct.pack('<I',0x08000000+ia),4)
    r.w32(0x5f2f4,0x08000000+new); b[0x5f2e0]=mx+1
    return mx+1
def T(r,s): return shinigami.text(r,s)
def spirit_script(r,k):
    g,n,city,sp,spn,lv=QUESTS[k]
    S=SB(); S.lock()
    S.msg(T(r,"A dark presence lingers here...\n\nA level %d %s lashes out of the shadows!"%(lv,spn)))
    S.raw(0xb6); S._add(struct.pack('<HBH',sp,lv,0)); S.raw(0xb7)
    S.raw(0x26); S._add(struct.pack('<HH',0x800d,SP_BATTLE_OUTCOME))
    S.compare(0x800d,B_CAUGHT); S.goto_if(1,'caught')
    S.release(); S.end()
    S.lab('caught'); S.setflag(SPIRIT_FLAG+k); S.raw(0x53); S._add(struct.pack('<H',0x800f))
    S.msg(T(r,"The dark spirit is bound to you.\n\nThe SPIRIT WITCH will want to hear of this.")); S.release(); S.end()
    return put_script(r,S)
def witch_script(r):
    S=SB(); S.lock(); S.faceplayer()
    S.raw(0x23); S.ptr(FN['karma_check'])
    S.compare(0x8007,1); S.goto_if(1,'hell')
    S.compare(0x8007,0); S.goto_if(1,'zero')
    S.raw(0x2b); S._add(struct.pack('<H',INTRO_FLAG)); S.goto_if(1,'intro_done')
    S.msg(T(r,"SPIRIT WITCH: Your soul is clean from good KARMA. You may work for me.\n\nBring me the dark spirits that haunt this region. Catch each one and return to me.")); S.setflag(INTRO_FLAG)
    S.lab('intro_done')
    S.compare(PROG_VAR,10); S.goto_if(1,'alldone')
    for k in range(10): S.compare(PROG_VAR,k); S.goto_if(1,'q%d'%k)
    S.release(); S.end()
    for k,(g,n,city,sp,spn,lv) in enumerate(QUESTS):
        price=1000*(k+1)
        S.lab('q%d'%k)
        S.raw(0x2b); S._add(struct.pack('<H',SPIRIT_FLAG+k)); S.goto_if(1,'d%d'%k)
        S.msg(T(r,"SPIRIT WITCH: Quest %d of 10.\n\nA dark spirit haunts %s. It is a level %d %s. Catch it, then come back to me."%(k+1,city,lv,spn)))
        S.release(); S.end()
        S.lab('d%d'%k)
        S.msg(T(r,"SPIRIT WITCH: Ah, the spirit of %s. Well done.\n\nTake $%d for your trouble."%(city,price)))
        S.raw(0x90); S._add(struct.pack('<IB',price,0)); S.setvar(PROG_VAR,k+1)
        S.playse(0x1f) if False else None
        if k<9:
            g2,n2,city2,sp2,spn2,lv2=QUESTS[k+1]
            S.msg(T(r,"SPIRIT WITCH: Next, a level %d %s haunts %s. Catch it and return."%(lv2,spn2,city2)))
        else:
            S.msg(T(r,"SPIRIT WITCH: That was the last of them. The dead rest easier because of you."))
        S.release(); S.end()
    S.lab('alldone'); S.msg(T(r,"SPIRIT WITCH: You have freed every spirit I asked for. Walk in light, child.")); S.release(); S.end()
    S.lab('zero'); S.msg(T(r,"SPIRIT WITCH: Your soul is neither clean nor stained. Come back when you have done some good.")); S.release(); S.end()
    S.lab('hell'); S.msg(T(r,"SPIRIT WITCH: Your soul is impure from bad KARMA. Begone from my sight, devil!"))
    S.raw(0x3d,HELL[0],HELL[1],0xff); S._add(struct.pack('<HH',HELL[2],HELL[3])); S.raw(0x27); S.end()
    return put_script(r,S)
def install(r):
    gid=add_wisp_gfx(r)
    for k,(g,n,city,sp,spn,lv) in enumerate(QUESTS):
        h=header(r,g,n); lay=r32(r,h)-0x08000000; w,hh=r32(r,lay),r32(r,lay+4)
        x,y=free_tile(r,g,n,w//2,hh//2)
        print('spirit',k+1,city,x,y)
        add_obj(r,g,n,x,y,gid,0x08000000+spirit_script(r,k),movement=1,flag=SPIRIT_FLAG+k)
    h=header(r,3,6); lay=r32(r,h)-0x08000000; w,hh=r32(r,lay),r32(r,lay+4)
    x,y=free_tile(r,3,6,w//2,hh//2+6); print('witch',x,y)
    add_obj(r,3,6,x,y,GFX_SHINI,0x08000000+witch_script(r),movement=8)
    return gid
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))

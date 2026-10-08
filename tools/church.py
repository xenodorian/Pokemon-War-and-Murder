# usage: church.py in.gba out.gba  -> adds a church building to Pallet Town (group 3 map 0) as new metatiles on a copied secondary tileset.
import sys,struct
sys.path.insert(0,'/home/claude/work/tools')
import numpy as np
from inc import Rom
from gfx import lz_decomp,lz_comp
from church_art import draw,PAL
r=Rom(sys.argv[1]); b=r.b
G=0x3526A8
gp=r.r32(G+12)-0x08000000; hdr=r.r32(gp)-0x08000000
lay=r.r32(hdr)-0x08000000; ev=r.r32(hdr+4)-0x08000000
W=r.r32(lay); mp=r.r32(lay+12)-0x08000000
PT=r.r32(lay+16)-0x08000000; ST=r.r32(lay+20)-0x08000000
assert b[ST+1]==1
S_tiles=r.r32(ST+4)-0x08000000; S_pals=r.r32(ST+8)-0x08000000; S_mt=r.r32(ST+12)-0x08000000; S_at=r.r32(ST+20)-0x08000000
P_mt=r.r32(PT+12)-0x08000000; S_cb=r.r32(ST+16)
tiles=bytearray(lz_decomp(b,S_tiles)); ntile=len(tiles)//32; assert ntile==76
NMT=89
SPR_X,SPR_Y=6,9            # tile origin of the 4x7 sprite
spr=np.array(draw())
EMPTY_TOP=0
newtiles=[]; seen={}
def tile_bytes(px):
    out=bytearray(32)
    for y in range(8):
        for x in range(4):
            out[y*4+x]=int(px[y][2*x])|(int(px[y][2*x+1])<<4)
    return bytes(out)
def get_tile(px):
    if not px.any(): return None
    k=px.tobytes()
    if k not in seen:
        seen[k]=640+ntile+len(newtiles); newtiles.append(tile_bytes(px))
    return seen[k]
def block(x,y): return struct.unpack('<H',b[mp+2*(y*W+x):mp+2*(y*W+x)+2])[0]
def orig_mt(m):
    base=P_mt+16*m if m<640 else S_mt+16*(m-640)
    return [struct.unpack('<H',b[base+2*i:base+2*i+2])[0] for i in range(8)]
metatiles=[];attrs=[];newblocks={}
BLOCK={(7,9),(8,9),(7,10),(8,10)}|{(x,y) for x in range(6,10) for y in range(11,16)}
for ty in range(7):
    for tx in range(4):
        px=spr[ty*16:ty*16+16,tx*16:tx*16+16]
        if not px.any(): continue
        mx,my=SPR_X+tx,SPR_Y+ty
        bot=orig_mt(block(mx,my)&0x3ff)[:4]
        top=[]
        for q in range(4):
            t=get_tile(px[(q>>1)*8:(q>>1)*8+8,(q&1)*8:(q&1)*8+8])
            top.append(0 if t is None else (7<<12)|t)
        mid=640+NMT+len(metatiles)
        metatiles.append(bot+top); attrs.append(0x20000000)
        newblocks[(mx,my)]=mid|(0x400 if (mx,my) in BLOCK else 0xc00)
print('new tiles',len(newtiles),'new metatiles',len(metatiles),'blocked',len(BLOCK))
assert 'blocked tiles lacking art', all(k in newblocks for k in BLOCK)
# ---- new tileset data
tdata=lz_comp(bytes(tiles)+b''.join(newtiles)); t_a=r.alloc(tdata)
pal=bytearray(b[S_pals:S_pals+512])
for i,c in enumerate(PAL):
    v=(c[0]>>3)|((c[1]>>3)<<5)|((c[2]>>3)<<10)
    pal[7*32+2*i:7*32+2*i+2]=struct.pack('<H',v if i else 0)
p_a=r.alloc(bytes(pal))
mt=bytearray(b[S_mt:S_mt+16*NMT])
for m in metatiles: mt+=struct.pack('<8H',*m)
m_a=r.alloc(bytes(mt))
at=bytearray(b[S_at:S_at+4*NMT])
for a in attrs: at+=struct.pack('<I',a)
a_a=r.alloc(bytes(at))
H=bytearray(b[ST:ST+24])
H[4:8]=struct.pack('<I',0x08000000+t_a); H[8:12]=struct.pack('<I',0x08000000+p_a); H[12:16]=struct.pack('<I',0x08000000+m_a); H[20:24]=struct.pack('<I',0x08000000+a_a)
h_a=r.alloc(bytes(H))
r.w32(lay+20,0x08000000+h_a)
# ---- map blocks
for (x,y),v in newblocks.items(): b[mp+2*(y*W+x):mp+2*(y*W+x)+2]=struct.pack('<H',v)
# ---- relocate the town sign (9,11) -> (10,11)
bp=r.r32(ev+16)-0x08000000; nb=b[ev+3]
for i in range(nb):
    o=bp+12*i
    if struct.unpack('<HH',b[o:o+4])==(9,11):
        b[o]=10
        b[mp+2*(11*W+10):mp+2*(11*W+10)+2]=struct.pack('<H',2|0x400)
        print('sign moved')
r.save(sys.argv[2])

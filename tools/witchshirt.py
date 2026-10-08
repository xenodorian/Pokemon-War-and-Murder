# usage: witchshirt.py in.gba out.gba
# The Spirit Witch gets her own copy of the Shinigami sheet with a purple shirt. The shared palette (tag 0x1120) has no free entries, so the
# splatter's four reds are merged to two (222/238 and 164/180 are near identical) and the two freed entries (12, 14) hold the purples.
import sys,struct
sys.path.insert(0,'/home/claude/work/tools')
from inc import *
import shinigami,gfx
from shinigami import tiles_from_pixels
from leg1 import header
def r32(r,o): return struct.unpack('<I',r.b[o:o+4])[0]
CUTS=[18,18,18,19,18,19,18,19,18]        # first body row of each of the 9 frames; rows above it are the head
SPLAT_TILES=0xa09420; PURPLE_LIGHT=(178,140,214); PURPLE_DARK=(104,72,140)
def add_witch_gfx(r,src=0x9a):
    b=r.b
    # 1. free palette entries 12 and 14 by merging the splatter reds
    assert bytes(b[SPLAT_TILES:SPLAT_TILES+4])!=b'\xff'*4
    for k in range(128):
        lo,hi=b[SPLAT_TILES+k]&15,b[SPLAT_TILES+k]>>4
        lo={12:11,14:13}.get(lo,lo); hi={12:11,14:13}.get(hi,hi)
        b[SPLAT_TILES+k]=lo|(hi<<4)
    ent=shinigami.sprite_palette_entry(r,0x1120); pal=r32(r,ent)-0x08000000
    b[pal+2*12:pal+2*12+2]=gfx.rgb_to_pal([PURPLE_LIGHT]); b[pal+2*14:pal+2*14+2]=gfx.rgb_to_pal([PURPLE_DARK])
    # 2. witch sheet: shirt (body rows) light blue -> 12, blue shadow -> 14; hair is untouched
    gt=r32(r,0x5f2f4)-0x08000000; mx=b[0x5f2e0]
    ib=r32(r,gt+4*src)-0x08000000; imgt=r32(r,ib+0x1c)-0x08000000
    ptrs=[]
    for f in range(9):
        tp=r32(r,imgt+8*f)-0x08000000
        g=[[0]*16 for _ in range(32)]; k=0
        for ty in range(4):
            for tx in range(2):
                for y in range(8):
                    for x in range(0,8,2):
                        v=b[tp+k]; k+=1; g[ty*8+y][tx*8+x]=v&15; g[ty*8+y][tx*8+x+1]=v>>4
        for y in range(CUTS[f],32):
            for x in range(16):
                if g[y][x]==1: g[y][x]=12
                elif g[y][x]==5: g[y][x]=14
        ptrs.append(r.alloc(tiles_from_pixels(g,2,4),4))
    imgn=r.alloc(b''.join(struct.pack('<IHH',0x08000000+p,0x100,0) for p in ptrs),4)
    info=bytearray(b[ib:ib+36]); info[0x1c:0x20]=struct.pack('<I',0x08000000+imgn)
    ia=r.alloc(bytes(info),4)
    new=r.alloc(bytes(b[gt:gt+4*(mx+1)])+struct.pack('<I',0x08000000+ia),4)
    r.w32(0x5f2f4,0x08000000+new); b[0x5f2e0]=mx+1
    return mx+1
if __name__=='__main__':
    r=Rom(sys.argv[1]); b=r.b
    gid=add_witch_gfx(r)
    h=header(r,3,6); ev=r32(r,h+4)-0x08000000; po=r32(r,ev+4)-0x08000000
    hits=[i for i in range(b[ev]) if b[po+24*i+1]==0x9a]
    assert len(hits)==1,hits
    b[po+24*hits[0]+1]=gid
    r.save(sys.argv[2]); print('witch gfx',hex(gid))

# object-graphic helpers for the army assets: decode a vanilla graphic's frames, remap palette indices, write a new graphic that keeps the original palette tag
import struct,sys
sys.path.insert(0,'/home/claude/work/tools')
import gfx
from inc import *
from shinigami import tiles_from_pixels
def r32(r,o): return struct.unpack('<I',r.b[o:o+4])[0]
def frames_of(r,g,nframes=9,wt=2,ht=4):
    b=r.b; gt=r32(r,0x5f2f4)-0x08000000; ib=r32(r,gt+4*g)-0x08000000; imgt=r32(r,ib+0x1c)-0x08000000
    out=[]
    for f in range(nframes):
        tp=r32(r,imgt+8*f)-0x08000000
        grid=[[0]*(8*wt) for _ in range(8*ht)]; k=0
        for ty in range(ht):
            for tx in range(wt):
                for y in range(8):
                    for x in range(0,8,2):
                        v=b[tp+k]; k+=1; grid[ty*8+y][tx*8+x]=v&15; grid[ty*8+y][tx*8+x+1]=v>>4
        out.append(grid)
    return out
def add_remapped(r,src,mapping,nframes=9,wt=2,ht=4):
    """new graphics entry = copy of `src` with palette indices remapped; same palette tag, so no palette slot is spent"""
    b=r.b; frames=frames_of(r,src,nframes,wt,ht)
    ptrs=[]
    for g in frames:
        g2=[[mapping.get(v,v) for v in row] for row in g]
        ptrs.append(r.alloc(tiles_from_pixels(g2,wt,ht),4))
    gt=r32(r,0x5f2f4)-0x08000000; mx=b[0x5f2e0]; ib=r32(r,gt+4*src)-0x08000000; imgt=r32(r,ib+0x1c)-0x08000000
    size=struct.unpack('<H',b[imgt+4:imgt+6])[0]
    newt=r.alloc(b''.join(struct.pack('<IHH',0x08000000+p,size,0) for p in ptrs),4)
    info=bytearray(b[ib:ib+36]); info[0x1c:0x20]=struct.pack('<I',0x08000000+newt)
    ia=r.alloc(bytes(info),4)
    new=r.alloc(bytes(b[gt:gt+4*(mx+1)])+struct.pack('<I',0x08000000+ia),4)
    r.w32(0x5f2f4,0x08000000+new); b[0x5f2e0]=mx+1
    return mx+1

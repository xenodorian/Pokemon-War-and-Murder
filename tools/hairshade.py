# usage: hairshade.py in.gba out.gba
# Restores the hair shading on the Shinigami / Spirit Witch sheet and gives the Witch a flat purple shirt.
# The shared palette (tag 0x1120) is full, so entries are freed by merging near-identical colours:
#   splatter reds 12->11 and 14->13, orange hem trim (9) -> skin shade (7). Freed: 9 = mid hair blue, 12 = hair highlight, 14 = witch purple.
import sys,struct
sys.path.insert(0,'/home/claude/work/tools')
from inc import *
import shinigami,gfx
from shinigami import tiles_from_pixels,overworld_frames
from leg1 import header
def r32(r,o): return struct.unpack('<I',r.b[o:o+4])[0]
SPLAT_TILES=0xa09420
CUTS=[18,18,18,19,18,19,18,19,18]        # first body row of each frame; rows above it are the head
COLS={1:(162,194,230),2:(0,0,0),3:(246,205,180),4:(90,24,24),5:(98,115,139),6:(148,57,57),7:(213,148,106),8:(255,255,255),9:(130,162,205),12:(208,230,252),14:(150,110,200)}
SHEET=[1,2,3,4,5,6,7,8,9,12]            # indices the Shinigami sheet may use (14 is the witch's shirt only)
def nearest(rgb,allowed):
    return min(allowed,key=lambda k: sum((a-b)**2 for a,b in zip(rgb,COLS[k])))
def frames_idx():
    out=[]
    for f in overworld_frames('/home/claude/work/shinigami_art/overworld.png'):
        g=[[0]*16 for _ in range(32)]
        for y in range(32):
            for x in range(16):
                p=f.getpixel((x,y))
                if p[3]>=128: g[y][x]=nearest(p[:3],SHEET)
        out.append(g)
    return out
def write_gfx(r,frames):
    ptrs=[r.alloc(tiles_from_pixels(g,2,4),4) for g in frames]
    return r.alloc(b''.join(struct.pack('<IHH',0x08000000+p,0x100,0) for p in ptrs),4)
if __name__=='__main__':
    r=Rom(sys.argv[1]); b=r.b
    # 1. merge the splatter reds, set the palette
    for k in range(128):
        lo,hi=b[SPLAT_TILES+k]&15,b[SPLAT_TILES+k]>>4
        lo={12:11,14:13}.get(lo,lo); hi={12:11,14:13}.get(hi,hi)
        b[SPLAT_TILES+k]=lo|(hi<<4)
    ent=shinigami.sprite_palette_entry(r,0x1120); pal=r32(r,ent)-0x08000000
    for i in (1,9,12,14): b[pal+2*i:pal+2*i+2]=gfx.rgb_to_pal([COLS[i]])
    fr=frames_idx()
    # 2. Shinigami sheet (gfx 0x9a): new tile data, image table repointed
    gt=r32(r,0x5f2f4)-0x08000000; mx=b[0x5f2e0]
    ib=r32(r,gt+4*0x9a)-0x08000000
    r.w32(ib+0x1c,0x08000000+write_gfx(r,fr))
    # 3. Witch sheet: copy with a flat purple shirt in the body rows
    wf=[[row[:] for row in g] for g in fr]
    for f,g in enumerate(wf):
        for y in range(CUTS[f],32):
            for x in range(16):
                if g[y][x] in (1,5,9,12): g[y][x]=14
    info=bytearray(b[ib:ib+36]); info[0x1c:0x20]=struct.pack('<I',0x08000000+write_gfx(r,wf))
    ia=r.alloc(bytes(info),4)
    new=r.alloc(bytes(b[gt:gt+4*(mx+1)])+struct.pack('<I',0x08000000+ia),4)
    r.w32(0x5f2f4,0x08000000+new); b[0x5f2e0]=mx+1
    h=header(r,3,6); ev=r32(r,h+4)-0x08000000; po=r32(r,ev+4)-0x08000000
    hits=[i for i in range(b[ev]) if b[po+24*i+1]==0x9a]
    assert len(hits)==1,hits
    b[po+24*hits[0]+1]=mx+1
    r.save(sys.argv[2]); print('witch gfx',hex(mx+1))

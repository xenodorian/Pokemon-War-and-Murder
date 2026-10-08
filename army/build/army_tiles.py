"""Tileset surgery. Every JRA base uses the same grey house; the house lives in Pewter's secondary tileset, so it is grafted (tiles, a merged palette, metatiles, attributes)
into a private uncompressed copy of each town's secondary tileset. Pewter's own two houses are recoloured brown, and its base uses its grafted grey copy."""
import sys,struct
sys.path.insert(0,'/home/claude/work/tools')
import gfx
from leg1 import r32,header
NSEC_TILES=384; NSEC_META=384

def rgb(c): return ((c&31)*8,((c>>5)&31)*8,((c>>10)&31)*8)
def c15(t): return (t[0]>>3)|((t[1]>>3)<<5)|((t[2]>>3)<<10)
def dist(a,b): return sum((x-y)**2 for x,y in zip(a,b))

class Tileset:
    def __init__(s,r,g,n):
        s.r=r; b=r.b; s.g,s.n=g,n
        s.lay=r32(r,header(r,g,n))-0x08000000
        P=r32(r,s.lay+16)-0x08000000; S=r32(r,s.lay+20)-0x08000000; s.P,s.S=P,S
        def tiles(T):
            t=r32(r,T+4)-0x08000000
            return bytes(gfx.lz_decomp(b,t)) if b[T]==1 else None
        s.ptiles=tiles(P); s.stiles=bytearray(tiles(S) or b'')
        s.nreal=len(s.stiles)//32
        s.stiles+=bytes(NSEC_TILES*32-len(s.stiles))
        pp=r32(r,P+8)-0x08000000; sp=r32(r,S+8)-0x08000000
        s.ppal=[[struct.unpack('<H',b[pp+32*k+2*i:pp+32*k+2*i+2])[0] for i in range(16)] for k in range(7)]
        s.spal=[[struct.unpack('<H',b[sp+32*k+2*i:sp+32*k+2*i+2])[0] for i in range(16)] for k in range(16)]
        pm=r32(r,P+12)-0x08000000; sm=r32(r,S+12)-0x08000000
        s.pmeta=lambda m: struct.unpack('<8H',b[pm+16*m:pm+16*m+16])
        s.smeta=[list(struct.unpack('<8H',b[sm+16*k:sm+16*k+16])) for k in range(NSEC_META)]
        pa=r32(r,P+20)-0x08000000; sa=r32(r,S+20)-0x08000000
        s.pattr=lambda m: struct.unpack('<I',b[pa+4*m:pa+4*m+4])[0]
        s.sattr=[struct.unpack('<I',b[sa+4*k:sa+4*k+4])[0] for k in range(NSEC_META)]
        s.cb=r32(r,S+16)
        s.next_tile=NSEC_TILES-1+640        # new tiles are taken from the top of the secondary range
        s.next_meta=NSEC_META-1+640
        s.used=None
    def entries(s,m): return list(s.pmeta(m)) if m<640 else list(s.smeta[m-640])
    def attr(s,m): return s.pattr(m) if m<640 else s.sattr[m-640]
    def tile_px(s,t):
        if t<640: return bytes(s.ptiles[32*t:32*t+32])
        return bytes(s.stiles[32*(t-640):32*(t-640)+32])
    def map_blocks(s):
        w,h=r32(s.r,s.lay),r32(s.r,s.lay+4); mp=r32(s.r,s.lay+12)-0x08000000
        return [struct.unpack('<H',s.r.b[mp+2*i:mp+2*i+2])[0]&0x3ff for i in range(w*h)]
    def slots_used(s):
        used=set()
        for m in set(s.map_blocks()):
            for e in s.entries(m): used.add(e>>12)
        return used
    def alloc_tile(s,px):
        t=s.next_tile; s.next_tile-=1
        assert t-640>=s.nreal,'secondary tileset full'
        s.stiles[32*(t-640):32*(t-640)+32]=px; return t
    def alloc_meta(s,ents,attr):
        m=s.next_meta; s.next_meta-=1
        assert m>max(x for x in s.map_blocks() if x>=640)+1,'secondary metatile range full'
        s.smeta[m-640]=list(ents); s.sattr[m-640]=attr; return m
    def free_slot(s,avoid=()):
        u=s.slots_used()
        for k in range(7,13):
            if k not in u and k not in avoid: return k
        return None
    def evacuate(s,slot,to_slot):
        """free a palette slot for this map: every entry of a metatile used on the map that points at it is redrawn (private tile copy) with the nearest colours of `to_slot`"""
        done={}
        for m in sorted(set(s.map_blocks())):
            ents=s.entries(m)
            if not any((e>>12)==slot for e in ents): continue
            assert m>=640,'primary metatile uses the slot'
            for k,e in enumerate(ents):
                if (e>>12)!=slot: continue
                t=e&0x3ff
                if (t,slot) not in done:
                    px=s.tile_px(t); pal=s.spal[slot]; out=bytearray(32)
                    mp=lambda ix: 0 if ix==0 else nearest_idx(s.spal[to_slot],rgb(pal[ix]))
                    for i,byte in enumerate(px): out[i]=mp(byte&15)|(mp(byte>>4)<<4)
                    done[(t,slot)]=s.alloc_tile(bytes(out))
                ents[k]=(e&0x0c00)|done[(t,slot)]|(to_slot<<12)
            s.smeta[m-640]=ents
    def commit(s):
        """write the private secondary tileset (uncompressed) and point this town's layout at it"""
        r=s.r
        tiles=r.alloc(bytes(s.stiles),4)
        pal=r.alloc(b''.join(struct.pack('<16H',*p) for p in s.spal),4)
        meta=r.alloc(b''.join(struct.pack('<8H',*m) for m in s.smeta),4)
        attr=r.alloc(b''.join(struct.pack('<I',a) for a in s.sattr),4)
        hdr=bytearray(r.b[s.S:s.S+24]); hdr[0]=0
        hdr[4:8]=struct.pack('<I',0x08000000+tiles); hdr[8:12]=struct.pack('<I',0x08000000+pal)
        hdr[12:16]=struct.pack('<I',0x08000000+meta); hdr[16:20]=struct.pack('<I',s.cb); hdr[20:24]=struct.pack('<I',0x08000000+attr)
        na=r.alloc(bytes(hdr),4); r.w32(s.lay+20,0x08000000+na)

def nearest_merge(cols,limit=15):
    """reduce a list of rgb colours to at most `limit` by merging the closest pair"""
    cols=list(cols)
    while len(cols)>limit:
        best=None
        for i in range(len(cols)):
            for j in range(i+1,len(cols)):
                d=dist(cols[i],cols[j])
                if best is None or d<best[0]: best=(d,i,j)
        _,i,j=best; cols[i]=tuple((a+b)//2 for a,b in zip(cols[i],cols[j])); del cols[j]
    return cols
def nearest_idx(pal,col):
    best=1
    for i in range(1,16):
        if dist(rgb(pal[i]),col)<dist(rgb(pal[best]),col): best=i
    return best

class House:
    """the grey Pewter house, extracted once: a 5x4 grid of block values and everything needed to graft it"""
    def __init__(s,src,rect):
        s.src=src; s.x0,s.y0,s.w,s.h=rect
        mp=r32(src.r,src.lay+12)-0x08000000; W=r32(src.r,src.lay)
        s.blocks=[[struct.unpack('<H',src.r.b[mp+2*((s.y0+j)*W+s.x0+i):mp+2*((s.y0+j)*W+s.x0+i)+2])[0] for i in range(s.w)] for j in range(s.h)]
        # colours used by the secondary tiles of the house
        cols=set(); s.pairs=set()
        for row in s.blocks:
            for v in row:
                for e in src.entries(v&0x3ff):
                    t=e&0x3ff
                    if t>=640:
                        s.pairs.add((t,e>>12)); px=src.tile_px(t); pal=src.spal[e>>12]
                        for byte in px:
                            for ix in (byte&15,byte>>4):
                                if ix: cols.add(rgb(pal[ix]))
        s.palette=nearest_merge(sorted(cols))
        s.pal15=[0]+[c15(c) for c in s.palette]+[0]*(15-len(s.palette))
    def remap(s,src,t,pal_slot):
        px=src.tile_px(t); pal=src.spal[pal_slot]; out=bytearray(32)
        look={}
        def m(ix):
            if ix==0: return 0
            c=rgb(pal[ix])
            if c not in look: look[c]=1+min(range(len(s.palette)),key=lambda k:dist(s.palette[k],c))
            return look[c]
        for i,byte in enumerate(px): out[i]=m(byte&15)|(m(byte>>4)<<4)
        return bytes(out)
    def graft(s,dst,slot):
        """copy the house into `dst` using palette slot `slot` (its merged palette is written there); returns the 5x4 block values to paint"""
        src=s.src; dst.spal[slot]=list(s.pal15)
        tmap={}; mmap={}
        for row in s.blocks:
            for v in row:
                m=v&0x3ff
                if m in mmap: continue
                ents=[]
                for e in src.entries(m):
                    t=e&0x3ff
                    if t>=640:
                        key=(t,e>>12)
                        if key not in tmap: tmap[key]=dst.alloc_tile(s.remap(src,t,e>>12))
                        e=(e&0x0c00)|tmap[key]|(slot<<12)
                    ents.append(e)
                mmap[m]=dst.alloc_meta(ents,src.attr(m))
        return [[(v&0xfc00)|mmap[v&0x3ff] for v in row] for row in s.blocks]

def brown(c):
    """grey-ish colour -> brown, keeping saturated colours (windows, doors) as they are"""
    r,g,b=rgb(c); mx,mn=max(r,g,b),min(r,g,b)
    if mx-mn>40: return c
    y=0.30*r+0.59*g+0.11*b
    return c15((min(248,int(y*1.00)),min(248,int(y*0.74)),min(248,int(y*0.46))))
def recolor_brown(ts,slots):
    for k in slots:
        ts.spal[k]=[ts.spal[k][0]]+[brown(c) for c in ts.spal[k][1:]]

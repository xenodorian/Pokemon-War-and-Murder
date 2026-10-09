import sys,struct
sys.path.insert(0,'/home/claude/work/tools')
import gfx
d=open(sys.argv[1],'rb').read()
def r32(o): return struct.unpack('<I',d[o:o+4])[0]
def hdr(g,n): return r32(r32(0x3526A8+4*g)-0x08000000+4*n)-0x08000000
def ts(T):
    comp=d[T]; tiles=r32(T+4)-0x08000000
    data=bytes(gfx.lz_decomp(d,tiles)) if d[tiles]==0x10 else d[tiles:tiles+0x3000]
    return dict(comp=comp,sec=d[T+1],data=data,pal=r32(T+8)-0x08000000,meta=r32(T+12)-0x08000000,attr=r32(T+20)-0x08000000)
def check(g,n):
    h=hdr(g,n); lay=r32(h)-0x08000000; w,hh=r32(lay),r32(lay+4); mp=r32(lay+12)-0x08000000
    P=ts(r32(lay+16)-0x08000000); S=ts(r32(lay+20)-0x08000000)
    ids=set(struct.unpack('<H',d[mp+2*i:mp+2*i+2])[0]&0x3ff for i in range(w*hh))
    # border
    bo=r32(lay+8)-0x08000000; bw,bh=d[lay+0x1c] if False else 2,2
    for i in range(4): ids.add(struct.unpack('<H',d[bo+2*i:bo+2*i+2])[0]&0x3ff)
    bad=[]
    for m in sorted(ids):
        if m>=640+384: bad.append((m,'block id out of range')); continue
        T=P if m<640 else S; k=m if m<640 else m-640
        for q in range(8):
            e=struct.unpack('<H',d[T['meta']+16*k+2*q:T['meta']+16*k+2*q+2])[0]
            t=e&0x3ff; pal=e>>12
            if pal>12: bad.append((m,q,'palette slot',pal))
            src=P if t<640 else S; tt=t if t<640 else t-640
            if tt*32+32>len(src['data']): bad.append((m,q,'tile beyond data',t))
    return len(ids),bad
if __name__=='__main__':
    tot=0
    for g,n in [(3,i) for i in (0,1,2,3,4,5,6,7,8,10)]+[(2,i) for i in range(67,82)]+[(3,18)]:
        try: cnt,bad=check(g,n)
        except Exception as e: print((g,n),'ERR',e); continue
        print((g,n),cnt,'blocks',bad[:6])

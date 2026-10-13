# Collision scan: in cells the patch changed, compare the map entry's collision/elevation bits with how the original ROM uses the same block.
# kind A = a walkable block carrying collision (invisible wall); kind B = a block the original always makes solid but collision is 0 (walk-through).
# usage: collision_scan.py patched.gba original.gba
import sys,struct,collections
def maps_raw(d):
    r32=lambda o: struct.unpack('<I',d[o:o+4])[0]
    out={}
    for g in range(0,45):
        gp=r32(0x3526A8+4*g)
        if not (0x08000000<=gp<0x0a000000): break
        gp-=0x08000000
        for n in range(0,200):
            hp=r32(gp+4*n)
            if not (0x08000000<=hp<0x0a000000): break
            lay=r32(hp-0x08000000)
            if not (0x08000000<=lay<0x0a000000): break
            lay-=0x08000000; w,h=r32(lay),r32(lay+4); mp=r32(lay+12)
            if not(0<w<600 and 0<h<600 and 0x08000000<=mp<0x0a000000): continue
            mp-=0x08000000
            if mp+2*w*h>len(d): continue
            grid=[[struct.unpack('<H',d[mp+2*(y*w+x):mp+2*(y*w+x)+2])[0] for x in range(w)] for y in range(h)]
            out[(g,n)]=(w,h,grid,r32(lay+20))
    return out
def key(b,sx): return b if b<640 else (sx,b)
def build(org):
    mo=maps_raw(org); mode=collections.defaultdict(collections.Counter)
    for k,(w,h,g,sx) in mo.items():
        for row in g:
            for v in row: mode[key(v&0x3ff,sx)][v>>10]+=1
    return mo,mode
def scan(cur,org,maps=None):
    mc=maps_raw(cur); mo,mode=build(org); orig_sx={v[3] for v in mo.values()}
    res=collections.defaultdict(list)
    for k,(w,h,g,sx) in mc.items():
        if maps and k not in maps: continue
        o=mo.get(k); sxo=sx if sx in orig_sx else (o[3] if o else None)
        for y in range(h):
            for x in range(w):
                v=g[y][x]
                if o is not None and x<o[0] and y<o[1] and o[2][y][x]==v: continue
                b=v&0x3ff
                if b>=640 and sxo is None: continue
                kk=key(b,sxo)
                if kk not in mode: continue
                tot=sum(mode[kk].values()); (top,cnt)=mode[kk].most_common(1)[0]
                col=(v>>10)&3; tcol=(top&3)
                if col!=0 and sum(c for r_,c in mode[kk].items() if (r_&3)==0)>=0.9*tot: res[k].append(('A',x,y,b,v>>10,top))
                if col==0 and sum(c for r_,c in mode[kk].items() if (r_&3)!=0)>=0.9*tot: res[k].append(('B',x,y,b,v>>10,top))
    return res,mode
if __name__=='__main__':
    cur=open(sys.argv[1],'rb').read(); org=open(sys.argv[2],'rb').read()
    TOWNS={(3,i) for i in (0,1,2,3,4,5,6,7,8,10,18)}
    res,_=scan(cur,org,TOWNS)
    for k in sorted(res):
        A=[t for t in res[k] if t[0]=='A']; B=[t for t in res[k] if t[0]=='B']
        print(k,'invisible walls (walkable block, collision set):',len(A),'| walk-through (solid block, no collision):',len(B))
        for kind,L in (('A',A),('B',B)):
            for t in L[:60]: print('   %s (%d,%d) block %d raw>>10=%d original usually %d'%t)

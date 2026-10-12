# Comb scan: finds blocks repeated along one axis for longer than the original game ever repeats them.
# usage: comb_scan.py patched.gba original.gba
import sys,struct,collections
sys.path.insert(0,'/home/claude/work/tools')
G=0x3526A8
def maps(d):
    r32=lambda o: struct.unpack('<I',d[o:o+4])[0]
    out={}
    for g in range(0,45):
        gp=r32(G+4*g)
        if not (0x08000000<=gp<0x0a000000): break
        gp-=0x08000000
        for n in range(0,200):
            hp=r32(gp+4*n)
            if not (0x08000000<=hp<0x0a000000): break
            lay=r32(hp-0x08000000)
            if not (0x08000000<=lay<0x0a000000): break
            lay-=0x08000000; w,h=r32(lay),r32(lay+4)
            mp=r32(lay+12)
            if not(0<w<600 and 0<h<600 and 0x08000000<=mp<0x0a000000): continue
            mp-=0x08000000
            if mp+2*w*h>len(d): continue
            grid=[[struct.unpack('<H',d[mp+2*(y*w+x):mp+2*(y*w+x)+2])[0]&0x3ff for x in range(w)] for y in range(h)]
            out[(g,n)]=(w,h,grid,r32(lay+16),r32(lay+20))
    return out
def runs(grid,w,h):
    """yield (axis,block,start,len,fixed) for horizontal ('H') and vertical ('V') runs"""
    for y in range(h):
        x=0
        while x<w:
            b=grid[y][x]; x2=x
            while x2+1<w and grid[y][x2+1]==b: x2+=1
            yield ('H',b,(x,y),x2-x+1)
            x=x2+1
    for x in range(w):
        y=0
        while y<h:
            b=grid[y][x]; y2=y
            while y2+1<h and grid[y2+1][x]==b: y2+=1
            yield ('V',b,(x,y),y2-y+1)
            y=y2+1
if __name__=='__main__':
    cur=open(sys.argv[1],'rb').read(); org=open(sys.argv[2],'rb').read()
    mc,mo=maps(cur),maps(org)
    # per tileset pair (primary,secondary): the longest run of each block anywhere in the original
    mx=collections.defaultdict(int)
    for k,(w,h,grid,P,Sx) in mo.items():
        for ax,b,st,ln in runs(grid,w,h):
            key=(Sx,ax,b); mx[key]=max(mx[key],ln)
    # blocks that are fine to repeat a lot (plain ground, water, trees handled by pairs) are skipped by their own history; flag the rest
    MIN=4
    names={(3,0):'PALLET',(3,1):'VIRIDIAN',(3,2):'PEWTER',(3,3):'CERULEAN',(3,4):'LAVENDER',(3,5):'VERMILION',(3,6):'CELADON',(3,7):'FUCHSIA',(3,8):'CINNABAR',(3,10):'SAFFRON'}
    rep=collections.defaultdict(list)
    for k,(w,h,grid,P,Sx) in mc.items():
        o=mo.get(k)
        for ax,b,(x,y),ln in runs(grid,w,h):
            if ln<MIN: continue
            limit=max([mx.get((Sx,ax,b),0)]+[mx.get((s2,ax,b),0) for s2 in {v[4] for v in mo.values() if v[3]==P}])
            if ln<=limit or limit>3: continue          # plain ground may repeat; only blocks the original never repeats along this axis
            # must involve a changed cell: outside the original size or different from it
            changed=0
            for i in range(ln):
                xx,yy=(x+i,y) if ax=='H' else (x,y+i)
                if o is None or xx>=o[0] or yy>=o[1] or o[2][yy][xx]!=b: changed+=1
            if changed==0: continue
            rep[k].append((ax,b,(x,y),ln,limit,changed))
    for k in sorted(rep):
        print(names.get(k,k),'map',k,len(rep[k]),'violations')
        for ax,b,st,ln,lim,ch in rep[k]: print('   %s run of block %d, %d long at %s, original never exceeds %d (%d cells changed)'%(ax,b,ln,st,lim,ch))

def alternations(grid,w,h):
    """horizontal and vertical stretches A B A B ... (A!=B) of length >= 6: yields (axis,(A,B),(x,y),len)"""
    for y in range(h):
        x=0
        while x+1<w:
            a,b=grid[y][x],grid[y][x+1]
            if a==b: x+=1; continue
            x2=x+1
            while x2+1<w and grid[y][x2+1]==grid[y][x2-1]: x2+=1
            if x2-x+1>=6: yield ('H',(a,b),(x,y),x2-x+1)
            x=x2
    for x in range(w):
        y=0
        while y+1<h:
            a,b=grid[y][x],grid[y+1][x]
            if a==b: y+=1; continue
            y2=y+1
            while y2+1<h and grid[y2+1][x]==grid[y2-1][x]: y2+=1
            if y2-y+1>=6: yield ('V',(a,b),(x,y),y2-y+1)
            y=y2
def alt_report(cur_path,org_path,only):
    cur=open(cur_path,'rb').read(); org=open(org_path,'rb').read()
    mc,mo=maps(cur),maps(org)
    mx=collections.defaultdict(int)
    for k,(w,h,grid,P,Sx) in mo.items():
        for ax,pr,st,ln in alternations(grid,w,h): mx[(ax,pr)]=max(mx[(ax,pr)],ln)
    res={}
    for k in only:
        if k not in mc: continue
        w,h,grid,P,Sx=mc[k]; o=mo.get(k)
        for ax,pr,(x,y),ln in alternations(grid,w,h):
            limit=mx.get((ax,pr),0)
            if ln<=limit: continue
            ch=0
            for i in range(ln):
                xx,yy=(x+i,y) if ax=='H' else (x,y+i)
                a=pr[i%2]
                if o is None or xx>=o[0] or yy>=o[1] or o[2][yy][xx]!=a: ch+=1
            if ch: res.setdefault(k,[]).append((ax,pr,(x,y),ln,limit,ch))
    return res

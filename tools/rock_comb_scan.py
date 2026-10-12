# Rock mound comb scan over every map. A rock edge block repeated across its own edge, a corner block repeated at all, or edge blocks alternated,
# counted only where the patched ROM differs from the original. usage: rock_comb_scan.py patched.gba original.gba
import sys; sys.path.insert(0,'/home/user/Pokemon-Outlaw-Mod/tools')
import comb_scan as C
VEDGE={112,114,115,117}            # side faces: may repeat vertically only
HEDGE={105,108,121,124}            # top and bottom faces: may repeat horizontally only
CORNER={104,106,107,109,120,122,123,125,178,179,186,187}   # corners: never repeat in a line
ROCK=VEDGE|HEDGE|CORNER|{113}
cur=open(sys.argv[1],'rb').read(); org=open(sys.argv[2],'rb').read()
mc,mo=C.maps(cur),C.maps(org)
def changed(k,x,y,b):
    o=mo.get(k)
    return o is None or x>=o[0] or y>=o[1] or o[2][y][x]!=b
hits={}
for k,(w,h,grid,P,Sx) in mc.items():
    for ax,b,(x,y),ln in C.runs(grid,w,h):
        if ln<3: continue
        bad=None
        if b in VEDGE and ax=='H': bad='side face repeated across its edge'
        if b in HEDGE and ax=='V': bad='top/bottom face repeated across its edge'
        if b in CORNER: bad='corner block repeated in a line'
        if not bad: continue
        cells=[(x+i,y) if ax=='H' else (x,y+i) for i in range(ln)]
        ch=sum(1 for (cx,cy) in cells if changed(k,cx,cy,b))
        if ch: hits.setdefault(k,[]).append((bad,ax,b,(x,y),ln,ch))
    for ax,pr,(x,y),ln in C.alternations(grid,w,h):
        if ln<4: pass
        if pr[0] in ROCK and pr[1] in ROCK:
            cells=[(x+i,y) if ax=='H' else (x,y+i) for i in range(ln)]
            ch=sum(1 for i,(cx,cy) in enumerate(cells) if changed(k,cx,cy,pr[i%2]))
            if ch: hits.setdefault(k,[]).append(('rock blocks alternated A B A B',ax,pr,(x,y),ln,ch))
for k in sorted(hits):
    print('map',k)
    for bad,ax,b,st,ln,ch in hits[k]: print('   %s: %s %s at %s, %d long, %d changed'%(bad,ax,b,st,ln,ch))
print(len(hits),'maps with candidates')

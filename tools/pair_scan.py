# Pair scan: adjacent block pairs in the patched ROM that the original ROM never has, counted only where a cell differs from the original.
# usage: pair_scan.py patched.gba original.gba
import sys,collections; sys.path.insert(0,'/home/user/Pokemon-Outlaw-Mod/tools')
import comb_scan as C
def key(b,Sx):
    return b if b<640 else (Sx,b)
def build_vocab(mo):
    pairs=set(); blocks=set()
    for k,(w,h,g,P,Sx) in mo.items():
        for y in range(h):
            row=g[y]
            for x in range(w):
                a=key(row[x],Sx); blocks.add(a)
                if x+1<w: pairs.add((a,key(row[x+1],Sx),'H'))
                if y+1<h: pairs.add((a,key(g[y+1][x],Sx),'V'))
    return pairs,blocks
def scan(cur,org):
    mc,mo=C.maps(cur),C.maps(org)
    pairs,blocks=build_vocab(mo)
    orig_sx={v[4] for v in mo.values()}
    out={}
    for k,(w,h,g,P,Sx) in mc.items():
        o=mo.get(k)
        sx=Sx if Sx in orig_sx else (o[4] if o else None)
        def ch(x,y):
            return o is None or x>=o[0] or y>=o[1] or o[2][y][x]!=g[y][x]
        def K(b): 
            if b<640: return b
            return None if sx is None else (sx,b)
        found=[]
        for y in range(h):
            for x in range(w):
                for dx,dy,d in ((1,0,'H'),(0,1,'V')):
                    x2,y2=x+dx,y+dy
                    if x2>=w or y2>=h: continue
                    if not(ch(x,y) or ch(x2,y2)): continue
                    a,b=K(g[y][x]),K(g[y2][x2])
                    if a is None or b is None: continue
                    if a not in blocks or b not in blocks: found.append((x,y,d,g[y][x],g[y2][x2],'new block')); continue
                    if (a,b,d) not in pairs: found.append((x,y,d,g[y][x],g[y2][x2],'unseen pair'))
        if found: out[k]=found
    return out
if __name__=='__main__':
    cur=open(sys.argv[1],'rb').read(); org=open(sys.argv[2],'rb').read()
    res=scan(cur,org)
    tot=0
    for k in sorted(res):
        unseen=[f for f in res[k] if f[5]=='unseen pair']; newb=[f for f in res[k] if f[5]=='new block']
        print('map',k,'unseen pairs',len(unseen),'involving new blocks',len(newb)); tot+=len(unseen)
    print('total unseen pairs',tot)

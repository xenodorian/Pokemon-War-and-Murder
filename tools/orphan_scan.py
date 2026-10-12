# Orphan scan: L-shaped corner blocks and | shaped edge blocks whose matching neighbours are missing, in cells the patch changed.
# Each family lists blocks that must have a given kind of block on a given side. usage: orphan_scan.py patched.gba original.gba
import sys; sys.path.insert(0,'/home/user/Pokemon-Outlaw-Mod/tools')
import comb_scan as C
ROAD_IN={365,366,367,357,358,359,373,374,375,405,413,366}
# block: {side: set of acceptable neighbour blocks}. sides: N S E W relative to the block
RULES={
 # paved road: left edge needs road to the east, right edge road to the west, top corners need road below, etc.
 365:{'E':ROAD_IN},367:{'W':ROAD_IN},357:{'E':ROAD_IN,'S':ROAD_IN},359:{'W':ROAD_IN,'S':ROAD_IN},358:{'S':ROAD_IN},
 373:{'E':ROAD_IN,'N':ROAD_IN},375:{'W':ROAD_IN,'N':ROAD_IN},374:{'N':ROAD_IN},
 # outdoor rock: side faces need rock on their inner side, corners need rock inward on both sides
 112:{'E':{113,115,112,107,123,124,120,121,186,187,179,178,117,108,105,104,114}},
 114:{'W':{113,117,114,109,125,124,122,121,186,187,178,179,115,108,105,106,112}},
 105:{'S':{113,108,107,109,112,114,115,117,120,121,122,123,124,125,186,187}},
 121:{'N':{113,124,123,125,120,122,115,117,108,112,114,179,178}},
 104:{'E':{105,106,104,186,187},'S':{112,113,115,114,117,107}},106:{'W':{105,104,106,186,187},'S':{114,113,117,115,112,109}},
 120:{'E':{121,122,120,179},'N':{112,113,115,123}},122:{'W':{121,120,122,178},'N':{114,113,117,125}},
}
TREE_L={0x14,0x16,0x1c,0x1e,0x24,0x26,0x0e}; TREE_R={0x15,0x17,0x1d,0x1f,0x25,0x27,0x0f}; TREE=TREE_L|TREE_R
def tree_variant_issue(g,x,y,w):
    b=g[y][x]
    if b in (0x14,0x1c,0x24,0x16,0x1e,0x26):
        if b in (0x1e,) and y>0 and g[y-1][x] in (0x0e,0x0f): return None
        ln=g[y][x-1] if x>0 else None
        facing_tree=ln in TREE if ln is not None else None
        if facing_tree is None: return None
        edge=b in (0x16,0x1e,0x26)
        if edge==facing_tree: return 'tree left half uses %s variant but its left neighbour is %s'%('edge' if edge else 'interior','a tree' if facing_tree else 'not a tree')
    if b in (0x15,0x1d,0x25,0x17,0x1f,0x27):
        if b==0x1f and y>0 and g[y-1][x] in (0x0e,0x0f): return None
        rn=g[y][x+1] if x+1<w else None
        facing_tree=rn in TREE if rn is not None else None
        if facing_tree is None: return None
        edge=b in (0x17,0x1f,0x27)
        if edge==facing_tree: return 'tree right half uses %s variant but its right neighbour is %s'%('edge' if edge else 'interior','a tree' if facing_tree else 'not a tree')
    return None
if __name__=='__main__':
    cur=open(sys.argv[1],'rb').read(); org=open(sys.argv[2],'rb').read()
    mc,mo=C.maps(cur),C.maps(org)
    names={(3,0):'PALLET',(3,1):'VIRIDIAN',(3,2):'PEWTER',(3,3):'CERULEAN',(3,4):'LAVENDER',(3,5):'VERMILION',(3,6):'CELADON',(3,7):'FUCHSIA',(3,8):'CINNABAR',(3,10):'SAFFRON',(3,18):'SEVEN ISLAND'}
    total=0
    for k,nm in names.items():
        if k not in mc: continue
        w,h,g,P,Sx=mc[k]; o=mo.get(k)
        def ch(x,y):
            return o is None or x>=o[0] or y>=o[1] or o[2][y][x]!=g[y][x]
        out=[]
        for y in range(h):
            for x in range(w):
                b=g[y][x]
                near=any(ch(x+dx,y+dy) for dx in (-1,0,1) for dy in (-1,0,1) if 0<=x+dx<w and 0<=y+dy<h)
                if not near: continue
                if b in RULES:
                    for side,ok in RULES[b].items():
                        dx,dy={'N':(0,-1),'S':(0,1),'E':(1,0),'W':(-1,0)}[side]
                        nx,ny=x+dx,y+dy
                        if 0<=nx<w and 0<=ny<h and g[ny][nx] not in ok: out.append((x,y,b,'needs %s on its %s side, has %d'%('matching block',side,g[ny][nx])))
                msg=tree_variant_issue(g,x,y,w)
                if msg: out.append((x,y,b,msg))
        if out:
            print(nm,k,len(out))
            for x,y,b,m in out[:40]: print('   (%d,%d) block %d: %s'%(x,y,b,m))
            total+=len(out)
    print('total',total)

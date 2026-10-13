"""Edge rules learned from the original hack's maps, for every tileset (water, shores, roads, sea rocks, plants, indoor floors, ...), so no family needs a hand table.
 build ORIGINAL.gba   writes edge_vocab.json.gz : for each (primary,secondary) tileset the block pairs that touch (H and V) and, for each block, the block the original puts
                      between a given north/south/east/west neighbour set (majority; 'amb' marks keys the original does not decide)
 Vocab.pair_findings  pairs the original never has in that tileset (an edge or corner whose neighbour is wrong shows up as an unseen pair)
 Vocab.suggest        the block the original puts at a cell with these four neighbours
 Vocab.repair         re-derive chosen cells from their neighbours, keeping a cell unless the original is unanimous about a different block
 python3 edge_learn.py coverage   prints per tileset: maps, distinct blocks, pairs, and the share of 4-neighbour keys the original decides unanimously"""
import sys,os,gzip,json,collections
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
VOCAB=os.path.join(HERE,'edge_vocab.json.gz')
def _maps(d):
    import comb_scan as C
    sys.path.insert(0,HERE)
    return C.maps(d)
def build(rom,out=VOCAB):
    mo=_maps(open(rom,'rb').read())
    pairs=collections.defaultdict(set); k4=collections.defaultdict(lambda:collections.defaultdict(collections.Counter)); nmaps=collections.Counter(); blocks=collections.defaultdict(set)
    for k,(w,h,g,P,S) in mo.items():
        t='%x_%x'%(P,S); nmaps[t]+=1
        for y in range(h):
            for x in range(w):
                b=g[y][x]; blocks[t].add(b)
                if x+1<w: pairs[t].add((b,g[y][x+1],0))
                if y+1<h: pairs[t].add((b,g[y+1][x],1))
                if 0<x<w-1 and 0<y<h-1: k4[t]['%d,%d,%d,%d'%(g[y-1][x],g[y+1][x],g[y][x+1],g[y][x-1])][b]+=1
    data={}
    for t in nmaps:
        tab={}
        for key,c in k4[t].items():
            tab[key]=c.most_common(1)[0][0] if len(c)==1 else [c.most_common(1)[0][0],-1]   # [majority,-1] = ambiguous
        data[t]={'maps':nmaps[t],'blocks':len(blocks[t]),'pairs':sorted(pairs[t]),'k4':tab}
    with gzip.open(out,'wt') as f: json.dump(data,f,separators=(',',':'))
    return data
class Vocab:
    def __init__(s,path=VOCAB):
        with gzip.open(path,'rt') as f: s.d=json.load(f)
        s.pairs={t:{tuple(p) for p in v['pairs']} for t,v in s.d.items()}
        s.blocks={t:{p[0] for p in v['pairs']}|{p[1] for p in v['pairs']} for t,v in s.d.items()}
    @staticmethod
    def key(P,S): return '%x_%x'%(P,S)
    def known(s,P,S): return s.key(P,S) in s.d
    def pair_ok(s,P,S,a,b,axis):
        t=s.pairs.get(s.key(P,S))
        return True if t is None else (a,b,axis) in t
    def pair_findings(s,grid,P,S,cells=None):
        """unseen block pairs in this tileset; cells = set of (x,y) to restrict to (pairs touching one of them)"""
        t=s.pairs.get(s.key(P,S)); bl=s.blocks.get(s.key(P,S))
        if t is None: return []
        h=len(grid); w=len(grid[0]); out=[]
        for y in range(h):
            for x in range(w):
                a=grid[y][x]&0x3ff
                for dx,dy,ax in ((1,0,0),(0,1,1)):
                    x2,y2=x+dx,y+dy
                    if x2>=w or y2>=h: continue
                    if cells is not None and (x,y) not in cells and (x2,y2) not in cells: continue
                    b=grid[y2][x2]&0x3ff
                    if a not in bl or b not in bl: continue      # a block the tileset never had (new art): not an edge-logic question
                    if (a,b,ax) not in t: out.append(('unseen-pair',x,y,a,b,'HV'[ax]))
        return out
    def suggest(s,P,S,n,so,e,w):
        """block the original puts between these neighbours: (block, unanimous) or None when the original never has this neighbourhood"""
        v=s.d.get(s.key(P,S))
        if not v: return None
        r=v['k4'].get('%d,%d,%d,%d'%(n,so,e,w))
        if r is None: return None
        return (r,True) if isinstance(r,int) else (r[0],False)
    def repair(s,grid,P,S,cells,rounds=3):
        """for each cell: if the original is unanimous that these neighbours call for another block, use it. Returns (new grid, changed cells)"""
        out=[row[:] for row in grid]; h=len(grid); w=len(grid[0]); changed=[]
        for _ in range(rounds):
            ch=False
            for (x,y) in sorted(cells):
                if not(0<x<w-1 and 0<y<h-1): continue
                g=lambda xx,yy: out[yy][xx]&0x3ff
                r=s.suggest(P,S,g(x,y-1),g(x,y+1),g(x+1,y),g(x-1,y))
                if r and r[1] and r[0]!=g(x,y):
                    out[y][x]=(out[y][x]&0xfc00)|r[0]; ch=True; changed.append((x,y,r[0]))
            if not ch: break
        return out,changed
    def coverage(s):
        rows=[]
        for t,v in sorted(s.d.items()):
            k=v['k4']; un=sum(1 for r in k.values() if isinstance(r,int))
            rows.append((t,v['maps'],v['blocks'],len(v['pairs']),len(k),100.0*un/max(1,len(k))))
        return rows
if __name__=='__main__':
    if sys.argv[1]=='build': build(sys.argv[2]); print('written',VOCAB,os.path.getsize(VOCAB),'bytes')
    elif sys.argv[1]=='coverage':
        print('%-18s %5s %7s %7s %8s %9s'%('tileset P_S','maps','blocks','pairs','k4 keys','decided%'))
        for r in Vocab().coverage(): print('%-18s %5d %7d %7d %8d %8.1f%%'%r)

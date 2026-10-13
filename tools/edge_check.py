"""usage: edge_check.py ROM [ORIGINAL_ROM]
Checks every map against edge_vocab.json.gz (learned from the original hack, see edge_learn.py): block pairs the tileset never has, and cells whose four neighbours make the original unanimous about a different block.
With ORIGINAL_ROM only cells that differ from it are reported."""
import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import comb_scan as C, edge_learn as EL
def run(rom,orig=None):
    mc=C.maps(open(rom,'rb').read()); mo=C.maps(open(orig,'rb').read()) if orig else {}
    V=EL.Vocab(); res={}; seen=set()
    for k,(w,h,g,P,S) in mc.items():
        sig=hash(str(g))
        if sig in seen: continue          # the map table lists some maps twice
        seen.add(sig)
        o=mo.get(k)
        if orig and o is None: continue
        P0,S0=(o[3],o[4]) if o else (P,S)
        if not V.known(P0,S0): continue
        ch={(x,y) for y in range(h) for x in range(w) if o is None or x>=o[0] or y>=o[1] or o[2][y][x]!=g[y][x]} if orig else None
        if ch is not None and not ch: continue
        up=V.pair_findings(g,P0,S0,ch)
        _,rep=V.repair(g,P0,S0,ch if ch is not None else {(x,y) for y in range(h) for x in range(w)},rounds=1)
        if up or rep: res[k]=(up,rep)
    return res
if __name__=='__main__':
    res=run(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else None)
    for k,(up,rep) in sorted(res.items()): print('map',k,'unseen pairs',len(up),'cells the original decides otherwise',len(rep))
    print(len(res),'maps with findings')

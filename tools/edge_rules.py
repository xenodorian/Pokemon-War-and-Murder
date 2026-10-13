"""Edge rules for the map builders, in one place so an edit cannot reintroduce combing, orphans or half trees.
Sources: rock_rules.py (Route 23 read), lawn_rules.py (Pallet read), retree.py (forest tessellation). Verified by render with the user, 2026-10-12.
Used by army_sites.extend_row (lip_fill) and army_tail (validate)."""
# ---- rock mounds: which blocks may repeat along which axis
ROCK=set(range(104,126))|{178,179,186,187}
ROCK_H_OK={105,108,113,121,124,186,187}      # top/bottom rims and the flat interior repeat horizontally
ROCK_V_OK={112,114,115,117,113}              # side walls and the flat interior repeat vertically
TREE_L={0x0e,0x14,0x16,0x1c,0x1e,0x24,0x26}; TREE_R={0x0f,0x15,0x17,0x1d,0x1f,0x25,0x27}
def _lawn_fill(cells,n):
    """n cells of flat dark lawn (8), as in the verified Lavender fix: a lawn stretch beside a rock lip stays flat, never a 9/8 comb"""
    return [(cells[-1]&0xfc00)|8]*n
def lip_fill(row,N):
    """A row whose east end is a rock lip (prev, lip with lip 113/114 and prev a rock block): the row extended by N columns, or None for any other row.
    The old rule repeated the block west of the lip, which turns wall and corner blocks into a comb. Here:
      prev 117 or 125 (wall of a mound that goes on east): the wall stays and the new cells are the flat interior 113;
      prev 179 (concave corner): its outer face 121 fills, the corner moves to the new east edge;
      prev 187 (rim corner): top rim 105 fills, the corner moves to the new east edge;
      prev 112 (side wall): the lawn west of it carries on (flat 8), the wall moves to the new east edge."""
    w=len(row); lip,prev=row[w-1]&0x3ff,row[w-2]&0x3ff
    if lip not in (113,114) or prev not in (117,125,179,187,112): return None
    fl=lambda b: (row[w-2]&0xfc00)|b
    if prev in (117,125): return row[:w-1]+[fl(113)]*N+[row[w-1]]
    if prev==179: return row[:w-2]+[fl(121)]*N+row[w-2:]
    if prev==187: return row[:w-2]+[fl(105)]*N+row[w-2:]
    west=row[:w-2]
    return west+_lawn_fill(west,N)+row[w-2:]

# ---- validation: run after an edit and compare with the map before it; any new finding is a bug in the edit
def rock_comb(grid):
    """rock blocks repeated along an axis they never repeat on (corners anywhere, walls horizontally, rims vertically)"""
    h=len(grid); w=len(grid[0]); out=[]
    for y in range(h):
        for x in range(w-1):
            a=grid[y][x]&0x3ff
            if a in ROCK and a==grid[y][x+1]&0x3ff and a not in ROCK_H_OK: out.append(('H',x,y,a))
    for y in range(h-1):
        for x in range(w):
            a=grid[y][x]&0x3ff
            if a in ROCK and a==grid[y+1][x]&0x3ff and a not in ROCK_V_OK: out.append(('V',x,y,a))
    return out
def half_trees(grid):
    """tree blocks that are not half of a pair (left half then right half)"""
    h=len(grid); w=len(grid[0]); out=[]
    for y in range(h):
        for x in range(w):
            b=grid[y][x]&0x3ff
            if b in TREE_L and not(x+1<w and grid[y][x+1]&0x3ff in TREE_R): out.append(('tree-left',x,y,b))
            if b in TREE_R and not(x>0 and grid[y][x-1]&0x3ff in TREE_L): out.append(('tree-right',x,y,b))
    return out
def alternating_rock(grid):
    """A B A B stretches of two different rock blocks, 4 or more long"""
    h=len(grid); w=len(grid[0]); out=[]
    for y in range(h):
        for x in range(w-3):
            a,b=grid[y][x]&0x3ff,grid[y][x+1]&0x3ff
            if a!=b and a in ROCK and b in ROCK and grid[y][x+2]&0x3ff==a and grid[y][x+3]&0x3ff==b: out.append(('alt-H',x,y,(a,b)))
    return out
def validate(name,grid,before=None):
    """raise AssertionError listing findings that the edit introduced (findings already in `before` are the original hack's and are tolerated)"""
    old={(f[0],f[1],f[2],f[3],f[4]) for f in findings(before)} if before is not None else set()
    new=[f for f in findings(grid) if (f[0],f[1],f[2],f[3],f[4]) not in old]
    assert not new,'%s: %d edge-rule violations introduced, first: %s'%(name,len(new),new[:8])
    return len(old)

# ---- lawn borders (lawn_rules.py): pale lawn around a dark region
import lawn_rules as L
PALE=662
LAWN_EDGE=set(L.EDGE.values())|set(L.CONVEX.values())|{652}
DARK_LAWN={1,8,9,16,17}
def lawn_border(D,cells):
    """{(x,y): block} for pale cells `cells` next to the dark region D (a set of (x,y)); cells with no dark neighbour stay pale"""
    out={}
    for (x,y) in cells:
        if (x,y) in D: continue
        b=L.border_block(D,x,y)
        out[(x,y)]=PALE if b is None else b
    return out
_CARD={654:(0,-1),670:(0,1),663:(1,0),686:(-1,0)}
_CONV={711:(1,1),710:(-1,1),703:(1,-1),702:(-1,-1)}
def lawn_edge_findings(grid):
    """a lawn edge block whose dark side is pale or whose pale side is dark; a convex corner whose diagonal cell is not dark"""
    h=len(grid); w=len(grid[0]); out=[]
    def at(x,y): return grid[y][x]&0x3ff if 0<=x<w and 0<=y<h else None
    for y in range(h):
        for x in range(w):
            b=grid[y][x]&0x3ff
            if b in _CARD:
                dx,dy=_CARD[b]; d=at(x+dx,y+dy); o=at(x-dx,y-dy)
                if d is not None and (d==PALE): out.append(('lawn-edge-dark-side-pale',x,y,b,d))
                if o is not None and o in DARK_LAWN: out.append(('lawn-edge-pale-side-dark',x,y,b,o))
            elif b in _CONV:
                dx,dy=_CONV[b]; d=at(x+dx,y+dy)
                if d is not None and d==PALE: out.append(('lawn-corner-diagonal-pale',x,y,b,d))
    return out

# ---- fences: all fence blocks are drawn on dark lawn. Horizontal 231, vertical 244 (pole left) / 245 (pole right), posts 252 / 253.
FENCE_H={231}; FENCE_V={244,245}; FENCE_POST={252,253}
def fence_run(kind,n):
    """blocks of a fence run: 'h' n cells of 231; 'v-left'/'v-right' n cells of 244/245 ending in the post 252/253 at the bottom"""
    if kind=='h': return [231]*n
    v,p=(244,252) if kind=='v-left' else (245,253)
    return [v]*(n-1)+[p]
def fence_findings(grid):
    h=len(grid); w=len(grid[0]); out=[]
    for y in range(h):
        for x in range(w-2):
            a=grid[y][x]&0x3ff
            if a in FENCE_V and a==grid[y][x+1]&0x3ff==grid[y][x+2]&0x3ff: out.append(('fence-vertical-block-run-horizontal',x,y,a,3))
    for y in range(h-2):
        for x in range(w):
            if grid[y][x]&0x3ff in FENCE_H and grid[y][x]&0x3ff==grid[y+1][x]&0x3ff==grid[y+2][x]&0x3ff: out.append(('fence-horizontal-block-run-vertical',x,y,231,3))
    for y in range(h):
        for x in range(w):
            a=grid[y][x]&0x3ff
            if a in FENCE_H|FENCE_V|FENCE_POST:
                for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    nx,ny=x+dx,y+dy
                    if 0<=nx<w and 0<=ny<h and grid[ny][nx]&0x3ff==PALE: out.append(('fence-on-pale-lawn',x,y,a,PALE)); break
    return out

# ---- ponds: the corner block follows what lies outside the corner (read from the original maps)
# top corners (left, right): square where rock or cliff lies outside; rounded with dark-grass pixels where dark lawn lies outside; Pallet's variants with pale-lawn pixels where pale lawn lies outside.
POND_TOP={'rock':(288,289),'dark':(290,292),'pale':(721,722)}
def outside_kind(b):
    if b in ROCK: return 'rock'
    if b==PALE or b in LAWN_EDGE: return 'pale'
    if b in DARK_LAWN or b in TREE_L|TREE_R: return 'dark'
    return None
def pond_corner_top(side,outside):
    """block for a pond's top-left (side 0) or top-right (side 1) corner, outside = block id of the cell above the corner"""
    k=outside_kind(outside)
    return None if k is None else POND_TOP[k][side]
def pond_findings(grid):
    h=len(grid); w=len(grid[0]); out=[]
    for y in range(1,h):
        for x in range(w):
            b=grid[y][x]&0x3ff
            for side in (0,1):
                for kind,pair in POND_TOP.items():
                    if b==pair[side]:
                        k=outside_kind(grid[y-1][x]&0x3ff)
                        if k is not None and k!=kind: out.append(('pond-corner-%s-outside-%s'%(kind,k),x,y,b,grid[y-1][x]&0x3ff))
    return out

def findings(grid):
    return ([('rock-comb',)+f for f in rock_comb(grid)]+[('half-tree',)+f for f in half_trees(grid)]+[('rock-alt',)+f for f in alternating_rock(grid)]
            +list(lawn_edge_findings(grid))+list(fence_findings(grid))+list(pond_findings(grid)))

# ---- every tileset: the vocabulary learned from the original maps (edge_learn.py). Warn-only, because a new building or sign legitimately makes pairs the original never has.
def vocab_report(name,grid,before,P,S):
    """(unseen pairs, cells the original decides otherwise) among the cells the edit changed; P,S are the map's ORIGINAL tileset pointers (read them before Tileset.commit)"""
    import edge_learn as EL
    V=EL.Vocab()
    if not V.known(P,S): return None
    h=len(grid); w=len(grid[0])
    ch={(x,y) for y in range(h) for x in range(w) if before is None or y>=len(before) or x>=len(before[0]) or before[y][x]!=grid[y][x]}
    if not ch: return (0,0)
    up=V.pair_findings(grid,P,S,ch); _,rep=V.repair(grid,P,S,ch,rounds=1)
    print('  vocabulary check %s: %d unseen pairs, %d cells the original decides otherwise %s'%(name,len(up),len(rep),rep[:6]))
    return len(up),len(rep)

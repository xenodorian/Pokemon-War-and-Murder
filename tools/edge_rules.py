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
def findings(grid):
    return [('rock-comb',)+f for f in rock_comb(grid)]+[('half-tree',)+f for f in half_trees(grid)]+[('rock-alt',)+f for f in alternating_rock(grid)]
def validate(name,grid,before=None):
    """raise AssertionError listing findings that the edit introduced (findings already in `before` are the original hack's and are tolerated)"""
    old={(f[0],f[1],f[2],f[3],f[4]) for f in findings(before)} if before is not None else set()
    new=[f for f in findings(grid) if (f[0],f[1],f[2],f[3],f[4]) not in old]
    assert not new,'%s: %d edge-rule violations introduced, first: %s'%(name,len(new),new[:8])
    return len(old)

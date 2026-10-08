"""Rebuilds forests so every tree is whole (2 blocks wide, 3 rows tall), following the vanilla forest tessellation:
 tip 0e|0f, first middle 1e|1f, then (join 14|15, middle 1c|1d) pairs, bottom 24|25; the left/right columns of a forest use the plain variants
 (join 16|15 and 14|17, middle 1e|1d and 1c|1f, bottom 26|25 and 24|27). A tree that does not fit becomes lawn.
 Only forest cells near the areas the base builder changed are touched (vanilla forests with special tops/overlaps stay as they are)."""
LEFT={0x0e,0x14,0x16,0x1c,0x1e,0x24,0x26}
RIGHT={0x0f,0x15,0x17,0x1d,0x1f,0x25,0x27}
TREE=LEFT|RIGHT
def kind_of(l,r):
    p=(l&0x3ff,r&0x3ff)
    if p==(0x0e,0x0f): return 'tip'
    if p==(0x1e,0x1f): return 'mid0'
    if p[0] in (0x14,0x16) and p[1] in (0x15,0x17): return 'join'
    if p[0] in (0x1c,0x1e) and p[1] in (0x1d,0x1f): return 'mid'
    if p[0] in (0x24,0x26) and p[1] in (0x25,0x27): return 'bottom'
    return None
def is_pair(grid,w,x,y): return x+1<w and (grid[y][x]&0x3ff) in LEFT and (grid[y][x+1]&0x3ff) in RIGHT
def pair_runs(grid,w,h):
    runs=[]
    for x in range(w-1):
        y=0
        while y<h:
            if is_pair(grid,w,x,y):
                y0=y
                while y<h and is_pair(grid,w,x,y): y+=1
                runs.append((x,y0,y-1))
            else: y+=1
    return runs
NEXT={'tip':'mid0','mid0':'join','mid':'join','join':'mid','bottom':'tip'}
def plan_run(grid,pre,w,h,px,y0,y1):
    """kinds for rows y0..y1 of the pair column px, or None when the run was not cut"""
    L=y1-y0+1
    above_tree=y0>0 and is_pair(pre,w,px,y0-1); below_tree=y1<h-1 and is_pair(pre,w,px,y1+1)
    cut_top=above_tree and not is_pair(grid,w,px,y0-1); cut_bot=below_tree and not is_pair(grid,w,px,y1+1)
    if not (cut_top or cut_bot): return None
    orig=[kind_of(grid[y][px],grid[y][px+1]) or 'mid' for y in range(y0,y1+1)]
    ends_bottom=cut_bot or orig[-1]=='bottom'
    if cut_top:
        if ends_bottom:
            # tip, mid0, (join, mid)*K, bottom: an odd number of rows, at least 3; an extra row at the cut end becomes lawn
            n=L if L%2==1 else L-1; lead=L-n
            if n<3: return ['lawn']*L
            seq=['tip','mid0']
            while len(seq)<n-1: seq.append('join' if seq[-1] in ('mid0','mid') else 'mid')
            seq.append('bottom')
            return ['lawn']*lead+seq
        if L<3: return ['lawn']*L
        seq=['tip','mid0']
        while len(seq)<L: seq.append(NEXT[seq[-1]])
        return seq[:L]
    # only the bottom was cut: keep the top as it is, end with a bottom row after the last middle row that has room for it
    cand=[i for i,t in enumerate(orig) if t in ('mid','mid0') and i+1<=L-1]
    if not cand: return ['lawn']*L
    j=cand[-1]
    return orig[:j+1]+['bottom']+['lawn']*(L-j-2)
def retree(grid,pre,w,h,lawn,zone,ts):
    """grid: current raw block rows (a modified copy is returned); pre: the same map before the cuts; zone: set of (x,y) cells near the cuts"""
    out=[row[:] for row in grid]
    runs=[r for r in pair_runs(grid,w,h) if any(((r[0]+dx,y) in zone) for y in range(r[1],r[2]+1) for dx in (0,1))]
    typ={}
    for (px,y0,y1) in runs:
        seq=plan_run(grid,pre,w,h,px,y0,y1)
        if seq is None: continue
        for i,t in enumerate(seq): typ[(px,y0+i)]=t
    paired=set()
    for x in range(w-1):
        for y in range(h):
            if is_pair(grid,w,x,y): paired.add((x,y)); paired.add((x+1,y))
    # orphan forest cells (half trees) inside the zone
    for (x,y) in zone:
        if 0<=x<w and 0<=y<h and (grid[y][x]&0x3ff) in TREE and (x,y) not in paired: out[y][x]=lawn
    def has(px,y):
        if px<0 or px+1>=w: return True
        if (px,y) in typ: return typ[(px,y)]!='lawn'
        return is_pair(grid,w,px,y)
    for (px,y),t in typ.items():
        if t=='lawn': out[y][px]=lawn; out[y][px+1]=lawn
    def tree_at(x,y):
        if x<0 or x>=w: return True          # beyond the map edge the forest carries on
        if y<0 or y>=h: return True
        return (out[y][x]&0x3ff) in TREE
    def pick(teal,plain,nx,ny,mine_side,toward):
        """the variant whose lawn-coloured corners are closest to the neighbouring block's colour; trees next to trees keep the shaded (teal) variant"""
        if tree_at(nx,ny): return teal
        ca,cb=ts.variant_colors(teal,plain); cn=ts.block_avg(out[ny][nx]&0x3ff)
        d=lambda c: sum((c[k]-cn[k])**2 for k in range(3))
        return teal if d(ca)<=d(cb) else plain
    SETS={'join':((0x14,0x16),(0x15,0x17)),'mid':((0x1c,0x1e),(0x1d,0x1f)),'mid0':((0x1c,0x1e),(0x1d,0x1f)),'bottom':((0x24,0x26),(0x25,0x27))}
    for (px,y),t in typ.items():
        if t=='lawn': continue
        if t=='tip': a,b=0x0e,0x0f
        else:
            (lt,lp),(rt,rp)=SETS[t]
            if t=='bottom' and 0<=y+1<h and not tree_at(px,y+1):
                a=pick(lt,lp,px,y+1,'bottom','top'); b=pick(rt,rp,px+1,y+1,'bottom','top')
            elif t=='mid0':
                a=lp if tree_at(px-1,y) else pick(lt,lp,px-1,y,'left','right')
                b=rp if tree_at(px+2,y) else pick(rt,rp,px+2,y,'right','left')
            else:
                a=pick(lt,lp,px-1,y,'left','right'); b=pick(rt,rp,px+2,y,'right','left')
        out[y][px]=(grid[y][px]&0xfc00)|a; out[y][px+1]=(grid[y][px+1]&0xfc00)|b
    return out

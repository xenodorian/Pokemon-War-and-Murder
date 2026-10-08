"""Map surgery for the JRA bases: extending a town to the east, placing the base building, and picking object positions inside a cloned floor."""
import sys,struct,random,collections
sys.path.insert(0,'/home/claude/work/tools')
import reach
from leg1 import r32,header

def layout_of(r,g,n):
    h=header(r,g,n); return r32(r,h)-0x08000000
def dims(r,g,n):
    lay=layout_of(r,g,n); return r32(r,lay),r32(r,lay+4)
def map_off(r,g,n):
    lay=layout_of(r,g,n); return r32(r,lay+12)-0x08000000
def get_block(r,g,n,x,y):
    w,_=dims(r,g,n); o=map_off(r,g,n)+2*(y*w+x); return struct.unpack('<H',r.b[o:o+2])[0]
def set_block(r,g,n,x,y,v):
    w,h=dims(r,g,n); assert 0<=x<w and 0<=y<h,(x,y,w,h)
    o=map_off(r,g,n)+2*(y*w+x); r.b[o:o+2]=struct.pack('<H',v)
def extend_right(r,g,n,N):
    """append N columns; each new column repeats the old east edge (two columns, alternating), so trees stay trees and an exit road carries on to the new edge.
    The east connection (if any) is anchored to the new edge, so the road still leads to the neighbour."""
    lay=layout_of(r,g,n); w,h=r32(r,lay),r32(r,lay+4); mp=r32(r,lay+12)-0x08000000
    old=[[struct.unpack('<H',r.b[mp+2*(y*w+x):mp+2*(y*w+x)+2])[0] for x in range(w)] for y in range(h)]
    nw=w+N; rows=[]
    for y in range(h):
        rows.append(old[y]+[old[y][w-2+((x-w)%2)] for x in range(w,nw)])
    new=r.alloc(b''.join(struct.pack('<%dH'%nw,*row) for row in rows),4)
    r.w32(lay,nw); r.w32(lay+12,0x08000000+new)
    return nw
def fill(r,g,n,x0,y0,x1,y1,v):
    for y in range(y0,y1+1):
        for x in range(x0,x1+1): set_block(r,g,n,x,y,v)
def copy_rect(r,g,n,sx,sy,w,h,dx,dy):
    blk=[[get_block(r,g,n,sx+i,sy+j) for i in range(w)] for j in range(h)]
    for j in range(h):
        for i in range(w): set_block(r,g,n,dx+i,dy+j,blk[j][i])
def walkable(v): return (v>>10)&3==0

# ------------------------------------------------------------------------------------------------ interior planning
def free_tiles(d,g,n,start,extra_blockers=()):
    w,h,grid,beh,objs=reach.load(d,g,n)
    blk=set(extra_blockers)
    seen={start}; dist={start:0}; q=collections.deque([start])
    while q:
        x,y=q.popleft()
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx,ny=x+dx,y+dy
            if not(0<=nx<w and 0<=ny<h) or (nx,ny) in seen or (nx,ny) in blk: continue
            v=grid[ny][nx]
            if (v>>10)&3: continue
            if beh(v&0x3ff) in (0x38,0x39,0x3a,0x3b): continue
            seen.add((nx,ny)); dist[(nx,ny)]=dist[(x,y)]+1; q.append((nx,ny))
    return dist,(w,h,grid,beh)
def plan_interior(d,g,n,entry,warps,nsold=4,seed='x'):
    """positions for nsold base soldiers and the Captain on the floor of map (g,n), entered at `entry`.
    Rules: plain floor tiles only, away from warps, never blocking: with every object placed as an obstacle, every object must still be reachable from the entrance
    and nothing may become cut off."""
    rng=random.Random('plan-'+seed)
    dist,(w,h,grid,beh)=free_tiles(d,g,n,entry)
    plain=lambda p: grid[p[1]][p[0]]>>10&3==0 and beh(grid[p[1]][p[0]]&0x3ff)==0
    near_warp=lambda p: any(abs(p[0]-wx)+abs(p[1]-wy)<=2 for wx,wy in warps)
    nb=lambda p: [(p[0]+a,p[1]+b) for a,b in ((1,0),(-1,0),(0,1),(0,-1))]
    cand=[p for p in dist if plain(p) and not near_warp(p) and dist[p]>=4]
    maxd=max(dist[p] for p in cand)
    def ok(placed):
        blk=set(placed)
        d2,_=free_tiles(d,g,n,entry,blk)
        # every placed object must be reachable (an adjacent tile reachable) and the number of reachable tiles may only drop by the objects themselves plus tiles that are dead ends
        for p in placed:
            if not any(q in d2 for q in nb(p)): return False
        lost=sum(1 for p in dist if p not in d2 and p not in blk)
        return lost==0
    placed=[]
    # the Captain: deepest tile that is a dead end or a room corner (>=2 walls around), keeping everything else reachable
    order=sorted(cand,key=lambda p:-dist[p])
    cap=None
    for p in order[:60]:
        if ok([p]):
            cap=p; break
    assert cap,'no Captain tile'
    placed=[cap]
    targets=[0.25,0.45,0.62,0.80][:nsold]
    soldiers=[]
    for t in targets:
        want=int(maxd*t)
        tries=sorted(cand,key=lambda p:(abs(dist[p]-want)+rng.random()*3))
        for p in tries:
            if any(abs(p[0]-q[0])+abs(p[1]-q[1])<5 for q in placed): continue
            if any(abs(p[0]-wx)+abs(p[1]-wy)<4 for wx,wy in warps): continue
            if ok(placed+[p]):
                placed.append(p); soldiers.append(p); break
        else: raise AssertionError('no tile for soldier at distance %d'%want)
    def facing(p):
        # face the neighbour that leads back toward the entrance when it is open, else the longest open line
        best=None
        for mv,(a,b) in ((7,(0,-1)),(8,(0,1)),(9,(-1,0)),(10,(1,0))):
            k=0; q=(p[0]+a,p[1]+b)
            while q in dist and k<4: k+=1; q=(q[0]+a,q[1]+b)
            score=(k,-dist.get((p[0]+a,p[1]+b),999))
            if best is None or score>best[0]: best=(score,mv)
        return best[1]
    return [(p,facing(p)) for p in soldiers],(cap,facing(cap))

def insert_rows(r,g,n,at,M,pattern):
    """insert M rows at y=at; the new rows repeat the rows listed in `pattern` alternately (events below `at` are not shifted, so only use where none exist)"""
    lay=layout_of(r,g,n); w,h=r32(r,lay),r32(r,lay+4); mp=r32(r,lay+12)-0x08000000
    old=[list(struct.unpack('<%dH'%w,r.b[mp+2*y*w:mp+2*(y+1)*w])) for y in range(h)]
    new=old[:at]+[list(old[pattern[k%len(pattern)]]) for k in range(M)]+old[at:]
    a=r.alloc(b''.join(struct.pack('<%dH'%w,*row) for row in new),4)
    r.w32(lay+4,h+M); r.w32(lay+12,0x08000000+a)

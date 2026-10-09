"""Custom JRA base interiors, built from the Silph Co / Hideout grey tile blocks (no copied layouts).
Layout (top to bottom): top wall, Hall A (Captain), wall W1, Hall B, wall W2, Hall C (entrance), exit mat on the bottom row.
The two wall gaps sit on opposite sides, so the route zig-zags: entrance -> east gap -> west gap -> Captain."""
import random,collections
FL=0x3000
def walk(b): return FL|b
def solid(b): return 0x0400|b
CAP,FACE,F1,F2,MAT=816,824,821,820,766
PLANT,TABLE=(847,),((835,836),(843,844))
POSTER=(861,869); BIGPOSTER=((862,863),(870,871))
def build(seed,w=28,h=20,nsold=4,decor=True):
    rng=random.Random('room-'+seed)
    g=[[walk(F1) for _ in range(w)] for _ in range(h)]
    cx=w//2
    gap1=rng.randrange(3,7); gap2=w-rng.randrange(6,10)         # west gap in W1, east gap in W2 (both 2 wide)
    y_a0,y_w1,y_b0,y_w2,y_c0=2,6,8,11,13                        # hall A rows 2-5, W1 6-7, hall B 8-10, W2 11-12, hall C 13..h-2
    if h>20: y_c0=13
    lane=set()
    # top wall
    for x in range(w): g[0][x]=solid(CAP); g[1][x]=solid(FACE)
    x=rng.randrange(2,5)
    while x<w-3:
        if rng.random()<0.5: g[0][x]=solid(POSTER[0]); g[1][x]=solid(POSTER[1]); x+=rng.randrange(4,8)
        else:
            g[0][x]=solid(BIGPOSTER[0][0]); g[0][x+1]=solid(BIGPOSTER[0][1]); g[1][x]=solid(BIGPOSTER[1][0]); g[1][x+1]=solid(BIGPOSTER[1][1]); x+=rng.randrange(5,9)
    # partition walls with 2-wide gaps
    for yy,gx in ((y_w1,gap1),(y_w2,gap2)):
        for x in range(w):
            if gx<=x<=gx+1: continue
            g[yy][x]=solid(CAP); g[yy+1][x]=solid(FACE)
    # lane (lighter floor) from the entrance up through both gaps
    for y in range(y_c0,h): g[y][cx]=walk(F2); g[y][cx-1]=walk(F2)
    for x in range(min(cx,gap2),max(cx,gap2)+2): g[y_c0][x]=walk(F2)
    for y in range(y_b0,y_c0): g[y][gap2]=walk(F2); g[y][gap2+1]=walk(F2)
    for x in range(min(gap1,gap2),max(gap1,gap2)+2): g[y_b0][x]=walk(F2)
    for y in range(y_a0,y_b0): g[y][gap1]=walk(F2); g[y][gap1+1]=walk(F2)
    # exit mat on the bottom row, arrival one tile above it
    g[h-1][cx]=walk(MAT); arrival=(cx,h-2); mat=(cx,h-1)
    protect=set()
    for y in range(y_a0,h):
        for x in (gap1,gap1+1,gap2,gap2+1,cx-1,cx,cx+1): protect.add((x,y))
    free=lambda x,y: (x,y) not in protect and g[y][x]==walk(F1) or g[y][x]==walk(F2) and False
    # furniture: plants along the wall faces and 2x2 tables, only on free floor away from the lanes
    def ok2(x,y): return all(0<=x+i<w and y+j<h and (x+i,y+j) not in protect and g[y+j][x+i]==walk(F1) for i in range(2) for j in range(2))
    if decor:
        for hall,(ya,yb) in enumerate(((y_a0,y_w1-1),(y_b0,y_w2-1),(y_c0,h-2))):
            for _ in range(3):
                x=rng.randrange(1,w-3); y=rng.randrange(ya,yb-1)
                if ok2(x,y) and (y+1<=yb) and all((x+i-1,y+j-1) not in protect for i in range(4) for j in range(4)):
                    for j in range(2):
                        for i in range(2): g[y+j][x+i]=solid(TABLE[j][i])
            for x in range(1,w-1):
                if rng.random()<0.18 and (x,ya) not in protect and (x-1,ya) not in protect and (x+1,ya) not in protect and g[ya][x]==walk(F1): g[ya][x]=solid(PLANT[0])
    def free_tile(x,y): return (x,y) not in protect and g[y][x]==walk(F1)
    pick=lambda lo,hi,ya,yb,avoid: next((x,y) for _ in range(400) for x,y in [(rng.randrange(lo,hi),rng.randrange(ya,yb))] if free_tile(x,y) and all(abs(x-a)+abs(y-b)>=5 for a,b in avoid))
    objs=[]; placed=[]
    cap=(w-3,y_a0+1) if free_tile(w-3,y_a0+1) else pick(w-6,w-2,y_a0,y_w1,[])
    placed.append(cap)
    s_a=pick(gap1+4,w//2+3,y_a0,y_w1,placed); placed.append(s_a)
    s_b=pick(2,w//2,y_b0,y_w2,placed); placed.append(s_b)
    s_b2=pick(w//2,w-3,y_b0,y_w2,placed); placed.append(s_b2)
    s_c=pick(2,cx-3,y_c0,h-1,placed); placed.append(s_c)
    soldiers=[s_c,s_b2,s_b,s_a][:nsold]
    return dict(w=w,h=h,grid=g,arrival=arrival,mat=mat,soldiers=soldiers,captain=cap,gaps=(gap1,gap2),cx=cx)
def facing(plan,p):
    """soldiers face along the open lane toward the player's likely approach: horizontally for hall rows"""
    x,y=p; return 10 if x<plan['w']//2 else 9

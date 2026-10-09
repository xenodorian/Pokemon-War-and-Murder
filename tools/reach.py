# usage: reach.py rom group num x0 y0 x1 y1 -> can the player walk from (x0,y0) to a tile next to (x1,y1)? (ledges only go down; cut trees, water and boulders are impassable here)
import sys,struct,collections
def load(d,g,n):
    r32=lambda o: struct.unpack('<I',d[o:o+4])[0]
    G=0x3526A8; gp=r32(G+4*g)-0x08000000; h=r32(gp+4*n)-0x08000000; lay=r32(h)-0x08000000
    w,hh=r32(lay),r32(lay+4); mp=r32(lay+12)-0x08000000
    P=r32(lay+16)-0x08000000; S=r32(lay+20)-0x08000000
    pa=r32(P+20)-0x08000000; sa=r32(S+20)-0x08000000
    def beh(m):
        a=struct.unpack('<I',d[(pa+4*m) if m<640 else (sa+4*(m-640)):][:4])[0]
        return a&0x1ff
    ev=r32(h+4)-0x08000000; po=r32(ev+4)-0x08000000
    objs={}
    for i in range(d[ev]): objs[struct.unpack('<hh',d[po+24*i+4:po+24*i+8])]=d[po+24*i+1]
    grid=[[struct.unpack('<H',d[mp+2*(y*w+x):mp+2*(y*w+x)+2])[0] for x in range(w)] for y in range(hh)]
    return w,hh,grid,beh,objs
def reach(d,g,n,start):
    w,h,grid,beh,objs=load(d,g,n)
    seen={start}; q=collections.deque([start])
    while q:
        x,y=q.popleft()
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx,ny=x+dx,y+dy
            if not(0<=nx<w and 0<=ny<h) or (nx,ny) in seen: continue
            v=grid[ny][nx]; m=v&0x3ff; col=(v>>10)&3
            if col: continue
            b=beh(m)
            if b in (0x38,0x39,0x3a,0x3b): continue
            if (nx,ny) in objs and objs[(nx,ny)] not in (0x98,0x99): continue
            seen.add((nx,ny)); q.append((nx,ny))
    return seen,(w,h)
if __name__=='__main__':
    d=open(sys.argv[1],'rb').read(); g,n,x0,y0,x1,y1=map(int,sys.argv[2:8])
    s,(w,h)=reach(d,g,n,(x0,y0)); print('reached',len(s),'tiles; target',(x1,y1),'reachable' if (x1,y1) in s else 'NOT reachable')

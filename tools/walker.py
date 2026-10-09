# walk-through recorder: plans a tile path on the real map data, drives the emulator with button taps, and records frames
import sys,os,struct,subprocess,collections
sys.path.insert(0,'/home/claude/work/tools')
import reach,t_all
from PIL import Image
os.chdir('/home/claude/work')
KEY={'U':'40','D':'80','L':'20','R':'10'}
DXY={'U':(0,-1),'D':(0,1),'L':(-1,0),'R':(1,0)}
def plan(d,g,n,start,goal,avoid=()):
    w,h,grid,beh,objs=reach.load(d,g,n)
    q=collections.deque([start]); par={start:None}
    while q:
        c=q.popleft()
        if c==goal: break
        for k,(dx,dy) in DXY.items():
            nx,ny=c[0]+dx,c[1]+dy
            if not(0<=nx<w and 0<=ny<h) or (nx,ny) in par: continue
            v=grid[ny][nx]; m=v&0x3ff
            if (v>>10)&3: continue
            if beh(m) in (0x38,0x39,0x3a,0x3b): continue
            if (nx,ny) in objs and objs[(nx,ny)] not in (0x98,0x99) and (nx,ny)!=goal: continue
            par[(nx,ny)]=(c,k); q.append((nx,ny))
    if goal not in par: raise Exception('no path %s -> %s'%(start,goal))
    moves=[]; c=goal
    while par[c]: c,k=par[c][0],par[c][1]; moves.append(k)
    return moves[::-1]
def keys_for(moves,t0,facing='D'):
    ev=[]; t=t0; f=facing
    for m in moves:
        if m!=f: ev.append((t,KEY[m])); t+=14; f=m
        ev.append((t,KEY[m])); t+=19
    return ev,t
def record(name,rom,g,n,start,legs,final_face=None,pokes=(),state='out/base.state',stride=6,end_pad=60):
    """legs: list of (map_group,map_num,goal_tile or None, extra_final_move) executed in order; positions chained by the caller via goals"""
    d=open(rom,'rb').read()
    t_all.make(rom,'out/w_%s.gba'%name,g,n,start[0],start[1])
    ev=[(30,'8')]+[(90+20*i,'80') for i in range(3)]+[(200,'1')]
    t=620; facing='D'; cur=start
    for (lg,ln,goal,warpmove,arrive) in legs:
        moves=plan(d,lg,ln,cur,goal)
        e,t=keys_for(moves,t,facing); ev+=e; facing=moves[-1] if moves else facing
        if warpmove:
            ev.append((t,KEY[warpmove])); ev.append((t+20,KEY[warpmove])); t+=140; facing=warpmove; cur=arrive
        else: cur=goal
    if final_face and final_face!=facing: ev.append((t,KEY[final_face])); t+=30
    t+=end_pad
    L=["setbit 2 fe5 3"]+list(pokes)
    for f,k in ev: L+=[f"{f} {k}",f"{f+4} 0"]
    shots=list(range(560,t,stride))
    for s in shots: L.append(f"shot {s}")
    L.append(f"end {t+2}")
    open('/tmp/claude-0/walk.txt','w').write('\n'.join(L))
    for f in os.listdir('shots'):
        if f.startswith('w_%s_'%name): os.remove('shots/'+f)
    subprocess.run(['./tools/harness_new','out/w_%s.gba'%name,'/tmp/claude-0/walk.txt','shots/w_'+name],env=dict(os.environ,LOADSTATE=state),capture_output=True,timeout=1800)
    return [Image.open('shots/w_%s_%05d.ppm'%(name,s)).convert('RGB') for s in shots]
def save_gif(frames,path,scale=2,ms=110):
    fr=[f.resize((f.width*scale,f.height*scale),Image.NEAREST) for f in frames]
    # drop consecutive duplicates (loading black frames excluded)
    fr[0].save(path,save_all=True,append_images=fr[1:],duration=ms,loop=0,optimize=True)

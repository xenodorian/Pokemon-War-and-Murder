import sys,os,subprocess,struct,random
sys.path.insert(0,'/home/claude/work/tools'); os.chdir('/home/claude/work')
import numpy as np
from PIL import Image
import gun_t3 as t, maprender, reach
ROM=sys.argv[1]; d=open(ROM,'rb').read()
def r32(o): return struct.unpack('<I',d[o:o+4])[0]
def shot_at(name,g,n,x,y,f=1100):
    t.mkw(ROM,'out/rc_%s.gba'%name,g,n,x,y,[])
    L=[]
    for ff,k in [(200,'1'),(440,'8'),(500,'40'),(540,'40'),(580,'40'),(640,'1')]: L+=[f"{ff} {k}",f"{ff+4} 0"]
    L+=[f"shot {f}",f"end {f+6}"]; open('/tmp/claude-0/rc.txt','w').write('\n'.join(L))
    subprocess.run(['./tools/harness_new','out/rc_%s.gba'%name,'/tmp/claude-0/rc.txt','shots/rc_'+name],env=dict(os.environ,LOADSTATE='out/user_new.raw'),capture_output=True,timeout=120)
    return Image.open('shots/rc_%s_%05d.ppm'%(name,f)).convert('RGB')
def entry_of(g,n):
    h=r32(r32(0x3526A8+4*g)-0x08000000+4*n)-0x08000000; ev=r32(h+4)-0x08000000
    nw=d[ev+1]; wp=r32(ev+8)-0x08000000
    return [(struct.unpack('<h',d[wp+8*i:wp+8*i+2])[0],struct.unpack('<h',d[wp+8*i+2:wp+8*i+4])[0]) for i in range(nw)]
def best_shift(scr,full,cx,cy):
    # find where the screen sits in the full render near expected
    S=np.array(scr).astype(int); best=None
    for dx in range(-16,17,1):
        for dy in range(-16,17,1):
            x0=(cx-7)*16+dx; y0=(cy-4)*16+dy
            if x0<0 or y0<0 or x0+240>full.shape[1] or y0+160>full.shape[0]: continue
            c=full[y0:y0+160,x0:x0+240].astype(int)
            e=np.abs(c-S).sum(2).mean()
            if best is None or e<best[0]: best=(e,dx,dy)
    return best
def check(g,n,k=4,seed=1,dxy=None):
    full=np.array(maprender.render(d,g,n).convert('RGB'))
    H,W=full.shape[0]//16,full.shape[1]//16
    ents=entry_of(g,n)
    cand=[]
    for (ex,ey) in ents[:1]:
        pass
    # walkable tiles: reach from any warp tile
    seen=set()
    for (ex,ey) in entry_of(g,n)+[(5,5)]:
        try: s,_=reach.reach(d,g,n,(ex,ey)); seen|=set(s)
        except Exception: pass
    pts=[p for p in seen if 7<=p[0]<=W-8 and 5<=p[1]<=H-6]
    random.Random(seed).shuffle(pts)
    res=[]
    for i,(x,y) in enumerate(pts[:k]):
        scr=shot_at('m%d_%d_%d'%(g,n,i),g,n,x,y)
        if dxy is None:
            b=best_shift(scr,full,x,y)
        else: b=(0,)+dxy
        e,dx,dy=b
        x0=(x-7)*16+dx; y0=(y-4)*16+dy
        c=full[y0:y0+160,x0:x0+240].astype(int); S=np.array(scr).astype(int)
        diff=np.abs(c-S).sum(2)
        cells=diff.reshape(20,8,30,8).max(axis=(1,3))
        frac=(cells>60).mean()
        res.append(((x,y),dx,dy,round(e,1),round(float(frac),3)))
        Image.fromarray(np.concatenate([S.astype(np.uint8),c.astype(np.uint8),np.clip(diff,0,255).astype(np.uint8)[:,:,None].repeat(3,2)],1)).save('shots/rcmp_%d_%d_%d.png'%(g,n,i))
    return res
if __name__=='__main__':
    g,n=int(sys.argv[2]),int(sys.argv[3])
    print(check(g,n,int(sys.argv[4]) if len(sys.argv)>4 else 3))

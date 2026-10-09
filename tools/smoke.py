import sys,os,subprocess,struct,json
sys.path.insert(0,'/home/claude/work/tools'); os.chdir('/home/claude/work')
import numpy as np
from PIL import Image
import gun_t3 as t
ROM=sys.argv[1]
def one(name,g,n,x,y,frames=(900,)):
    t.mkw(ROM,'out/sm_%s.gba'%name,g,n,x,y,[])
    L=[]
    for f,k in [(200,'1'),(440,'8'),(500,'40'),(540,'40'),(580,'40'),(640,'1')]: L+=[f"{f} {k}",f"{f+4} 0"]
    for s in frames: L.append(f"shot {s}")
    L.append("end %d"%(max(frames)+10)); open('/tmp/claude-0/sm.txt','w').write('\n'.join(L))
    subprocess.run(['./tools/harness_new','out/sm_%s.gba'%name,'/tmp/claude-0/sm.txt','shots/sm_'+name],env=dict(os.environ,LOADSTATE='out/user_new.raw'),capture_output=True,timeout=120)
    ims=[np.array(Image.open('shots/sm_%s_%05d.ppm'%(name,s)).convert('RGB')) for s in frames]
    im=ims[-1]; return im.std(), im.mean(), len(set(map(tuple,im.reshape(-1,3)[::37])))
if __name__=='__main__':
    import army
    jobs=[]
    C=army.CITIES
    for c in C:
        e=army.EXT.get(c['name']); 
        if e: jobs.append(('town_'+c['name'],3,c['town'],e['start'][0],e['start'][1]))
    for n in range(69,82): jobs.append(('m2_%d'%n,2,n,5,5))
    jobs+= [('hell',2,68,11,23),('church',2,67,7,12),('camp',3,18,21,16)]
    bad=[]
    for name,g,n,x,y in jobs:
        sd,mean,cols=one(name,g,n,x,y)
        flag='OK' if sd>8 and cols>8 else 'SUSPECT'
        print(name,g,n,(x,y),'std %.1f mean %.0f colors %d'%(sd,mean,cols),flag)

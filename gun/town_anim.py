import sys,os,subprocess
sys.path.insert(0,'/home/claude/work/tools'); os.chdir('/home/claude/work')
from PIL import Image, ImageChops
import numpy as np
import gun_t3 as t
import army
ROM=sys.argv[1]
def shots(name,g,n,x,y,frames):
    t.mkw(ROM,'out/sm_%s.gba'%name,g,n,x,y,[])
    L=[]
    for ff,k in [(200,'1'),(440,'8'),(500,'40'),(540,'40'),(580,'40'),(640,'1')]: L+=[f"{ff} {k}",f"{ff+4} 0"]
    for f in frames: L.append(f"shot {f}")
    L.append(f"end {frames[-1]+10}"); open('/tmp/claude-0/sm.txt','w').write('\n'.join(L))
    subprocess.run(['./tools/harness_new','out/sm_%s.gba'%name,'/tmp/claude-0/sm.txt','shots/sm_'+name],env=dict(os.environ,LOADSTATE='out/user_new.raw'),capture_output=True,timeout=300)
    return [Image.open('shots/sm_%s_%05d.ppm'%(name,f)).convert('RGB') for f in frames]
if __name__=='__main__':
    names=sys.argv[2:]
    for c in army.CITIES:
        if names and c['name'] not in names: continue
        e=army.EXT.get(c['name'])
        if not e: continue
        fr=[900,1000,1100,1200,1300,1400]
        ims=shots('ta_'+c['name'],3,c['town'],e['bx']+2,e['by']+5,fr)
        a=[np.array(i).astype(int) for i in ims]
        d=[int((np.abs(a[i]-a[0]).sum(2)>0).sum()) for i in range(1,6)]
        print(c['name'],'changed pixels vs first:',d)
        W=Image.new('RGB',(240*3,160*2))
        for i,im in enumerate(ims): W.paste(im,((i%3)*240,(i//3)*160))
        W.resize((1440,640),Image.NEAREST).save('shots/ta_%s.png'%c['name'])

import sys,os,subprocess
sys.path.insert(0,'/home/claude/work/tools'); os.chdir('/home/claude/work')
from PIL import Image
import gun_t3 as t
def seq(rom,g,n,x,y,keys,frames,name='seq',cols=6,state='out/user_new.raw',flags=()):
    t.mkw(rom,'out/sq_%s.gba'%name,g,n,x,y,[])
    L=[t.flagpoke(f) for f in flags]
    for ff,k in [(200,'1'),(440,'8'),(500,'40'),(540,'40'),(580,'40'),(640,'1')]+list(keys): L+=[f"{ff} {k}",f"{ff+4} 0"]
    for f in frames: L.append(f"shot {f}")
    L.append(f"end {frames[-1]+10}"); open('/tmp/claude-0/sq.txt','w').write('\n'.join(L))
    subprocess.run(['./tools/harness_new','out/sq_%s.gba'%name,'/tmp/claude-0/sq.txt','shots/sq_'+name],env=dict(os.environ,LOADSTATE=state),capture_output=True,timeout=300)
    ims=[Image.open('shots/sq_%s_%05d.ppm'%(name,f)).convert('RGB') for f in frames]
    rows=(len(ims)+cols-1)//cols; W=Image.new('RGB',(240*cols,160*rows))
    for i,im in enumerate(ims): W.paste(im,((i%cols)*240,(i//cols)*160))
    W.save('shots/sq_%s.png'%name); return W
if __name__=='__main__':
    pass

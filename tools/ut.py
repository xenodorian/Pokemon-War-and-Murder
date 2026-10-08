# tests from the user's save state: the QUESTS entry of the test ROM warps (group,num,x,y); the save dialog in the state finishes first
import sys,subprocess,os
sys.path.insert(0,'/home/claude/work/tools')
import t_all
from PIL import Image
os.chdir('/home/claude/work')
STATE='out/user.state'
def run(name,rom,g,n,x,y,keys=(),shots=(),rams=(),end=900,pokes=(),give=None):
    t_all.make(rom,'out/ut_%s.gba'%name,g,n,x,y,give)
    L=list(pokes)
    P=[(200,'1'),(440,'8'),(500,'40'),(540,'40'),(580,'40'),(640,'1')]+list(keys)
    for f,k in P: L+=[f"{f} {k}",f"{f+4} 0"]
    for s in shots: L.append(f"shot {s}")
    for f,a,c in rams: L.append(f"ram {f} {a:x} {c}")
    L.append(f"end {end}")
    open('/tmp/claude-0/ta.txt','w').write('\n'.join(L))
    for f in os.listdir('shots'):
        if f.startswith('ut_'+name+'_'): os.remove('shots/'+f)
    r=subprocess.run(['./tools/harness_new','out/ut_%s.gba'%name,'/tmp/claude-0/ta.txt','shots/ut_'+name],env=dict(os.environ,LOADSTATE=STATE),capture_output=True,text=True,timeout=600)
    ims=[Image.open('shots/ut_%s_%05d.ppm'%(name,s)) for s in shots]
    cols=min(3,len(ims)); rows=(len(ims)+cols-1)//cols
    W=Image.new('RGB',(240*cols,160*rows))
    for i,im in enumerate(ims): W.paste(im,((i%cols)*240,(i//cols)*160))
    W.resize((W.width*2,W.height*2),Image.NEAREST).save('shots/ut_%s.png'%name)
    return [l for l in (r.stdout+r.stderr).splitlines() if l.startswith('RAM')]

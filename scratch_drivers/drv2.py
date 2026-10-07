import subprocess,os,glob
from PIL import Image
SP='/tmp/claude-0/-home-claude/6e40a750-3062-5a1e-998e-15cd4f95db16/scratchpad/'
def run(name,keys,shots,end,rom='/home/claude/work/ss.gba',state='sw.mgba',extra=()):
    L=list(extra)
    for f,k in keys: L+=[f"{f} {k}",f"{f+4} 0"]
    for s in shots: L.append(f"shot {s}")
    L.append(f"end {end}")
    open(SP+'t2.txt','w').write('\n'.join(L))
    for g in glob.glob(SP+name+'_*.ppm'): os.remove(g)
    subprocess.run(['/home/claude/work/tools/harness_ls',rom,SP+'t2.txt',SP+name],env=dict(os.environ,LOADSTATE=SP+state),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    ims=[Image.open(SP+'%s_%05d.ppm'%(name,s)) for s in shots]
    cols=3;rows=(len(ims)+2)//3
    W=Image.new('RGB',(240*cols,160*rows))
    for i,im in enumerate(ims): W.paste(im,((i%cols)*240,(i//cols)*160))
    W.resize((W.width*2,W.height*2),Image.NEAREST).save(SP+name+'.png')

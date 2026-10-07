import sys,subprocess,os
sys.path.insert(0,'/home/claude/work/tools')
import scr
from PIL import Image
def run(name,rom,keys,flags=(),shots_at=(),end=None,extra=()):
    """keys: list of (frame,hexkey,release_frame). warps via QUESTS entry (DEBUGWARP build)."""
    L=[]
    for f in range(0,5600,8): L+=[f"{f} 1",f"{f+4} 0"]
    L.append("5600 0")
    for fl in flags:
        i={v:k for k,v in scr.FLAGS.items()}[fl]; L.append("setbit 5650 %x %x"%(0xEE0+i//8,1<<(i%8)))
    L+=list(extra)
    L+=["5700 40","5740 0","5800 8","5806 0"]
    t0=5860
    L+=[f"{t0} 80",f"{t0+4} 0"]; t0+=20      # down to QUESTS (no dex/mons yet)
    L+=[f"{t0+40} 1",f"{t0+46} 0"]
    t=t0+110
    L+=[f"{t} 1",f"{t+4} 0"]; t+=200       # select first entry -> debug warp script
    base=t
    for f,k,r in keys: L+=[f"{base+f} {k}",f"{base+r} 0"]
    for s in shots_at: L.append(f"shot {base+s}")
    L.append(f"end {base+(end or max(f for f,_,_ in keys)+100)}")
    open('/home/claude/work/shots/_s3.txt','w').write('\n'.join(L))
    pre='/home/claude/work/shots/'+name
    subprocess.run(['/home/claude/work/tools/harness',rom,'/home/claude/work/shots/_s3.txt',pre],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    ims=[Image.open('%s_%05d.ppm'%(pre,base+s)) for s in shots_at]
    cols=3; rows=(len(ims)+cols-1)//cols
    W=Image.new('RGB',(240*cols,160*rows))
    for i,im in enumerate(ims): W.paste(im,((i%cols)*240,(i//cols)*160))
    W=W.resize((W.width*2,W.height*2),Image.NEAREST); W.save(pre+'_sheet.png'); return pre+'_sheet.png'

import sys; sys.path.insert(0,'/home/claude/work/tools')
import subprocess,struct
from church_test import *
from PIL import Image
def trial(tag,rom,extra_pre,tx=17,ty=6,presses=8):
    L=list(extra_pre)
    L+=["400 40","416 0","450 1","454 0"]
    sh=[]; t=520
    for k in range(presses): L+=[f"{t} 1",f"{t+4} 0"]; sh.append(t+45); t+=75
    L+=["dump %d"%(t+20)]
    run(rom,'out/'+tag,L,sh,t+40)
    W=Image.new('RGB',(240*3,160*((len(sh)+2)//3)))
    for i,s in enumerate(sh):
        subprocess.run(['python3','/home/claude/work/tools/ppm2png.py',S+'t.png','/home/claude/work/out/%s_%05d.ppm'%(tag,s)]); W.paste(Image.open(S+'t.png'),((i%3)*240,(i//3)*160))
    W.save(S+tag+'.png'); return t+20

import sys,os,re
sys.path.insert(0,'.')
from sim import *
def sim2(tid,seed,frames=2600):
    b=bytearray(base); b[i+2]=tid&255; b[i+3]=tid>>8
    open('/home/claude/work/ttr_x.gba','wb').write(b)
    keys=[(60,'8'),(80,'40'),(95,'40'),(110,'1'),(250+seed*7,'1')]
    f=300
    for k in range(int(frames/40)): keys.append((f+seed*3,'1')); f+=40
    os.environ['PCS']=str(frames-300); os.environ['PCE']='7'
    out=go('sim',keys,[frames-50],frames,rom='/home/claude/work/ttr_x.gba',state='fin.mgba')
    pcs=[int(re.search(r'pc=([0-9a-f]+)',l).group(1),16) for l in out.splitlines() if ' pc=' in l]
    inrom=sum(1 for p in pcs if 0x08000000<=p<0x0a000000)
    return inrom,len(pcs)

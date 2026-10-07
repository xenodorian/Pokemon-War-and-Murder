import sys,os,subprocess,re,shutil
sys.path.insert(0,'.')
from mt import *
base=open('/home/claude/work/ttr.gba','rb').read()
i=base.find(bytes([0x5c,0,1,0,0,0]))
assert i>0 and base.count(bytes([0x5c,0,1,0,0,0]))>=1
def sim(tid,seed,frames=2600,rom_path='/home/claude/work/ttr_x.gba'):
    b=bytearray(base); b[i+2]=tid&255; b[i+3]=tid>>8
    open(rom_path,'wb').write(b)
    keys=[(60,'8'),(80,'40'),(95,'40'),(110,'1'),(250+seed*7,'1')]
    f=300
    for k in range(int(frames/40)): keys.append((f+seed*3,'1')); f+=40
    os.environ['PCS']=str(frames-200); os.environ['PCE']='50'
    out=go('sim',keys,[frames-50],frames,rom=rom_path,state='fin.mgba')
    pcs=[l for l in out.splitlines() if ' pc=' in l]
    bad=[l for l in pcs if not re.search(r'pc=0[0-9a-f]{7}',l) or int(re.search(r'pc=([0-9a-f]+)',l).group(1),16)<0x08000000 and int(re.search(r'pc=([0-9a-f]+)',l).group(1),16)>0x3ff]
    return pcs[-1] if pcs else None, bad

import sys,os,re
sys.path.insert(0,'.')
from mt import go
keys=[(40,'8'),(60,'40'),(80,'40'),(100,'40'),(120,'1'),(500,'40'),(520,'40')]
f=560
for i in range(50): keys.append((f,'1')); f+=45
os.environ['PCS']=str(f-300); os.environ['PCE']='7'
shots=[400,540,700,900,1200,1600,2000,2600,f-5]
out=go('jt5',keys,shots,f,rom='/home/claude/work/tjw.gba',state='fin.mgba')
pcs=[int(re.search(r'pc=([0-9a-f]+)',l).group(1),16) for l in out.splitlines() if ' pc=' in l]
print(len(pcs),sorted(set(p>>24 for p in pcs)),[hex(p) for p in pcs[-4:]])

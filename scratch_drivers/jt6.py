import sys,os,re
sys.path.insert(0,'.')
from mt import go
keys=[(40,'8'),(60,'40'),(80,'40'),(100,'40'),(120,'1'),(520,'40')]
f=600
for i in range(60): keys.append((f,'1')); f+=45
os.environ['PCS']=str(f-300); os.environ['PCE']='7'
shots=[500,620,760,900,1100,1400,1800,2400,f-5]
out=go('jt6',keys,shots,f,rom='/home/claude/work/tjw.gba',state='fin.mgba')
pcs=[int(re.search(r'pc=([0-9a-f]+)',l).group(1),16) for l in out.splitlines() if ' pc=' in l]
print(len(pcs),sorted(set(p>>24 for p in pcs)),[hex(p) for p in pcs[-3:]])

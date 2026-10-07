import sys,os; sys.path.insert(0,'.')
from mt import go
keys=[(40,'8'),(60,'80'),(80,'1'),(500,'8'),(540,'40'),(570,'1'),(640,'20')]
f=700
for i in range(40): keys.append((f,'80')); f+=8
keys+= [(1050,'40'),(1100,'1'),(1170,'1')]
f=1240
for i in range(4): keys.append((f,'80')); f+=20
keys.append((1340,'1'))
f=1420
for i in range(8): keys.append((f,'1')); f+=70
go('ev11',keys,[1330,1400,1500,1650,1800,2000,2100,2200],2250,rom='/home/claude/work/tsd.gba',state='sw2.mgba')

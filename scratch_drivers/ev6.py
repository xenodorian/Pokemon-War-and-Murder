import sys,os; sys.path.insert(0,'.')
from mt import go
keys=[(40,'8'),(60,'80'),(80,'1'),(500,'8'),(540,'40'),(570,'1'),(640,'20')]
f=700
for i in range(40): keys.append((f,'80')); f+=8
keys+= [(1050,'40'),(1100,'1'),(1170,'1'),(1250,'1')]
f=1330
for i in range(25): keys.append((f,'1')); f+=50
go('ev6',keys,[1300,1450,1600,1750,1900,2100,2300,2500,2800],2900,rom='/home/claude/work/tsd.gba',state='g24.mgba')

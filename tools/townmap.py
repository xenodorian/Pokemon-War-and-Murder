import sys; sys.path.insert(0,'/home/claude/work/tools')
import gun_t3 as t3
def townmap(rom,g,n,x,y,name='tm',flags=()):
    keys=[(900,'8'),(960,'40'),(1010,'1'),(1100,'10')]+[(1170+30*i,'40') for i in range(7)]+[(1420,'80'),(1460,'80'),(1520,'1'),(1600,'1')]
    t3.run(name,rom,g,n,x,y,[(361,1)],list(flags),keys,[1500,1580,1700,1800],1850)
if __name__=='__main__': townmap(sys.argv[1],*map(int,sys.argv[2:6]))

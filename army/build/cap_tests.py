import sys,struct,os
sys.path.insert(0,'/home/claude/work/tools')
import t_all,army,reach
os.chdir('/home/claude/work')
ROM=sys.argv[1]
d=open(ROM,'rb').read()
r32=lambda o: struct.unpack('<I',d[o:o+4])[0]
def flagpoke(f): return "setbit 3 %x %x"%(0xEE0+(f>>3),1<<(f&7))
BASE={'PEWTER':69,'PALLET':70,'VIRIDIAN':71,'CERULEAN':72,'VERMILION':73,'LAVENDER':74,'CELADON':75,'SAFFRON':76,'FUCHSIA':77,'CINNABAR':78}
def base_info(num):
    gp=r32(0x3526A8+8)-0x08000000; h=r32(gp+4*num)-0x08000000; ev=r32(h+4)-0x08000000; po=r32(ev+4)-0x08000000; wp=r32(ev+8)-0x08000000
    objs=[(d[po+24*i+1],struct.unpack('<hh',d[po+24*i+4:po+24*i+8])) for i in range(d[ev])]
    entry=struct.unpack('<hh',d[wp:wp+4])
    return objs,entry
def captain_test(name):
    c=[x for x in army.CITIES if x['name']==name][0]; num=BASE[name]
    objs,entry=base_info(num)
    cap=[p for g,p in objs if g==0xa0][0]
    seen,_=reach.reach(d,2,num,entry)
    # a reachable neighbour tile (not occupied)
    occ={p for g,p in objs}
    for key,(dx,dy) in (('40',(0,1)),('80',(0,-1)),('20',(1,0)),('10',(-1,0))):   # key to press from the neighbour toward the captain: neighbour = captain - dir
        pass
    cand=[]
    for key,(dx,dy) in (('40',(0,1)),('80',(0,-1)),('20',(1,0)),('10',(-1,0))):
        nb=(cap[0]+dx,cap[1]+dy)
        if nb in seen and nb not in occ: cand.append((key,nb))
    key,nb=cand[0]
    cid=army.ID_POOL[9*c['idx']+4]
    pokes=[flagpoke(0x500+cid)]
    keys=[(380,key)]+[(420+40*i,'1') for i in range(8)]
    tag='cap_'+name
    t_all.run(tag,ROM,2,num,nb[0],nb[1],pokes=pokes,keys=keys,shots=[400,480,560,640,720,760],end=780)
    return tag
if __name__=='__main__':
    for n in sys.argv[2:]: print(captain_test(n))

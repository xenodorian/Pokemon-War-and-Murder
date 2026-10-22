import sys,struct,os
sys.path.insert(0,'/home/claude/work/tools')
import t_all,army
os.chdir('/home/claude/work')
ROM=sys.argv[1] if len(sys.argv)>1 else 'out/c16.gba'
ids=army.ID_POOL
C={c['name']:c for c in army.CITIES}
def flagpoke(f): return "setbit 3 %x %x"%(0xEE0+(f>>3),1<<(f&7))
def sites(name):
    c=C[name]; e=army.EXT.get(name) or dict(bx=33,by=2,guards=[(33,6,10),(38,6,9)],sign=(39,6))
    return c,e,(e['bx']+1,e['by']+3),(e['bx']+1,e['by']+4)
def door(name,medal=True,guards_beaten=True,end=900):
    c,e,dr,fr=sites(name)
    tid=ids[9*c['idx']+7:9*c['idx']+9]
    pokes=[flagpoke(0x500+t) for t in tid] if guards_beaten else []
    give=None
    if medal and c['num']>1:
        prev=[x for x in army.CITIES if x['num']==c['num']-1][0]; give=(prev['item'],1)
    sy=fr[1]+(1 if name!='SAFFRON' else 2)
    sx=fr[0]
    keys=[(380,'40'),(420,'40'),(470,'40')]
    tag='door_%s_%s_%s'%(name,'m' if medal else 'n','g' if guards_beaten else 'x')
    run=t_all.run(tag,ROM,3,army.CITIES[0]['town'] if False else c['town'],sx,sy,pokes=pokes,keys=keys,shots=[360,430,520,640],end=700,give=give)
    return tag
if __name__=='__main__':
    for a in sys.argv[2:]:
        name,medal,gb=a.split(',')
        print(door(name,medal=='1',gb=='1'))

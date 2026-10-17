"""Inventory of every decal object (splatter 152/153/161, feather 155) in every map of a ROM, with the collision/elevation of its tile and its hide flag.
usage: decal_scan.py ROM.gba [OUT.json]"""
import sys,struct,json,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(1,'/home/claude/work/tools')
import leg1
DECAL={152:'splat',153:'body',161:'army_splat',155:'feather'}
def scan(path):
    d=open(path,'rb').read(); r32=lambda o:struct.unpack('<I',d[o:o+4])[0]
    out=[]; gtab=r32(leg1.GROUPS)-0x8000000
    counts=[0]*5
    # map groups: group sizes unknown; walk until pointers stop looking valid
    for g in range(0,5):
        gp=r32(leg1.GROUPS+4*g)-0x8000000
        n=0
        while True:
            hp=r32(gp+4*n)
            if not (0x8000000<=hp<0x8000000+len(d)): break
            h=hp-0x8000000
            try:
                lay=r32(h)-0x8000000; w,hh=struct.unpack('<II',d[lay:lay+8]); mp=r32(lay+12)-0x8000000
                ev=r32(h+4)-0x8000000
                no=d[ev]; po=r32(ev+4)-0x8000000
            except Exception: break
            if not(1<=w<=300 and 1<=hh<=300): break
            for i in range(no):
                o=po+24*i; gfx=d[o+1]
                if gfx in DECAL:
                    x,y=struct.unpack('<hh',d[o+4:o+8])
                    m=struct.unpack('<H',d[mp+2*(y*w+x):mp+2*(y*w+x)+2])[0]
                    out.append(dict(map=(g,n),id=d[o],kind=DECAL[gfx],x=x,y=y,elev=d[o+8]>>4,collision=(m>>10)&3,mapelev=m>>12,flag=struct.unpack('<H',d[o+20:o+22])[0]))
            n+=1
    return out
if __name__=='__main__':
    o=scan(sys.argv[1])
    for e in o: print(e)
    print(len(o),'decals')
    if len(sys.argv)>2: json.dump(o,open(sys.argv[2],'w'))

# usage: patrol.py in.gba out.gba
# Generated police: three hidden officer objects in each gym city, copies of that city's gym trainers. church.c (apply_killed2) shows them at random open spots while the Kill Count is above 10.
import sys,struct
sys.path.insert(0,'/home/claude/work/tools')
from inc import *
import leg1,shinigami
from leg1 import r32,header,free_tile
from shinigami import SB,put_script
T=0x798790
POL0=55; HIDE_FLAG=0x4AD
CLASS_POLICE=91; PIC_POLICE=126; GFX_POLICE=60
CITIES=[((3,1),[350],'VIRIDIAN CITY'),((3,2),[414],'PEWTER CITY'),((3,3),[234],'CERULEAN CITY'),((3,5),[141,423],'VERMILION CITY'),
        ((3,6),[132,265,160,266,267,133,402],'CELADON CITY'),((3,7),[418],'FUCHSIA CITY'),((3,10),[280,283,462,463,464,281],'SAFFRON CITY'),((3,8),[213,177,178,214,179,215,180],'CINNABAR ISLAND')]
NAMES=['JACK','HANK','BOB','DAN','LEE','RAY','TOM','MIKE','FRED','GUS','NED','PAUL','SAM','TIM','VIC','WADE','ZACH','CARL','DEAN','ELI','GREG','IVAN','JOEL','OWEN']
def install(r):
    b=r.b; k=0
    t_intro=0x08000000+r.alloc(leg1.enc("OFFICER: Halt! You have killed too many people. You're under arrest!"),1)
    t_lost=0x08000000+r.alloc(leg1.enc("OFFICER: Argh... You won't get away with this."),1)
    t_after=0x08000000+r.alloc(leg1.enc("OFFICER: Keep killing and there will be more of us."),1)
    for (g,n),pool,city in CITIES:
        h=header(r,g,n); lay=r32(r,h)-0x08000000; w,hh=r32(r,lay),r32(r,lay+4)
        for j in range(3):
            tid=POL0+k; src=pool[j%len(pool)]
            e=bytearray(b[T+40*src:T+40*src+40]); e[1]=CLASS_POLICE; e[3]=PIC_POLICE
            nm=bytes(leg1.ENC[c] for c in NAMES[k]); e[4:16]=nm+b'\xff'*(12-len(nm))
            b[T+40*tid:T+40*tid+40]=e
            S=SB(); S.raw(0x5c,0); S._add(struct.pack('<HH',tid,0)); S.ptr(t_intro); S.ptr(t_lost); S.msg(t_after,6); S.end()
            sc=put_script(r,S)
            ev=r32(r,h+4)-0x08000000; no=b[ev]; po=r32(r,ev+4)-0x08000000
            x,y=free_tile(r,g,n,w//2+j*3-3,hh//2)
            ids=[b[po+24*i] for i in range(no)]
            t=bytearray(24); t[0]=max(ids)+1; t[1]=GFX_POLICE; t[4:6]=struct.pack('<h',x); t[6:8]=struct.pack('<h',y)
            t[8]=3; t[9]=1; t[10]=0x11; t[12:14]=struct.pack('<H',1); t[14:16]=struct.pack('<H',4); t[16:20]=struct.pack('<I',0x08000000+sc); t[20:22]=struct.pack('<H',HIDE_FLAG)
            new=r.alloc(bytes(b[po:po+24*no])+bytes(t),4); b[ev]=no+1; r.w32(ev+4,0x08000000+new)
            k+=1
        print(city,'officers',k)
    assert k==24
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))

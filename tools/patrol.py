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
# Gen 1 species and the level at which each is a natural pick (basic forms 1, evolutions near their evolution level, stone forms at a typical level); legendaries left out
GEN1=[(1,1),(2,16),(3,32),(4,1),(5,16),(6,36),(7,1),(8,16),(9,36),(10,1),(11,7),(12,10),(13,1),(14,7),(15,10),(16,1),(17,18),(18,36),(19,1),(20,20),(21,1),(22,20),(23,1),(24,22),(25,1),(26,30),
 (27,1),(28,22),(29,1),(30,16),(31,30),(32,1),(33,16),(34,30),(35,1),(36,30),(37,1),(38,30),(39,1),(40,30),(41,1),(42,22),(43,1),(44,21),(45,30),(46,1),(47,24),(48,1),(49,31),(50,1),(51,26),
 (52,1),(53,28),(54,1),(55,33),(56,1),(57,28),(58,1),(59,30),(60,1),(61,25),(62,30),(63,1),(64,16),(65,30),(66,1),(67,28),(68,36),(69,1),(70,21),(71,30),(72,1),(73,30),(74,1),(75,25),(76,36),
 (77,1),(78,40),(79,1),(80,37),(81,1),(82,30),(83,1),(84,1),(85,31),(86,1),(87,34),(88,1),(89,38),(90,1),(91,30),(92,1),(93,25),(94,36),(95,1),(96,1),(97,26),(98,1),(99,28),(100,1),(101,30),
 (102,1),(103,30),(104,1),(105,28),(106,20),(107,20),(108,1),(109,1),(110,35),(111,1),(112,42),(113,1),(114,1),(115,1),(116,1),(117,32),(118,1),(119,33),(120,1),(121,30),(122,1),(123,1),(124,1),
 (125,1),(126,1),(127,1),(128,1),(129,1),(130,20),(131,1),(132,1),(133,1),(134,30),(135,30),(136,30),(137,1),(138,1),(139,40),(140,1),(141,40),(142,1),(143,1),(147,1),(148,30),(149,55)]
# town level cap and the gym leader's party size (the soldiers' rules): a soldier has 1..lead Pokemon, each 3-8 levels below the cap (never under 2)
CAPS={(3,1):(10,4),(3,2):(15,2),(3,3):(20,2),(3,5):(25,3),(3,6):(35,3),(3,7):(45,4),(3,10):(40,4),(3,8):(50,4)}
def police_team(g,n,tid):
    import random
    cap,lead=CAPS[(g,n)]; rng=random.Random('police-%d'%tid)
    k=rng.randint(1,lead); levels=sorted(max(2,cap-rng.randint(3,8)) for _ in range(k)); team=[]; used=set()
    for lv in levels:
        elig=[sp for sp,mn in GEN1 if mn<=lv]; near=[sp for sp,mn in GEN1 if lv-20<=mn<=lv]
        pool=[x for x in (near or elig) if x not in used] or elig
        sp=rng.choice(pool); used.add(sp); team.append((sp,lv))
    return team
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
            team=police_team(g,n,tid); pd=b''.join(struct.pack('<HBBHH',160,lv,0,sp,0) for sp,lv in team)
            e[0]=0; e[32]=len(team); e[36:40]=struct.pack('<I',0x08000000+r.alloc(pd,4))
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

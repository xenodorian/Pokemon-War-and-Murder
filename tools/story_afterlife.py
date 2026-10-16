"""MAX's soul in the afterlife (usage: story_afterlife.py IN.gba OUT.gba). Runs after story_viridian.py.
Spec section 5b: after the Viridian loss MAX "goes to heaven or hell, comes back to the screen once, and then STAYS DEAD".
 - the Viridian loss sets VAR_SOUL = 1 (story_viridian.py). In heaven (2,80) or hell (2,68), the first steps away from the arrival tile start the scene:
   MAX's soul (the girl sprite, a hidden object shown only while VAR_SOUL == 1) speaks, fades, VAR_SOUL = 2 (never again).
 - NORMAL run (F_PLAYABLE clear): the visit is only a visit, afterwards LEAF is white-out-restored to the Pokemon Center (special 200, runs the story white-out hooks).
   PLAYABLE run: LEAF stays dead in the afterlife.
 - other deaths (being shot elsewhere) leave VAR_SOUL at 0: no soul."""
import sys,struct,os
sys.path.insert(0,'/home/claude/work/tools'); sys.path.insert(1,os.path.dirname(os.path.abspath(__file__)))
from inc import *
from leg1 import r32,header
from shinigami import SB,put_script,add_obj,add_coord
import story_ids as I, story_text as ST
import story_viridian as V
G=2
SITES=[dict(n=80,name='HEAVEN',obj=(8,22),trig=[(7,24),(8,24),(9,24)],hide=I.HIDE_SOULH,
            lines=["MAX: So this is where it ends for me. Don't mourn, LEAF.","You did what you could. Go on. I will not be back."]),
       dict(n=68,name='HELL',obj=(10,22),trig=[(11,22),(12,22)],hide=I.HIDE_SOULX,
            lines=["MAX: Of course. Even down here I have an escort.","Don't look for me, LEAF. I will not be back."])]
def add_mapscript(r,g,n,typ,ptr):
    """append a map script entry (type, pointer) to the map's table; returns nothing (the table moves to free space)"""
    h=header(r,g,n); ms=r32(r,h+8)-0x08000000 if r32(r,h+8) else None
    ents=[]
    if ms:
        a=ms
        while r.b[a]: ents.append(bytes(r.b[a:a+5])); a+=5
    assert not any(e[0]==typ for e in ents),'type exists'
    ents.append(bytes([typ])+struct.pack('<I',ptr))
    r.w32(h+8,0x08000000+r.alloc(b''.join(ents)+b'\0',4))
def site(r,s):
    n=s['n']; T=lambda t: ST.ptr_s(r,V.wrap(t))
    oid=add_obj(r,G,n,s['obj'][0],s['obj'][1],V.GFX_GIRL,0,0,s['hide'])
    S=SB(); S.lockall(); S.setvar(I.VAR_SOUL,2); S.clearflag(s['hide']); S.addobject(oid)
    S.msg(T(s['lines']),4)
    S.msg(T(["MAX's soul fades away."]),4)
    S.setflag(s['hide']); S.removeobject(oid)
    S.raw(0x2b); S._add(struct.pack('<H',I.F_PLAYABLE)); S.goto_if(1,'stay')
    # NORMAL run: back to the Pokemon Center as after any lost battle
    S.msg(T(["A hand pulls you back toward the living."]),4); S.raw(0x97,1); S.raw(0x25,200,0); S.raw(0x27); S.releaseall(); S.end()
    S.lab('stay'); S.releaseall(); S.end()
    sc=0x08000000+put_script(r,S)
    for x,y in s['trig']: add_coord(r,G,n,x,y,I.VAR_SOUL,1,sc)
    h=header(r,G,n); ev=r32(r,h+4)-0x08000000; cp=r32(r,ev+12)-0x08000000
    for k in range(r.b[ev+2]):
        if r32(r,cp+16*k+12)==sc: r.b[cp+16*k+4]=0        # elevation 0 = any
    L=SB(); L.compare(I.VAR_SOUL,1); L.goto_if(1,'show'); L.setflag(s['hide']); L.end(); L.lab('show'); L.clearflag(s['hide']); L.end()
    add_mapscript(r,G,n,3,0x08000000+put_script(r,L))
    print('afterlife',s['name'],'object',oid)
def install(r):
    for s in SITES: site(r,s)
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))

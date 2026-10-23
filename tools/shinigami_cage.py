"""Shinigami cage (usage: shinigami_cage.py IN.gba OUT.gba), run through tools/patch.sh.
Pewter base (map 2,69): Shinigami moves to (21,3) and is walled in by three iron-bar objects (20,3) (22,3) (21,2) and a gate object at (21,4).
The gate stays shut until the Captain is beaten (flag 0x4C0); talking to it then opens it (HIDE_GATE set, object removed). The old freeing branch in
Shinigami's own script still checks 0x4C0, so nothing else can free him early. Corridor row 5 stays open, so the Captain is reachable."""
import sys,struct,os
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from inc import *
import leg1,shinigami,leg1b
from leg1 import r32,header
from shinigami import SB,put_script,add_obj
from PIL import Image,ImageDraw
import story_text as ST
import story_ids as I
HIDE_GATE=0x880
GFX_SHINI=0x9a
ART=os.path.join(HERE,'..','shinigami_art','bars.png')
def make_bars():
    im=Image.new('RGBA',(16,16),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rectangle([0,0,15,2],fill=(90,90,100,255)); d.rectangle([0,13,15,15],fill=(90,90,100,255))
    for x in (2,6,10,14): d.rectangle([x,0,x+1,15],fill=(60,60,70,255)); d.line([x,0,x,15],fill=(150,150,160,255))
    im.save(ART)
def find_obj(r,po,no,gfx):
    for i in range(no):
        t=po+24*i
        if r.b[t+1]==gfx: return t
    raise SystemExit('object not found')
def install(r):
    make_bars(); bars=leg1b.gfx_add_static16(r,ART)
    h=header(r,2,69); ev=r32(r,h+4)-0x08000000; no=r.b[ev]; po=r32(r,ev+4)-0x08000000
    t=find_obj(r,po,no,GFX_SHINI); assert struct.unpack('<hh',r.b[t+4:t+8])==(21,4),'already caged?'
    r.b[t+6:t+8]=struct.pack('<h',3)
    bars_text=ST.ptr_s(r,["Iron bars. SHINIGAMI sits behind them,\nin chains."])
    S=SB(); S.lock(); S.msg(bars_text,4); S.release(); S.end()
    sb=0x08000000+put_script(r,S)
    for x,y in ((20,3),(22,3),(21,2)): add_obj(r,2,69,x,y,bars,sb,0,0)
    no=r.b[ev]; po=r32(r,ev+4)-0x08000000
    gid=max(r.b[po+24*i] for i in range(no))+1
    G=SB(); G.lock()
    G.raw(0x2b); G._add(struct.pack('<H',I.F_CAPTAIN_DOWN)); G.goto_if(1,'open')
    G.msg(ST.ptr_s(r,["The cell door is locked.\nThe key is on the CAPTAIN."]),4); G.release(); G.end()
    G.lab('open')
    G.msg(ST.ptr_s(r,["You take the key from the CAPTAIN.\nThe cell door swings open."]),4)
    G.playse(39); G.setflag(HIDE_GATE); G.removeobject(gid); G.release(); G.end()
    got=add_obj(r,2,69,21,4,bars,0x08000000+put_script(r,G),0,HIDE_GATE); assert got==gid,(got,gid)
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))

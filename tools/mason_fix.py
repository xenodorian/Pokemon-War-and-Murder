"""Remove the surviving Outlaw rival (Gary) lines (usage: mason_fix.py IN.gba OUT.gba), run through tools/patch.sh.
story_mason.py patched the script copies at the stock addresses, but the Outlaw ROM keeps live copies of several rival scenes elsewhere, still with the old lines
(checked in the emulator: Pokemon Tower 2F showed "MASON: ... Is your POKeMON dead? ... I can at least make them faint!" and then fought JRA SOLDIER WADE).
Every line below is live (a script pointer reaches it). MASON is the protective one who wants LEAF to stay out of the war (CryMon talk.masonFight, masonAfter, masonWin).
 - Pokemon Tower 2F (map 2,61, script 0xeb1b77): intro, talk and defeat text now use the Mason Tower texts of story_mason; the three trainerbattle records 33, 34, 35
   (JRA soldiers since the army stage reused those ids) become MASON record 429.
 - Route 22 gate (script 0x800038): intro and talk use the Mason Route 22 late texts of story_mason.
 - Oak's lab: the rival's 'my Gramps is an old fool' and 'homeless dirtbag' lines, Daisy's 'I wish MASON could learn something'.
 - A trainer's 'complete douchebag' lines, Blaine's 'bribe', the name quiz 'What a jerk'."""
import sys,struct,os
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from inc import *
from g3 import ENC
import story_text as ST
def e(s): return bytes(ENC[c] if c!='\n' else 0xFE for c in s)
def repoint(r,refs,ptr):
    for a in refs:
        old=r32(r,a); assert 0x08100000<=old<0x0a000000,(hex(a),hex(old))
        r.w32(a,ptr)
def r32(r,a): return struct.unpack('<I',r.b[a:a+4])[0]
def install(r):
    b=r.b
    # --- Pokemon Tower 2F: trainers 33..35 -> MASON 429, Mason texts
    for o in (0xeb1c43,0xeb1c4e,0xeb1c59):
        assert b[o]==0x5c and b[o+1]==3 and struct.unpack('<H',b[o+2:o+4])[0] in (33,34,35),hex(o)
        b[o+2:o+4]=struct.pack('<H',429)
    repoint(r,[0xeb1bbf],r32(r,0x1632d9))
    repoint(r,[0xeb1bed],r32(r,0x163307))
    repoint(r,[0xeb1c49,0xeb1c54,0xeb1c5f],r32(r,0x163363))
    # --- Route 22 gate
    repoint(r,[0x80005f],r32(r,0x16844b))
    repoint(r,[0x80008d],r32(r,0x168479))
    # --- Oak's lab
    repoint(r,[0x168ef8],ST.ptr_s(r,["MASON: The Professor means well.\nHe cannot see the war coming.","MASON: Here. A TOWN MAP. Use it to\nfind the way home, LEAF."]))
    repoint(r,[0x1697ed],ST.ptr_s(r,["MASON: You gave LEAF a POKéMON for\nthis? She is a kid, Professor.","MASON: I'm getting a TOWN MAP from\nDAISY. Then I'm following her."]))
    repoint(r,[0x168eda],ST.ptr_s(r,["It looks very happy.","I wish MASON could see this. He\nworries too much about LEAF."]))
    # --- a trainer who met 'a complete douchebag', and the name quiz
    repoint(r,[0x16106b],ST.ptr_s(r,["I met a guy who begged people\nto stay out of this war."]))
    repoint(r,[0x161075],ST.ptr_s(r,["MASON was his name.\nHe might be right."]))
    repoint(r,[0x1305fc],ST.ptr_s(r,["Yup, looks like you remember.\nHis name is MASON! A worrier."]))
    # --- Blaine: the bribe becomes a refused request
    s=0x199543; en=b.index(b'\xff',s); data=bytes(b[s:en+1])
    old=b'\xfd\x06'+e(' gave me a bribe so I')+b'\xfe'+e('gave him a badge.')
    assert old in data
    new=data.replace(old,e("MASON asked me to turn you")+b'\xfe'+e("away. I said no."))
    repoint(r,[0x16d9e7],0x08000000+r.alloc(new,1))
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))

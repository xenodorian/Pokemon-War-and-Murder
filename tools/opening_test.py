"""Plays the new opening from a cold boot in the mGBA harness: names skipped, house, father, shelf (Sandshrew), crate (Potion), door, Mason, Anne.
usage: opening_test.py ROM.gba   Writes shots/op_*.png contact sheets under /home/claude/work/shots."""
import sys,os,struct,subprocess
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(1,'/home/claude/work/tools')
from PIL import Image
K={'W':0,'A':1,'B':2,'S':8,'U':0x40,'D':0x80,'L':0x20,'R':0x10}
def build(steps,start=1250):
    """steps: list of (label, [(key,hold,gap)...]); returns script lines and shot frames"""
    L=["200 8","204 0"]; f=300
    while f<1230: L+=[f"{f} 1",f"{f+4} 0"]; f+=24
    f=start; marks=[]
    for lab,acts in steps:
        for key,hold,gap in acts:
            L+=[f"{f} {K[key]:x}",f"{f+hold} 0"]; f+=hold+gap
        marks.append((lab,f+6))
    return L,marks,f+20
def seq(*s):
    """('D',3): walk 3 tiles down; ('A',n): n presses; ('W',n): wait n frames"""
    out=[]
    for k,n in s:
        if k=='A':
            for _ in range(n): out.append(('A',4,36))
        elif k=='W': out.append(('W',n,0))
        else:
            out.append((k,16*n-4,10))                # n tiles (16 frames per tile; the first frame also turns the player)
    return out
SB1=0x20255a4      # gSaveBlock1 in EWRAM (position x,y at +0); checked against the pointer at 0x3005008 at the end
PARTY=0x2024029      # gPlayerPartyCount
def run(rom,steps,name='op',start=1250):
    os.chdir('/home/claude/work')
    L,marks,end=build(steps,start)
    for lab,fr in marks: L+= [f"shot {fr}",f"ram {fr} {SB1:x} 6",f"ram {fr+1} {PARTY:x} 1"]
    # party count, SB1 position, map, flags/vars region of EWRAM
    L+=[f"ram {end-6} 3005008 4",f"ram {end-5} 2000000 262144",f"end {end}"]
    open('/tmp/claude-0/op.txt','w').write('\n'.join(L))
    for f in os.listdir('shots'):
        if f.startswith(name+'_'): os.remove('shots/'+f)
    r=subprocess.run(['./tools/harness_new',rom,'/tmp/claude-0/op.txt','shots/'+name],capture_output=True,text=True,timeout=1800)
    rams=[l.split() for l in (r.stdout+r.stderr).splitlines() if l.startswith('RAM')]
    rp=[x for x in rams if x[2]=='03005008:'][0]; rw=[x for x in rams if x[2]=='02000000:'][0]
    sb1=struct.unpack('<I',bytes(int(x,16) for x in rp[3:]))[0]; ew=bytes(int(x,16) for x in rw[3:]); o=sb1-0x2000000
    ims=[Image.open('shots/%s_%05d.ppm'%(name,fr)) for _,fr in marks]
    cols=10; rows=(len(ims)+cols-1)//cols
    W=Image.new('RGB',(240*cols,160*rows))
    for i,im in enumerate(ims): W.paste(im,((i%cols)*240,(i//cols)*160))
    W.save('shots/%s.png'%name)
    pos={}
    for l in (r.stdout+r.stderr).splitlines():
        if l.startswith('RAM') and l.split()[2]=='%08x:'%SB1: pos[int(l.split()[1][1:])]=struct.unpack('<hhbb',bytes(int(x,16) for x in l.split()[3:9]))
    pc={}
    for l in (r.stdout+r.stderr).splitlines():
        if l.startswith('RAM') and l.split()[2]=='%08x:'%PARTY: pc[int(l.split()[1][1:])-1]=int(l.split()[3],16)
    flags=lambda f:(ew[o+0xEE0+(f>>3)]>>(f&7))&1
    var=lambda v:struct.unpack('<H',ew[o+0x1000+2*(v-0x4000):o+0x1002+2*(v-0x4000)])[0]
    return marks,dict(flags={hex(f):flags(f) for f in range(0x4EF,0x4F7)},VAR_CRY=var(0x406D),OAK_SCENE=var(0x4050),pos=struct.unpack('<hhbb',ew[o:o+6]),steps=[(lab,pos.get(fr),'party',pc.get(fr)) for lab,fr in marks],sb1=hex(sb1)),ew
def main(rom):
    """house: shelf (Sandshrew), crate (Potion), door, then Pallet: Mason fight and Anne's Poke Balls"""
    steps=[('start',seq(('A',1))),
     ('to shelf',seq(('D',1),('R',4),('U',2))+[('U',3,30)]),
     ('shelf 1',seq(('A',1))),('shelf 2',seq(('A',1))),('shelf 3',seq(('A',1))),
     ('got mon',seq(('A',1),('W',30))),
     ('to crate',seq(('D',2),('R',2))+[('U',3,30)]),
     ('crate 1',seq(('A',1))),('crate 2',seq(('A',1))),('crate done',seq(('A',5),('W',30))),
     ('to door',seq(('L',6),('D',2))),('door',[('D',30,10),('W',200,0)]),
     ('outside',seq(('W',120),('D',1),('U',1),('W',200))),
     ('mason',seq(('A',8),('W',60)))]+[('b%d'%i,seq(('A',1),('W',50))) for i in range(90)]
    marks,info,ew=run(rom,steps)
    print(info)
def main_lab(rom):
    """cold boot into Oak's lab (test ROM with the start moved) and talk to Oak"""
    steps=[('start',seq(('W',10))),('walk',seq(('U',2))),('talk',seq(('A',1),('W',40))),('talk2',seq(('A',1),('W',40))),('talk3',seq(('A',1),('W',40))),('talk4',seq(('A',1),('W',40)))]
    marks,info,ew=run(rom,steps)
    print(info)
if __name__=='__main__': (main_lab if len(sys.argv)>2 and sys.argv[2]=='lab' else main)(sys.argv[1])

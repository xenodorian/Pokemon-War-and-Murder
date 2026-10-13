"""Drive the player in the mGBA harness from a saved game: warp to (group,num,x,y), then press keys, read position and map from RAM, take screenshots.
usage as a module: drive(rom, g, n, x, y, steps, shots=()) -> dict(pos=(x,y), map=(g,n), shots=[paths]); steps = [('D',tiles) | ('A',presses) | ('W',frames)].
The state out/user_new.raw is a late-game save; scripts that depend on early-game flags need their own setup."""
import sys,os,struct,subprocess
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(1,'/home/claude/work/tools')
from PIL import Image
KEY={'U':0x40,'D':0x80,'L':0x20,'R':0x10,'A':1,'B':2,'S':8,'E':4}
def drive(rom,g,n,x,y,steps,shots=(),t0=900,state='out/user_new.raw',tag='ft',pokes=()):
    import gun_t3 as t
    os.chdir('/home/claude/work')
    t.mkw(rom,'out/%s.gba'%tag,g,n,x,y,[])
    L=list(pokes)
    for f,kk in [(200,'1'),(440,'8'),(500,'40'),(540,'40'),(580,'40'),(640,'1')]: L+=[f"{f} {kk}",f"{f+4} 0"]
    f=t0
    for k,v in steps:
        if k=='W': f+=v
        elif k=='A':
            for _ in range(v): L+=[f"{f} 1",f"{f+4} 0"]; f+=40
        else:
            L+=[f"{f} {KEY[k]:x}",f"{f+16*v-4} 0"]; f+=16*v+8
    for s in shots: L.append(f"shot {s}")
    end=f+30
    L+=[f"ram {end-4} 3005008 4",f"ram {end-3} 2000000 262144",f"end {end}"]
    open('/tmp/claude-0/ft.txt','w').write('\n'.join(L))
    for fn in os.listdir('shots'):
        if fn.startswith(tag+'_'): os.remove('shots/'+fn)
    r=subprocess.run(['./tools/harness_new','out/%s.gba'%tag,'/tmp/claude-0/ft.txt','shots/'+tag],env=dict(os.environ,LOADSTATE=state),capture_output=True,text=True,timeout=900)
    rams=[l.split() for l in (r.stdout+r.stderr).splitlines() if l.startswith('RAM')]
    sb=struct.unpack('<I',bytes(int(v,16) for v in rams[0][3:]))[0]; ew=bytes(int(v,16) for v in rams[1][3:]); o=sb-0x2000000
    px,py,mg,mn=struct.unpack('<hhbb',ew[o:o+6])
    return dict(pos=(px,py),map=(mg,mn),shots=['shots/%s_%05d.ppm'%(tag,s) for s in shots],ew=ew,sb=o)
def sheet(paths,out,cols=4,scale=2):
    ims=[Image.open(p) for p in paths]; rows=(len(ims)+cols-1)//cols
    W=Image.new('RGB',(240*cols,160*rows))
    for i,im in enumerate(ims): W.paste(im,((i%cols)*240,(i//cols)*160))
    W.resize((W.width*scale,W.height*scale),Image.NEAREST).save(out)

"""New game from a cold boot: title, new game, names skipped. Prints the player and rival names, position and map from RAM.
usage: newgame_test.py ROM.gba   (needs the mGBA harness in /home/claude/work/tools/harness_new)"""
import sys,os,struct,subprocess
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(1,'/home/claude/work/tools')
from g3 import ENC
DEC={v:k for k,v in ENC.items()}
def run(rom,frames=1500,shots=()):
    os.chdir('/home/claude/work')
    L=["200 8","204 0"]
    f=300
    while f<frames:
        L+=[f"{f} 1",f"{f+4} 0"]; f+=24
    for s in shots: L.append(f"shot {s}")
    L+=[f"ram {frames-12} 3005008 4",f"ram {frames-11} 300500c 4",f"ram {frames-10} 2000000 262144",f"end {frames}"]
    open('/tmp/claude-0/ng.txt','w').write('\n'.join(L))
    r=subprocess.run(['./tools/harness_new',rom,'/tmp/claude-0/ng.txt','shots/ng'],capture_output=True,text=True,timeout=900)
    rams=[l.split() for l in (r.stdout+r.stderr).splitlines() if l.startswith('RAM')]
    sb1=struct.unpack('<I',bytes(int(x,16) for x in rams[0][3:]))[0]; sb2=struct.unpack('<I',bytes(int(x,16) for x in rams[1][3:]))[0]
    ew=bytes(int(x,16) for x in rams[2][3:])
    nm=lambda b:''.join(DEC.get(c,'?') for c in b.split(b'\xff')[0])
    o1=sb1-0x2000000; o2=sb2-0x2000000
    return dict(player=nm(ew[o2:o2+8]),rival=nm(ew[o1+0x3a4c:o1+0x3a4c+8]),pos=struct.unpack('<hh',ew[o1:o1+4]),gender=ew[o2+8])
if __name__=='__main__': print(run(sys.argv[1]))

"""Viridian arrest test, emulator only. Builds a TEST ROM (door warps to Viridian below the Route 1 entrance), then plays key tokens and writes a contact sheet.
usage: viri_test.py "KEYS" OUT.png [STEP] [START]   KEYS as in warp_test.py (U3 D2 L1 R1 A2 W120); STEP = frames between shots (default 30); env VIRI_ROM reuses a built ROM; env TEST_GIVE/TEST_FOE as in cry_open.py
Needs out/user_new.raw."""
import sys,os,subprocess,glob
from PIL import Image
ROOT='/home/claude/work'; os.chdir(ROOT)
keys,out=sys.argv[1],sys.argv[2]; step=int(sys.argv[3]) if len(sys.argv)>3 else 30; start=int(sys.argv[4]) if len(sys.argv)>4 else 1400
rom=os.environ.get('VIRI_ROM') or '/tmp/viri_rom.gba'; script='/tmp/viri_test.txt'
if not os.environ.get('VIRI_ROM'):
    subprocess.run(['sh','tools/apply_all.sh',rom],check=True,env=dict(os.environ,TEST_BATTLE='1',TEST_WARP=os.environ.get('VIRI_WARP','3,1,23,38')),capture_output=True)
KEY={'U':0x40,'D':0x80,'L':0x20,'R':0x10}
L=[]
for f in range(60,600,40): L+=[f"{f} 2",f"{f+4} 0"]
L+=["700 80","760 0"]
f=1400
for tok in keys.split():
    k,v=tok[0],int(tok[1:])
    if k=='W': f+=v
    elif k=='A':
        for _ in range(v): L+=[f"{f} 1",f"{f+4} 0"]; f+=40
    else: L+=[f"{f} {KEY[k]:x}",f"{f+16*v-4} 0"]; f+=16*v+8
for s in range(start,f+60,step): L.append(f"shot {s}")
L.append(f"end {f+60}")
open(script,'w').write('\n'.join(L))
for p in glob.glob('shots/vt_*.ppm'): os.remove(p)
subprocess.run(['./tools/harness_new',rom,script,'shots/vt'],env=dict(os.environ,LOADSTATE='out/user_new.raw'),capture_output=True,timeout=900)
ims=[]
for p in sorted(glob.glob('shots/vt_*.ppm')):
    d=open(p,'rb').read(); pa=d.split(b'\n',3); w,h=map(int,pa[1].split()); ims.append(Image.frombytes('RGB',(w,h),pa[3]))
cols=4; rows=(len(ims)+cols-1)//cols; w,h=ims[0].size
sh=Image.new('RGB',(cols*(w+2),rows*(h+2)))
for i,im in enumerate(ims): sh.paste(im,((i%cols)*(w+2),(i//cols)*(h+2)))
sh.save(out); print(len(ims),'frames',f)

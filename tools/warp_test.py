"""Warp test: builds a TEST ROM (TEST_BATTLE + TEST_WARP=g,n,x,y) where the house door warps to the given map, then walks/presses keys and writes a contact sheet.
usage: warp_test.py G,N,X,Y "KEYS" OUT.png [END]   KEYS: space separated tokens like U3 (up 3 tiles) D2 L1 R1 A2 W120 (wait frames); needs out/user_new.raw"""
import sys,os,subprocess,glob
from PIL import Image
ROOT='/home/claude/work'; os.chdir(ROOT)
warp,keys,out=sys.argv[1],sys.argv[2],sys.argv[3]
tmp=os.environ.get('TMPDIR','/tmp'); rom=os.path.join(tmp,'warp_rom.gba'); script=os.path.join(tmp,'warp_test.txt')
subprocess.run(['sh','tools/apply_all.sh',rom],check=True,env=dict(os.environ,TEST_BATTLE='1',TEST_WARP=warp),capture_output=True)
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
shots=list(range(1400,f+60,max(20,(f-1000)//16)))
for s in shots: L.append(f"shot {s}")
L.append(f"end {f+60}")
open(script,'w').write('\n'.join(L))
for p in glob.glob('shots/wt2_*.ppm'): os.remove(p)
subprocess.run(['./tools/harness_new',rom,script,'shots/wt2'],env=dict(os.environ,LOADSTATE='out/user_new.raw'),capture_output=True,timeout=900)
ims=[]
for p in sorted(glob.glob('shots/wt2_*.ppm')):
    d=open(p,'rb').read(); pa=d.split(b'\n',3); w,h=map(int,pa[1].split()); ims.append(Image.frombytes('RGB',(w,h),pa[3]))
cols=4; rows=(len(ims)+cols-1)//cols; w,h=ims[0].size
sh=Image.new('RGB',(cols*(w+2),rows*(h+2)))
for i,im in enumerate(ims): sh.paste(im,((i%cols)*(w+2),(i//cols)*(h+2)))
sh.save(out); print(len(ims),'frames')

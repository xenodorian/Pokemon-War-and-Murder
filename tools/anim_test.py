"""Animation check: like damage_test.py but takes dense screenshots while the move runs and writes a contact sheet.
usage: anim_test.py LEAF_LEVEL SLOT FOE_SPECIES FOE_LEVEL OUT_SHEET.png [START END STEP]   (needs out/user_new.raw; env LEAF_X etc. tune positions)"""
import sys,os,subprocess,glob
from PIL import Image
ROOT='/home/claude/work'; os.chdir(ROOT)
lv,slot,foe,flv,out=int(sys.argv[1]),int(sys.argv[2]),sys.argv[3],sys.argv[4],sys.argv[5]
S,E,ST=(int(x) for x in (sys.argv[6:9] if len(sys.argv)>8 else (1370,1700,8)))
tmp=os.environ.get('TMPDIR','/tmp'); rom=os.path.join(tmp,'anim_rom.gba'); script=os.path.join(tmp,'anim_test.txt')
subprocess.run(['sh','tools/apply_all.sh',rom],check=True,env=dict(os.environ,TEST_BATTLE='1',TEST_GIVE='%s,%d'%(os.environ.get('SPECIES','107'),lv),TEST_FOE='%s,%s'%(foe,flv)),capture_output=True)
L=[]
for f in range(60,600,40): L+=[f"{f} 2",f"{f+4} 0"]
L+=["700 80","760 0"]
for f in range(1000,1160,30): L+=[f"{f} 1",f"{f+4} 0"]
L+=["1250 1","1254 0"]
t=1320
if slot&2: L+=[f"{t} 80",f"{t+4} 0"]; t+=20
if slot&1: L+=[f"{t} 10",f"{t+4} 0"]; t+=20
L+=[f"{t} 1",f"{t+4} 0"]
print('move chosen at frame',t)
for s in range(S,E,ST): L.append(f"shot {s}")
L.append(f"end {E}")
open(script,'w').write('\n'.join(L))
for p in glob.glob('shots/an_*.ppm'): os.remove(p)
subprocess.run(['./tools/harness_new',rom,script,'shots/an'],env=dict(os.environ,LOADSTATE='out/user_new.raw'),capture_output=True,timeout=900)
ims=[]
for p in sorted(glob.glob('shots/an_*.ppm')):
    d=open(p,'rb').read(); pa=d.split(b'\n',3); w,h=map(int,pa[1].split()); ims.append(Image.frombytes('RGB',(w,h),pa[3]))
cols=6; rows=(len(ims)+cols-1)//cols; w,h=ims[0].size; w2,h2=w*2//3,h*2//3
sh=Image.new('RGB',(cols*(w2+2),rows*(h2+2)),(30,30,30))
for i,im in enumerate(ims): sh.paste(im.resize((w2,h2)),((i%cols)*(w2+2),(i//cols)*(h2+2)))
sh.save(out); print(len(ims),'frames')

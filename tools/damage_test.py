"""Move damage test: builds a TEST ROM (TEST_BATTLE, TEST_GIVE=107,LEVEL, TEST_FOE=SPECIES,LEVEL), starts the wild battle from the house door,
picks FIGHT and a move slot, and samples the enemy and player HP in gBattleMons (0x02023BE4, 0x58 bytes each, hp at +0x28, maxhp +0x2c).
usage: damage_test.py LEAF_LEVEL SLOT FOE_SPECIES FOE_LEVEL OUT_SHEET.png   (SLOT 0..3: 0 top left, 1 top right, 2 bottom left, 3 bottom right)
needs out/user_new.raw (a new-game state, see CURRENT_WORK.md)"""
import sys,os,subprocess,glob,struct
from PIL import Image
ROOT='/home/claude/work'; os.chdir(ROOT)
lv,slot,foe,flv,sheet_out=int(sys.argv[1]),int(sys.argv[2]),sys.argv[3],sys.argv[4],sys.argv[5]
tmp=os.environ.get('TMPDIR','/tmp')
rom=os.path.join(tmp,'damage_rom_%d.gba'%lv); script=os.path.join(tmp,'damage_test.txt')
subprocess.run(['sh','tools/apply_all.sh',rom],check=True,env=dict(os.environ,TEST_BATTLE='1',TEST_GIVE='107,%d'%lv,TEST_FOE='%s,%s'%(foe,flv)),capture_output=True)
L=[]
for f in range(60,600,40): L+=[f"{f} 2",f"{f+4} 0"]
L+=["700 80","760 0"]
for f in range(1000,1160,30): L+=[f"{f} 1",f"{f+4} 0"]     # text until the action menu shows (about frame 1200)
L+=["1250 1","1254 0"]                                       # FIGHT
t=1320
if slot&2: L+=[f"{t} 80",f"{t+4} 0"]; t+=20
if slot&1: L+=[f"{t} 10",f"{t+4} 0"]; t+=20
L+=[f"{t} 1",f"{t+4} 0"]                                    # use the move
END=t+900
for f in range(1200,END,25): L+=[f"ram {f} 2023c0c 2",f"ram {f} 2023c64 2",f"ram {f} 2023c68 2"]
for s in range(1200,END,150): L.append(f"shot {s}")
L.append(f"end {END}")
open(script,'w').write('\n'.join(L))
for p in glob.glob('shots/dt_*.ppm'): os.remove(p)
r=subprocess.run(['./tools/harness_new',rom,script,'shots/dt'],env=dict(os.environ,LOADSTATE='out/user_new.raw'),capture_output=True,text=True,timeout=900)
hp={}
for l in (r.stdout+r.stderr).splitlines():
    if l.startswith('RAM'):
        p=l.split(); f=int(p[1][1:]); a=p[2][:-1]; v=int(p[4],16)*256+int(p[3],16); hp.setdefault(f,{})[a]=v
last=None
for f in sorted(hp):
    cur=(hp[f]['02023c0c'],hp[f]['02023c64'],hp[f]['02023c68'])
    if cur!=last: print('frame',f,'player hp %d, enemy hp %d / %d'%cur); last=cur
ims=[]
for p in sorted(glob.glob('shots/dt_*.ppm')):
    d=open(p,'rb').read(); pa=d.split(b'\n',3); w,h=map(int,pa[1].split()); ims.append(Image.frombytes('RGB',(w,h),pa[3]))
cols=3; rows=(len(ims)+cols-1)//cols; w,h=ims[0].size
sh=Image.new('RGB',(cols*(w+4),rows*(h+4)),(30,30,30))
for i,im in enumerate(ims): sh.paste(im,((i%cols)*(w+4),(i//cols)*(h+4)))
sh.save(sheet_out)

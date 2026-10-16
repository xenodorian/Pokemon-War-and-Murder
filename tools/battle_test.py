"""Battle test: builds a TEST ROM (TEST_BATTLE=1: stepping onto the house door starts a wild Pidgey battle, lv 5),
loads the new-game state, walks onto the door tile, picks FIGHT and the first move, and writes a contact sheet.
usage: battle_test.py OUT_SHEET.png   (needs out/user_new.raw: a new-game state with an empty party, made with the harness SAVEAT hook)
Expect: wild PIDGEY appears, LEAF (stand-in, Lv 1, 1 HP) goes out with BITCH SLAP 1/20 PP, TYPE/FIGHT."""
import sys,os,subprocess,glob
from PIL import Image
ROOT='/home/claude/work'; os.chdir(ROOT)
sheet_out=sys.argv[1]
tmp=os.environ.get('TMPDIR','/tmp')
rom=os.path.join(tmp,'battle_test_rom.gba'); script=os.path.join(tmp,'battle_test.txt')
subprocess.run(['sh','tools/apply_all.sh',rom],check=True,env=dict(os.environ,TEST_BATTLE='1'),capture_output=True)
L=[]
for f in range(60,600,40): L+=[f"{f} 2",f"{f+4} 0"]         # B closes the save prompt in the saved state
L+=["700 80","760 0"]                                        # walk down onto the door tile
for f in range(800,2400,120): L+=[f"{f} 1",f"{f+4} 0"]      # A: advance text, FIGHT, first move
for s in range(700,2400,170): L.append(f"shot {s}")
L.append("end 2400")
open(script,'w').write('\n'.join(L))
for p in glob.glob('shots/bt_*.ppm'): os.remove(p)
subprocess.run(['./tools/harness_new',rom,script,'shots/bt'],env=dict(os.environ,LOADSTATE='out/user_new.raw'),capture_output=True,timeout=900)
ims=[]
for p in sorted(glob.glob('shots/bt_*.ppm')):
    d=open(p,'rb').read(); pa=d.split(b'\n',3); w,h=map(int,pa[1].split()); ims.append(Image.frombytes('RGB',(w,h),pa[3]))
cols=3; rows=(len(ims)+cols-1)//cols; w,h=ims[0].size
sheet=Image.new('RGB',(cols*(w+4),rows*(h+4)),(30,30,30))
for i,im in enumerate(ims): sheet.paste(im,((i%cols)*(w+4),(i//cols)*(h+4)))
sheet.save(sheet_out); print(len(ims),'frames ->',sheet_out)

"""Decal layering/collision walk test, emulator only. Builds a TEST ROM warped next to a decal and walks LEAF over it from the west, the east, the south and the north,
taking a frame every STEP frames; writes a labelled contact sheet.
usage: layer_test.py NAME G,N,X,Y OUT.png [POKES] [FLAGS] [CLEAR]    (X,Y = the decal tile; the player starts 2 tiles west of it)
 POKES  = viri_test VIRI_POKE (e.g. 0x1130=2), FLAGS = VIRI_FLAGS, CLEAR = VIRI_CLEAR. Env ROMSRC=ROM.gba tests an already built ROM-less variant (default: rebuild with apply_all)."""
import sys,os,subprocess,glob
from PIL import Image,ImageDraw
ROOT='/home/claude/work'; os.chdir(ROOT)
name,pos,out=sys.argv[1:4]; pokes=sys.argv[4] if len(sys.argv)>4 else ''; flags=sys.argv[5] if len(sys.argv)>5 else ''; clear=sys.argv[6] if len(sys.argv)>6 else ''
g,n,x,y=[int(v) for v in pos.split(',')]
START=(x-2,y)
# phases: (label, key, tiles)
PH=[('east pass (walk right over it)','R',4),('west pass (walk back left)','L',4),('to the south side','D',2),('(step right)','R',2),('north pass (walk up over it)','U',4),('south pass (walk down over it)','D',4)]
keys='W60 '+' '.join(f'{k}{v}' for _,k,v in PH)+' W20'
env=dict(os.environ,VIRI_WARP=f'{g},{n},{START[0]},{START[1]}',VIRI_POKE=pokes,VIRI_FLAGS=flags,VIRI_CLEAR=clear)
STEP=int(os.environ.get('STEP','14'))
r=subprocess.run(['python3','tools/viri_test.py',keys,'/tmp/_lt.png',str(STEP),'1440'],env=env,capture_output=True,text=True)
ims=[]; fr=[]
for p in sorted(glob.glob('shots/vt_*.ppm')):
    d=open(p,'rb').read(); pa=d.split(b'\n',3); w,h=map(int,pa[1].split()); ims.append(Image.frombytes('RGB',(w,h),pa[3]))
# frame index -> phase label
sched=[]; f=1400+60
for lab,k,v in PH: sched.append((f,f+16*v+8,lab)); f+=16*v+8
def label(i):
    t=1440+i*STEP
    for a,b,l in sched:
        if a<=t<b: return l
    return 'start' if t<1460 else 'end'
cols=7; sc=3
ims=[im.crop((92,48,148,104)) for im in ims]
w,h=ims[0].size; w2,h2=int(w*sc),int(h*sc)
rows=(len(ims)+cols-1)//cols
sheet=Image.new('RGB',(cols*(w2+4),rows*(h2+16)+22),(30,30,30)); dr=ImageDraw.Draw(sheet)
dr.text((4,4),f'{name}: map {g},{n} decal tile ({x},{y}), player starts at {START}; flags/pokes {flags} {pokes} {clear}',fill=(255,255,255))
for i,im in enumerate(ims):
    X=(i%cols)*(w2+4); Y=22+(i//cols)*(h2+16)
    sheet.paste(im.resize((w2,h2)),(X,Y+14)); dr.text((X+2,Y+2),f'{i} {label(i)}'[:40],fill=(255,255,0))
sheet.save(out); print(out,len(ims),'frames')

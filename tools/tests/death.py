import sys,os,subprocess,glob,re
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(R); os.makedirs('/tmp/emu_out',exist_ok=True)
tag=sys.argv[1]; rom='/tmp/emu_out/%s.gba'%tag
subprocess.run(['sh','tools/mk_test_rom.sh',rom],check=True,env=dict(os.environ,TEST_BATTLE='1'),capture_output=True)
L=[]
for f in range(60,600,40): L+=[f"{f} 2",f"{f+4} 0"]
L+=["700 80","760 0"]
for f in range(800,8000,90): L+=[f"{f} 1",f"{f+4} 0"]
shots=[int(x) for x in os.environ.get('SHOTS','1500,2000,2500,3000,3500,4000,4500,5000,5500,6000,6500,7000').split(',')]
L+=[f"shot {s}" for s in shots]
for f in range(800,8000,30): L.append(f"ram {f} 20242da 2")
for f in range(800,8000,300): L.append(f"ram {f} 20370d0 2")
L.append('ram 2100 3005008 4')
for f in range(800,8000,300): L.append(f"ram {f} 20370d0 2")
L+=[f'ram {f} 2026776 2' for f in range(1400,2300,150)]
L.append('end 8000')
open('/tmp/emu_out/%s.txt'%tag,'w').write('\n'.join(L))
for p in glob.glob('shots/%s_*.ppm'%tag): os.remove(p)
res=subprocess.run(['./tools/harness_new',rom,'/tmp/emu_out/%s.txt'%tag,'shots/%s'%tag],env=dict(os.environ,LOADSTATE='saves/ported/new_game_empty_party.raw'),capture_output=True,text=True,timeout=1200)
open('/tmp/emu_out/%s.err'%tag,'w').write(res.stderr)
print([l for l in res.stderr.split('\n') if l.startswith('RAM')][-5:])
from PIL import Image
fs=sorted(glob.glob('shots/%s_*.ppm'%tag)); ims=[Image.open(f) for f in fs]
if ims:
    w,h=ims[0].size; cols=4; rows=(len(ims)+cols-1)//cols
    s=Image.new('RGB',(cols*w,rows*h))
    for i,im in enumerate(ims): s.paste(im,((i%cols)*w,(i//cols)*h))
    s.save('/tmp/emu_out/%s_sheet.png'%tag); print(len(fs),'frames')

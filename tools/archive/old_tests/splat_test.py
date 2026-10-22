"""Walks the player over the Pallet splatter (11,12) from the north, then back from the south, with screenshots, on ROM A and ROM B (before / after).
usage: splat_test.py ROM_A ROM_B   -> shots/splat.png"""
import sys,os,subprocess
sys.path.insert(0,'/home/claude/work/tools'); os.chdir('/home/claude/work')
import gun_t3 as t
from PIL import Image
def run(rom,tag):
    t.mkw(rom,'out/sp_%s.gba'%tag,3,0,11,10,[])
    L=[]
    for f,kk in [(200,'1'),(440,'8'),(500,'40'),(540,'40'),(580,'40'),(640,'1')]: L+=[f"{f} {kk}",f"{f+4} 0"]
    t0=900; shots=[]
    L+=[f"{t0} 80",f"{t0+16*4} 0"]          # south 4 tiles: (11,10) -> (11,14)
    L+=[f"{t0+90} 40",f"{t0+90+16*4} 0"]    # north 4 tiles back
    for f in range(t0+16,t0+16*4+8,8): shots.append(f)
    for f in range(t0+90+16,t0+90+16*4+8,8): shots.append(f)
    for s in shots: L.append(f"shot {s}")
    L.append(f"end {t0+90+16*4+30}")
    open('/tmp/claude-0/sp.txt','w').write('\n'.join(L))
    for f in os.listdir('shots'):
        if f.startswith('sp_%s_'%tag): os.remove('shots/'+f)
    subprocess.run(['./tools/harness_new','out/sp_%s.gba'%tag,'/tmp/claude-0/sp.txt','shots/sp_'+tag],env=dict(os.environ,LOADSTATE='out/user_new.raw'),capture_output=True,text=True,timeout=900)
    return [Image.open('shots/sp_%s_%05d.ppm'%(tag,s)).crop((60,20,180,140)) for s in shots]
a=run(sys.argv[1],'a'); b=run(sys.argv[2],'b')
W=Image.new('RGB',(120*len(a),240))
for i,(x,y) in enumerate(zip(a,b)): W.paste(x,(120*i,0)); W.paste(y,(120*i,120))
W.resize((W.width*2,W.height*2),Image.NEAREST).save('shots/splat.png'); print(W.size)

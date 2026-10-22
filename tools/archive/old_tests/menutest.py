import sys,subprocess,os
from PIL import Image
# usage: menutest.py rom name "keys" ; keys = list of frame:hexkey ; shots after each
def run(rom,name,presses,shots,end,extra=(),state='out/base.state'):
    L=["setbit 2 fe5 3"]+list(extra)
    for f,k in presses: L+=[f"{f} {k}",f"{f+4} 0"]
    for s in shots: L.append(f"shot {s}")
    L.append("ram %d 20370f0 24"%(end-1)); L.append("ram %d 2037150 16"%(end-1)); L.append("ram %d 203ade4 12"%(end-1))
    L.append(f"end {end}")
    open('/tmp/claude-0/mt.txt','w').write('\n'.join(L))
    for g in os.listdir('shots'):
        if g.startswith(name+'_'): os.remove('shots/'+g)
    r=subprocess.run(['./tools/harness_new',rom,'/tmp/claude-0/mt.txt','shots/'+name],env=dict(os.environ,LOADSTATE=state),capture_output=True,text=True,timeout=300)
    ims=[Image.open('shots/%s_%05d.ppm'%(name,s)) for s in shots]
    cols=min(3,len(ims)); rows=(len(ims)+cols-1)//cols
    W=Image.new('RGB',(240*cols,160*rows))
    for i,im in enumerate(ims): W.paste(im,((i%cols)*240,(i//cols)*160))
    W.resize((W.width*2,W.height*2),Image.NEAREST).save('shots/'+name+'.png')
    print('\n'.join(l for l in (r.stdout+r.stderr).splitlines() if l.startswith('RAM')))
if __name__=='__main__':
    rom=sys.argv[1]
    P=[(30,'8')]; f=90
    for k in sys.argv[3].split(','):
        P.append((f,k)); f+=20
    run(rom,sys.argv[2],P,[80]+[90+20*i+14 for i in range(len(sys.argv[3].split(',')))],f+20)

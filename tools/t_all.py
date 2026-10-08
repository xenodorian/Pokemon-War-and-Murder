import sys,struct,subprocess,os
from PIL import Image
sys.path.insert(0,'/home/claude/work/tools')
os.chdir('/home/claude/work')
def make(rom,out,g,n,x,y,give=None):
    d=bytearray(open(rom,'rb').read())
    end=max(i for i in range(0xA00000,len(d)) if d[i]!=0xff)+1; a=(end+3)&~3
    gv=b''
    if give: gv=bytes([0x79])+struct.pack('<H',give[0])+bytes([give[1]])+bytes(2)+bytes(9)
    sc=gv+bytes([0x39,g,n,0xff])+struct.pack('<HH',x,y)+bytes([0x27,0x02]); d[a:a+len(sc)]=sc
    d[0xa01a38:0xa01a3c]=struct.pack('<I',0x08000000+a); open(out,'wb').write(d)
def run(name,rom,g,n,x,y,pokes=(),keys=(),shots=(),rams=(),end=700,flags=True,give=None,state='out/base.state'):
    make(rom,'out/t_%s.gba'%name,g,n,x,y,give)
    L=[]
    if flags: L.append("setbit 2 fe5 3")
    L+=list(pokes)
    P=[(30,'8')]+[(90+20*i,'80') for i in range(3)]+[(200,'1')]+list(keys)
    for f,k in P: L+=[f"{f} {k}",f"{f+4} 0"]
    for s in shots: L.append(f"shot {s}")
    for f,a,c in rams: L.append(f"ram {f} {a:x} {c}")
    L.append(f"end {end}")
    open('/tmp/claude-0/ta.txt','w').write('\n'.join(L))
    for g_ in os.listdir('shots'):
        if g_.startswith('t_'+name+'_'): os.remove('shots/'+g_)
    r=subprocess.run(['./tools/harness_new','out/t_%s.gba'%name,'/tmp/claude-0/ta.txt','shots/t_'+name],env=dict(os.environ,LOADSTATE=state),capture_output=True,text=True,timeout=300)
    ims=[Image.open('shots/t_%s_%05d.ppm'%(name,s)) for s in shots]
    cols=min(3,len(ims)); rows=(len(ims)+cols-1)//cols
    W=Image.new('RGB',(240*cols,160*rows))
    for i,im in enumerate(ims): W.paste(im,((i%cols)*240,(i//cols)*160))
    W.resize((W.width*2,W.height*2),Image.NEAREST).save('shots/t_%s.png'%name)
    return [l for l in (r.stdout+r.stderr).splitlines() if l.startswith('RAM')]

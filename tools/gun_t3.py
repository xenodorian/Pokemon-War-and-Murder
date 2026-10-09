import sys,struct,os,subprocess
sys.path.insert(0,'/home/claude/work/tools'); os.chdir('/home/claude/work')
from PIL import Image
import gun_t2 as t2
def mkw(rom,out,g,n,x,y,gives):
    d=bytearray(open(rom,'rb').read())
    end=max(i for i in range(0xA00000,len(d)) if d[i]!=0xff)+1; a=(end+3)&~3
    sc=b''
    for it,q in gives: sc+=bytes([0x44])+struct.pack('<HH',it,q)
    sc+=bytes([0x39,g,n,0xff])+struct.pack('<HH',x,y)+bytes([0x27,0x02])
    d[a:a+len(sc)]=sc; d[0xa01a38:0xa01a3c]=struct.pack('<I',0x08000000+a); open(out,'wb').write(d)
def flagpoke(f): return "setbit 3 %x %x"%(0xEE0+(f>>3),1<<(f&7))
def run(name,rom,g,n,x,y,gives,flags,keys,shots,end,state='out/user.state',pokes=()):
    mkw(rom,'out/gw_%s.gba'%name,g,n,x,y,gives)
    L=[flagpoke(f) for f in flags]+list(pokes)
    P=[(200,'1'),(440,'8'),(500,'40'),(540,'40'),(580,'40'),(640,'1')]+list(keys)
    for f,k in P: L+=[f"{f} {k}",f"{f+4} 0"]
    for s in shots: L.append(f"shot {s}")
    L.append(f"end {end}")
    open('/tmp/claude-0/ta.txt','w').write('\n'.join(L))
    for f in os.listdir('shots'):
        if f.startswith('gw_'+name+'_'): os.remove('shots/'+f)
    subprocess.run(['./tools/harness_new','out/gw_%s.gba'%name,'/tmp/claude-0/ta.txt','shots/gw_'+name],env=dict(os.environ,LOADSTATE=state),capture_output=True,text=True,timeout=600)
    ims=[Image.open('shots/gw_%s_%05d.ppm'%(name,s)) for s in shots]
    cols=min(3,len(ims)); rows=(len(ims)+cols-1)//cols
    W=Image.new('RGB',(240*cols,160*rows))
    for i,im in enumerate(ims): W.paste(im,((i%cols)*240,(i//cols)*160))
    W.resize((W.width*2,W.height*2),Image.NEAREST).save('shots/gw_%s.png'%name)
G=[(52,1),(53,5),(56,1)]
if __name__=='__main__':
    # talk to the Pallet patrol soldier at (12,4), trainer 16, from (12,5)
    keys=[(900,'40'),(960,'1')]
    run('jmenu','out/c17.gba',3,0,12,5,G,[0x500+16],keys,[880,1000,1100,1200],1200)

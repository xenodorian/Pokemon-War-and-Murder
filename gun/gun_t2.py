import sys,struct,os,subprocess
sys.path.insert(0,'/home/claude/work/tools'); os.chdir('/home/claude/work')
from PIL import Image
STATE='out/user.state'
def mk(rom,out,tid,give=(),setflag=True):
    d=bytearray(open(rom,'rb').read())
    end=max(i for i in range(0xA00000,len(d)) if d[i]!=0xff)+1; a=(end+3)&~3
    sc=b''
    for it,q in give: sc+=bytes([0x44])+struct.pack('<HH',it,q)
    if setflag: sc+=bytes([0x29])+struct.pack('<H',0x500+tid)
    sc+=bytes([0x5c,0])+struct.pack('<HH',tid,0)+struct.pack('<II',0x08000000+a+200,0x08000000+a+200)+bytes([0x02])
    sc=sc.ljust(200,b'\x00')+bytes([0xff])
    d[a:a+len(sc)]=sc; d[0xa01a38:0xa01a3c]=struct.pack('<I',0x08000000+a); open(out,'wb').write(d)
def run(name,rom,tid,give,keys,shots,end,rams=()):
    mk(rom,'out/gt_%s.gba'%name,tid,give)
    L=[]
    P=[(200,'1'),(440,'8'),(500,'40'),(540,'40'),(580,'40'),(640,'1')]+list(keys)
    for f,k in P: L+=[f"{f} {k}",f"{f+4} 0"]
    for s in shots: L.append(f"shot {s}")
    for f,a,c in rams: L.append(f"ram {f} {a:x} {c}")
    L.append(f"end {end}")
    open('/tmp/claude-0/ta.txt','w').write('\n'.join(L))
    for f in os.listdir('shots'):
        if f.startswith('gt_'+name+'_'): os.remove('shots/'+f)
    r=subprocess.run(['./tools/harness_new','out/gt_%s.gba'%name,'/tmp/claude-0/ta.txt','shots/gt_'+name],env=dict(os.environ,LOADSTATE=STATE),capture_output=True,text=True,timeout=600)
    ims=[Image.open('shots/gt_%s_%05d.ppm'%(name,s)) for s in shots]
    cols=min(3,len(ims)); rows=(len(ims)+cols-1)//cols
    W=Image.new('RGB',(240*cols,160*rows))
    for i,im in enumerate(ims): W.paste(im,((i%cols)*240,(i//cols)*160))
    W.resize((W.width*2,W.height*2),Image.NEAREST).save('shots/gt_%s.png'%name)
    return [l for l in (r.stdout+r.stderr).splitlines() if l.startswith('RAM')]
if __name__=='__main__':
    G=[(52,1),(53,5),(56,1)]
    run('menu','out/c17.gba',89,G,[(900,'80'),(960,'1')],[800,860,1000,1100,1200,1300],1300)
    run('menu2','out/c17.gba',620,G,[(900,'80'),(960,'1')],[800,1000,1100,1200,1300,1400],1400)

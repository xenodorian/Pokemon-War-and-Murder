import sys,struct,os,subprocess
sys.path.insert(0,'tools'); os.chdir('/home/claude/work')
from PIL import Image
def run(tid,name):
    d=bytearray(open('out/c17.gba','rb').read())
    end=max(i for i in range(0xA00000,len(d)) if d[i]!=0xff)+1; a=(end+3)&~3
    txt=bytes([0xff]); sc=bytes([0x25,0,0,0x2a])+struct.pack('<H',0x500+tid)+bytes([0x5c,0])+struct.pack('<HH',tid,0)+struct.pack('<II',0x08000000+a+48,0x08000000+a+48)+bytes([0x02])
    sc=sc.ljust(48,b'\x00')+txt
    d[a:a+len(sc)]=sc; d[0xa01a38:0xa01a3c]=struct.pack('<I',0x08000000+a)
    open('out/m_%s.gba'%name,'wb').write(d)
    L=[x for f,k in [(200,"1"),(440,"8"),(500,"40"),(540,"40"),(580,"40")] for x in (f"{f} {k}",f"{f+4} 0")]
    for i,f in enumerate(range(700,6000,40)): L+=[f"{f} {["1","1","1","2"][i%4]}",f"{f+4} 0"]
    shots=list(range(2100,2325,25))[:9]
    L+=[f"shot {s}" for s in shots]+["end 6000"]
    open('/tmp/claude-0/m.txt','w').write('\n'.join(L))
    subprocess.run(['./tools/harness_new','out/m_%s.gba'%name,'/tmp/claude-0/m.txt','shots/m_'+name],env=dict(os.environ,LOADSTATE='out/user.state'),capture_output=True,timeout=300)
    ims=[Image.open('shots/m_%s_%05d.ppm'%(name,s)) for s in shots]
    W=Image.new("RGB",(720,480))
    for i,im in enumerate(ims): W.paste(im,((i%3)*240,(i//3)*160))
    W.resize((1440,960),Image.NEAREST).save('shots/m_%s.png'%name)
for tid,n in ((1,'soldier'),): run(tid,n)

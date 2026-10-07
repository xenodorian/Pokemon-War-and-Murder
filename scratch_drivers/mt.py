import sys,subprocess,os,struct,itertools,re
sys.path.insert(0,'.')
from drv2 import SP
from PIL import Image
def go(name,keys,shots,end,rom='/home/claude/work/tm.gba',state='user.mgba',rams=()):
    L=[]
    for f,k in keys: L+=[f"{f} {k}",f"{f+4} 0"]
    for s in shots: L.append(f"shot {s}")
    for f,a,n in rams: L.append(f"ram {f} {a:x} {n}")
    L.append(f"end {end}")
    open(SP+'t3.txt','w').write('\n'.join(L))
    import glob
    for g in glob.glob(SP+name+'_*.ppm'): os.remove(g)
    r=subprocess.run(['/home/claude/work/tools/harness_ls',rom,SP+'t3.txt',SP+name],env=dict(os.environ,LOADSTATE=SP+state),capture_output=True,text=True)
    ims=[Image.open(SP+'%s_%05d.ppm'%(name,s)) for s in shots]
    cols=3;rows=(len(ims)+2)//3
    W=Image.new('RGB',(240*cols,160*rows))
    for i,im in enumerate(ims): W.paste(im,((i%cols)*240,(i//cols)*160))
    W.resize((W.width*2,W.height*2),Image.NEAREST).save(SP+name+'.png')
    return r.stdout+r.stderr
def ivs(hexdump):
    b=bytes.fromhex(hexdump); pid,otid=struct.unpack('<II',b[:8]); key=pid^otid
    raw=bytearray(b[0x20:0x50])
    for k in range(0,48,4): raw[k:k+4]=struct.pack('<I',struct.unpack('<I',raw[k:k+4])[0]^key)
    perms=list(itertools.permutations('GAEM')); o=perms[pid%24]
    m=raw[o.index('M')*12:][:12]; g=raw[o.index('G')*12:][:12]
    iv=struct.unpack('<I',m[4:8])[0]
    cs=sum(struct.unpack('<24H',raw))&0xffff
    return struct.unpack('<H',g[:2])[0],[(iv>>s)&31 for s in (0,5,10,20,25,15)],cs==struct.unpack('<H',b[0x1c:0x1e])[0], list(struct.unpack('<6H',b[0x56:0x62]))
def seq(n_uses,item_ups,extra_shots=(),state='fin.mgba',rom='/home/claude/work/tm.gba',tag='s'):
    keys=[(60,'8'),(80,'40'),(95,'40'),(110,'1'),(250,'2'),(400,'8'),(430,'40'),(445,'40'),(460,'1'),(560,'20')]
    f=620
    for i in range(45): keys.append((f,'80')); f+=8
    for i in range(item_ups): keys.append((f,'40')); f+=10
    shots=[]; rams=[(f,0x02024414,100)]
    for u in range(n_uses):
        keys.append((f+10,'1')); keys.append((f+60,'1')); f+=140     # open item menu, USE
        if u==0:
            for i in range(4): keys.append((f,'80')); f+=15
        keys.append((f+30,'1')); shots.append(f+100); shots.append(f+160)
        for k in range(5): keys.append((f+200+k*60,'1'))              # dismiss messages
        shots.append(f+420); f+=500
        rams.append((f,0x02024414,100))
        # back in bag
    out=go(tag,keys,shots,f+10,rom=rom,state=state,rams=rams)
    res=[]
    for l in out.splitlines():
        if l.startswith('RAM f'):
            res.append(ivs(''.join(l.split(': ')[1].split())))
    return res

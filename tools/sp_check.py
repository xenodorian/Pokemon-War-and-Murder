import sys,os,struct,subprocess
sys.path.insert(0,'/home/claude/work/tools'); os.chdir('/home/claude/work')
import gun_t3 as t3
def flagset(f): return t3.flagpoke(f)
def mkw(rom,out,g,n,x,y,setvars):
    d=bytearray(open(rom,'rb').read())
    end=max(i for i in range(0xA00000,len(d)) if d[i]!=0xff)+1; a=(end+3)&~3
    sc=b''
    for v,val in setvars: sc+=bytes([0x16])+struct.pack('<HH',v,val)
    sc+=bytes([0x39,g,n,0xff])+struct.pack('<HH',x,y)+bytes([0x27,0x02])
    d[a:a+len(sc)]=sc; d[0xa01a38:0xa01a3c]=struct.pack('<I',0x08000000+a); open(out,'wb').write(d)
def run(name,rom,g,n,x,y,flags,keys,shots,end,pokes=(),setvars=()):
    mkw(rom,'out/gw_%s.gba'%name,g,n,x,y,setvars)
    L=[flagset(f) for f in flags]+list(pokes)
    P=[(200,'1'),(440,'8'),(500,'40'),(540,'40'),(580,'40'),(640,'1')]+list(keys)
    for f,k in P: L+=[f"{f} {k}",f"{f+4} 0"]
    for s in shots: L.append(f"shot {s}")
    L.append(f"ram {end-2} 3005008 4"); L.append(f"ram {end-1} 2000000 262144"); L.append(f"end {end}")
    open('/tmp/claude-0/ta.txt','w').write('\n'.join(L))
    r=subprocess.run(['./tools/harness_new','out/gw_%s.gba'%name,'/tmp/claude-0/ta.txt','shots/gw_'+name],env=dict(os.environ,LOADSTATE='out/user.state'),capture_output=True,text=True,timeout=900)
    rams=[l.split() for l in (r.stdout+r.stderr).splitlines() if l.startswith('RAM')]
    sb=struct.unpack('<I',bytes(int(x,16) for x in rams[0][3:]))[0]; ew=bytes(int(x,16) for x in rams[1][3:]); off=sb-0x2000000
    fl=ew[off+0xEE0:off+0xEE0+0x120]; vs=ew[off+0x1000:off+0x1200]
    return lambda f:(fl[f>>3]>>(f&7))&1, lambda v:struct.unpack('<H',vs[(v-0x4000)*2:(v-0x4000)*2+2])[0], ew, off

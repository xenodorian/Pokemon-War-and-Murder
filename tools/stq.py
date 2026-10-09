# usage: stq.py rom raw_state [frames] -> prints player location, party, flags and vars of a state as the ROM sees them after loading
import os,subprocess,struct,sys
def dump(rom,state,addr,n,frame=4):
    L=[f"ram {frame} {addr:x} {n}",f"end {frame+3}"]
    open('/tmp/claude-0/stq.txt','w').write('\n'.join(L))
    r=subprocess.run(['./tools/harness_new',rom,'/tmp/claude-0/stq.txt','shots/stq'],env=dict(os.environ,LOADSTATE=state),capture_output=True,text=True,cwd='/home/claude/work')
    for l in (r.stdout+r.stderr).splitlines():
        if l.startswith('RAM'):
            p=l.split(); return bytes(int(x,16) for x in p[3:])
def info(rom,state):
    sb=struct.unpack('<I',dump(rom,state,0x3005008,4))[0]
    ew=dump(rom,state,0x2000000,262144)
    off=sb-0x2000000
    fl=ew[off+0xEE0:off+0xEE0+0x120]; vs=ew[off+0x1000:off+0x1200]
    pos=struct.unpack('<hh',ew[off:off+4]); loc=ew[off+4:off+8]
    return dict(sb=sb,ew=ew,off=off,flags=fl,vars=vs,pos=pos,loc=loc)
def flag(i,f): return (i['flags'][f>>3]>>(f&7))&1
def var(i,v): return struct.unpack('<H',i['vars'][(v-0x4000)*2:(v-0x4000)*2+2])[0]
if __name__=='__main__':
    i=info(sys.argv[1],sys.argv[2]); print('sb1',hex(i['sb']),'pos',i['pos'],'loc',i['loc'].hex())
    setf=[f for f in range(0x120*8) if flag(i,f)]
    print('flags set in 0x4A0..0x4FF:',[hex(f) for f in setf if 0x4A0<=f<0x500])
    print('flags 0x3F0..0x3FF:',[hex(f) for f in setf if 0x3F0<=f<0x400])
    print('vars nonzero:',{hex(v):var(i,v) for v in range(0x4000,0x4100) if var(i,v)})

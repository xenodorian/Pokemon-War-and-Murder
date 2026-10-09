import struct,sys
def load(path):
    s=open(path,'rb').read()
    best={}
    for sec in range(len(s)//4096):
        o=sec*4096; sid,chk,sig,cnt=struct.unpack('<HHII',s[o+0xFF4:o+0x1000])
        if sig!=0x8012025: continue
        best.setdefault(cnt,{})[sid]=s[o:o+0xF80]
    cnt=max(k for k in best if len(best[k])>=14)
    secs=best[cnt]
    sb1=b''.join(secs[i] for i in (1,2,3,4))
    return cnt,secs,sb1
def flag(sb1,f): return (sb1[0xEE0+(f>>3)]>>(f&7))&1
def var(sb1,v): return struct.unpack('<H',sb1[0x1000+(v-0x4000)*2:0x1000+(v-0x4000)*2+2])[0]
if __name__=='__main__':
    cnt,secs,sb1=load(sys.argv[1]); print('counter',cnt)
    print('loc',struct.unpack('<bbhh',sb1[0:6]) if False else sb1[:8].hex())
    print('DEAL 0x40AB',var(sb1,0x40AB),'LIB 0x40AC',var(sb1,0x40AC),'PROG 0x40F5',var(sb1,0x40F5),'bless 0x40F4',var(sb1,0x40F4))
    print('POL_HIDE flag 0x4AD',flag(sb1,0x4AD),'cleared flags',[flag(sb1,0x4C0+i) for i in range(11)])

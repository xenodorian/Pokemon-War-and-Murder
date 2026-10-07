# Incremental patching helpers: operate directly on an already built Outlaw ROM (no orig.gba needed).
import struct
from keystone import Ks,KS_ARCH_ARM,KS_MODE_THUMB
ks=Ks(KS_ARCH_ARM,KS_MODE_THUMB)
class Rom:
    def __init__(s,path):
        s.b=bytearray(open(path,'rb').read())
        s.end=max(i for i in range(0xA00000,len(s.b)) if s.b[i]!=0xff)+1
        s.cur=(s.end+3)&~3
    def alloc(s,data,align=4):
        s.cur=(s.cur+align-1)&~(align-1); a=s.cur
        assert s.b[a:a+len(data)]==b'\xff'*len(data),hex(a)
        s.b[a:a+len(data)]=data; s.cur+=len(data); return a
    def asm(s,src,at): 
        enc,_=ks.asm(src,0x08000000+at); return bytes(enc)
    def fn(s,src):
        s.cur=(s.cur+3)&~3
        return s.alloc(s.asm(src,s.cur),4)
    def w32(s,o,v): s.b[o:o+4]=struct.pack('<I',v)
    def r32(s,o): return struct.unpack('<I',s.b[o:o+4])[0]
    def bl(s,at,dst):
        off=dst-(at+4)
        s.b[at:at+4]=struct.pack('<HH',0xF000|((off>>12)&0x7FF),0xF800|((off>>1)&0x7FF))
    def save(s,path): open(path,'wb').write(s.b)
    def put(s,at,data):
        assert s.b[at:at+len(data)]==b'\xff'*len(data),hex(at)
        s.b[at:at+len(data)]=data

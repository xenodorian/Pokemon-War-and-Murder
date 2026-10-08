import sys,struct
from capstone import *
d=open('/home/claude/work/out/c10.gba','rb').read()
md=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
a=int(sys.argv[1],16);b=int(sys.argv[2],16)
for i in md.disasm(d[a:b],0x08000000+a):
    ex=''
    if i.mnemonic=='ldr' and 'pc' in i.op_str:
        off=int(i.op_str.split('#')[1].rstrip(']'),16); la=((i.address+4)&~3)+off-0x08000000; ex='  ; =%08x'%struct.unpack('<I',d[la:la+4])[0]
    print(hex(i.address),i.mnemonic,i.op_str,ex)

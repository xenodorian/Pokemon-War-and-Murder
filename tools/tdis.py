import sys,struct
from capstone import *
import os
ROM=os.environ.get('TROM','/root/.claude/uploads/6e40a750-3062-5a1e-998e-15cd4f95db16/f4046af2-outlaw-2015-09-05.gba')
d=open(ROM,'rb').read()
def dis(start,end):
    md=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
    for i in md.disasm(d[start:end],0x08000000+start):
        a=i.address-0x08000000
        extra=''
        if i.mnemonic=='ldr' and 'pc' in i.op_str:
            import re
            m=re.search(r'#(0x[0-9a-f]+)',i.op_str)
            if m:
                ea=(((i.address+4)&~3)+int(m.group(1),16))-0x08000000
                extra='   ; =0x%08x'%struct.unpack('<I',d[ea:ea+4])[0]
        print('%06x: %-6s %s%s'%(a,i.mnemonic,i.op_str,extra))
if __name__=='__main__':
    dis(int(sys.argv[1],16),int(sys.argv[2],16))

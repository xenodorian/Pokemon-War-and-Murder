"""Make an existing FireRed save show LEAF: sets playerGender (SaveBlock2 + 8) to 1 and the saved player object's graphicsId (SaveBlock1 objectEvents at 0x6A0, isPlayer bit) from Red (0..6) to Leaf (7..13), in both save slots, with sector checksums fixed.
Old saves made before the female-LEAF fix keep gender 0, and Continue respawns the saved Red object, so they show Red until this is applied.
usage: save_leaf.py in.srm out.srm   (writes a new file; never run it on the user's uploaded originals in place)"""
import sys,struct
d=bytearray(open(sys.argv[1],'rb').read())
def ck(b,n):
    s=sum(struct.unpack_from('<%dI'%(n//4),b,0))&0xffffffff
    return ((s>>16)+(s&0xffff))&0xffff
for slot in (0,1):
    for s in range(14):
        off=(slot*14+s)*0x1000
        sid,chk,sig,idx=struct.unpack_from('<HHII',d,off+0xFF4)
        if sig!=0x08012025: continue
        if sid==0:
            d[off+8]=1; struct.pack_into('<H',d,off+0xFF6,ck(d[off:off+0x1000],0xF24))
        elif sid==1:
            for i in range(16):
                e=off+0x6A0+i*0x24
                if d[e]&1 and d[e+2]&1 and d[e+5]<=6: d[e+5]+=7
            struct.pack_into('<H',d,off+0xFF6,ck(d[off:off+0x1000],0xF80))
assert sys.argv[1]!=sys.argv[2]
open(sys.argv[2],'wb').write(d); print('ok')

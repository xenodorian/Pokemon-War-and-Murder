"""Remove framed paintings that a potted plant's leaf top clips (military base maps 2,70..2,79).
Only the painting's own blocks are replaced (row 0 -> 816, row 1 -> 824); leaf tops, pots and
collision bits (0xFC00) are kept. Every cell's old id is asserted before it is written.
usage: base_paintings_clipped.py IN.gba OUT.gba (after base1_paintings.py)"""
import sys,struct
IN=sys.argv[1]
OUT=sys.argv[2]
G=2
# (map, x, y, old_id, new_id)
EDITS={
 70:[(7,0,862,816),(8,0,863,816),(7,1,870,824),
     (19,0,862,816),(20,0,863,816),(20,1,871,824)],
 71:[(9,0,861,816),(9,1,869,824),
     (19,0,862,816),(20,0,863,816),(20,1,871,824)],
 74:[(18,0,862,816),(19,0,863,816),(18,1,870,824),(19,1,871,824)],
 77:[(9,0,862,816),(10,0,863,816),(9,1,870,824),(10,1,871,824),
     (16,0,862,816),(17,0,863,816),(16,1,870,824)],
}
d=bytearray(open(IN,'rb').read())
u32=lambda a:struct.unpack_from('<I',d,a)[0]
gp=u32(0x3526A8+4*G)-0x08000000
n_done=0
for N,edits in EDITS.items():
    hp=u32(gp+4*N)-0x08000000; lay=u32(hp)-0x08000000
    w,h=u32(lay),u32(lay+4); mp=u32(lay+12)-0x08000000
    assert (w,h)==(28,20),(N,w,h)
    for x,y,old,new in edits:
        o=mp+2*(y*w+x); v=struct.unpack_from('<H',d,o)[0]
        assert v&0x3ff==old,(N,x,y,v&0x3ff,old)
        struct.pack_into('<H',d,o,(v&0xfc00)|new); n_done+=1
assert n_done==22,n_done
open(OUT,'wb').write(d)
print('cells changed',n_done,'->',OUT)

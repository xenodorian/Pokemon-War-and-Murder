"""First military base interior (map 2,69): the framed pictures on the north wall are removed (the potted plants' leaf tops clipped through them).
Paintings 861/869 (single) and 862,863/870,871 (wide) become the plain wall blocks 816 (row 0) and 824 (row 1); the cells keep their collision bits.
usage: base1_paintings.py IN.gba OUT.gba"""
import sys,os,struct
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(1,'/home/claude/work/tools')
from inc import Rom
G,N=2,69
WALL={861:816,862:816,863:816,869:824,870:824,871:824}
def apply(r):
    d=r.b; u32=lambda a:struct.unpack_from('<I',d,a)[0]
    gp=u32(0x3526A8+4*G)-0x08000000; hp=u32(gp+4*N)-0x08000000; lay=u32(hp)-0x08000000
    w,h=u32(lay),u32(lay+4); mp=u32(lay+12)-0x08000000
    n=0
    for y in range(h):
        for x in range(w):
            o=mp+2*(y*w+x); v=struct.unpack_from('<H',d,o)[0]
            if (v&0x3ff) in WALL:
                struct.pack_into('<H',d,o,(v&0xfc00)|WALL[v&0x3ff]); n+=1
    assert n==10,n          # three single pictures (2 rows each) and one wide picture (2x2)
    return n
if __name__=='__main__':
    r=Rom(sys.argv[1]); print('cells',apply(r)); r.save(sys.argv[2])

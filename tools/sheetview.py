import struct,sys
sys.path.insert(0,'/home/claude/work/tools')
import gfx
from PIL import Image
def render(rom,gids,out,scale=5):
    d=open(rom,'rb').read()
    def r32(o): return struct.unpack('<I',d[o:o+4])[0]
    pt=r32(0x5f4d8)-0x08000000; n=0
    while struct.unpack('<H',d[pt+8*n+4:pt+8*n+6])[0]!=0x1120: n+=1
    pal=r32(pt+8*n)-0x08000000; cols=gfx.pal_to_rgb(d[pal:pal+32])
    gt=r32(0x5f2f4)-0x08000000
    W=Image.new('RGB',(16*9+20,32*len(gids)),(120,160,120))
    for row,gid in enumerate(gids):
        info=r32(gt+4*gid)-0x08000000; imgt=r32(info+0x1c)-0x08000000
        for f in range(9):
            tp=r32(imgt+8*f)-0x08000000; k=0
            for ty in range(4):
                for tx in range(2):
                    for y in range(8):
                        for x in range(0,8,2):
                            v=d[tp+k]; k+=1
                            for dx,ix in ((0,v&15),(1,v>>4)):
                                if ix: W.putpixel((f*16+tx*8+x+dx,row*32+ty*8+y),cols[ix])
    tp=0x8a09420-0x8000000; k=0
    for ty in range(2):
        for tx in range(2):
            for y in range(8):
                for x in range(0,8,2):
                    v=d[tp+k]; k+=1
                    for dx,ix in ((0,v&15),(1,v>>4)):
                        if ix: W.putpixel((148+tx*8+x+dx,ty*8+y),cols[ix])
    W.resize((W.width*scale,W.height*scale),Image.NEAREST).save(out)
if __name__=='__main__': render(sys.argv[1],[int(x,16) for x in sys.argv[3].split(',')],sys.argv[2])

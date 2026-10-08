# usage: maprender.py rom group num out.png [gray]  -> renders a map layout (both tile layers, no sprites)
import sys,struct
sys.path.insert(0,'/home/claude/work/tools')
import gfx
from PIL import Image
def render(d,g,n,gray=False,tsmod=None):
    def r32(o): return struct.unpack('<I',d[o:o+4])[0]
    G=0x3526A8; gp=r32(G+4*g)-0x08000000; h=r32(gp+4*n)-0x08000000; lay=r32(h)-0x08000000
    w,hh=r32(lay),r32(lay+4); mp=r32(lay+12)-0x08000000
    P=r32(lay+16)-0x08000000; S=r32(lay+20)-0x08000000
    def ts(T):
        comp=d[T]; tiles=r32(T+4)-0x08000000
        data=gfx.lz_decomp(d,tiles) if d[tiles]==0x10 else d[tiles:tiles+0x4000]
        pals=r32(T+8)-0x08000000; mt=r32(T+12)-0x08000000; at=r32(T+16)-0x08000000
        return data,pals,mt,at
    pt,pp,pm,pa=ts(P); st,sp,sm,sa=ts(S)
    cols={}
    for i in range(7): cols[i]=gfx.pal_to_rgb(d[pp+32*i:pp+32*i+32])
    for i in range(7,13): cols[i]=gfx.pal_to_rgb(d[sp+32*i:sp+32*i+32])
    if gray:
        for k in cols: cols[k]=[(int((.3*r+.59*g_+.11*b)),)*3 for r,g_,b in cols[k]]
    def tile(idx,pal,hf,vf):
        data=pt if idx<640 else st; o=(idx if idx<640 else idx-640)*32
        im=Image.new('RGBA',(8,8),(0,0,0,0)); 
        if o+32>len(data): return im
        for y in range(8):
            for x in range(4):
                b=data[o+y*4+x]
                for dx,ix in ((0,b&15),(1,b>>4)):
                    if ix: im.putpixel((2*x+dx,y),cols[pal][ix]+(255,))
        if hf: im=im.transpose(Image.FLIP_LEFT_RIGHT)
        if vf: im=im.transpose(Image.FLIP_TOP_BOTTOM)
        return im
    cache={}
    def mtile(m):
        if m in cache: return cache[m]
        src=pm if m<640 else sm; o=src+16*(m if m<640 else m-640)
        ents=struct.unpack('<8H',d[o:o+16])
        im=Image.new('RGBA',(16,16),(0,0,0,255))
        for layer in (0,1):
            for q in range(4):
                e=ents[layer*4+q]; t=tile(e&0x3ff,e>>12,(e>>10)&1,(e>>11)&1)
                im.alpha_composite(t,((q%2)*8,(q//2)*8))
        cache[m]=im; return im
    out=Image.new('RGBA',(w*16,hh*16),(0,0,0,255))
    for y in range(hh):
        for x in range(w):
            v=struct.unpack('<H',d[mp+2*(y*w+x):mp+2*(y*w+x)+2])[0]
            out.paste(mtile(v&0x3ff),(x*16,y*16))
    return out
if __name__=='__main__':
    d=open(sys.argv[1],'rb').read()
    render(d,int(sys.argv[2]),int(sys.argv[3]),len(sys.argv)>5).convert('RGB').save(sys.argv[4])

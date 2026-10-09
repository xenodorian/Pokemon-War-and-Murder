import sys,struct
sys.path.insert(0,'/home/claude/work/tools')
import gfx
from PIL import Image,ImageDraw
def tileset_ctx(d,g,n):
    def r32(o): return struct.unpack('<I',d[o:o+4])[0]
    gp=r32(0x3526A8+4*g)-0x08000000; h=r32(gp+4*n)-0x08000000; lay=r32(h)-0x08000000
    P=r32(lay+16)-0x08000000; S=r32(lay+20)-0x08000000
    def ts(T):
        tiles=r32(T+4)-0x08000000
        data=gfx.lz_decomp(d,tiles) if d[tiles]==0x10 else d[tiles:tiles+0x3000 if d[T+1] else 0x5000]
        return data,r32(T+8)-0x08000000,r32(T+12)-0x08000000,r32(T+20)-0x08000000
    return ts(P),ts(S)
def make_renderer(d,g,n):
    (pt,pp,pm,pa),(st,sp,sm,sa)=tileset_ctx(d,g,n)
    cols={}
    for i in range(7): cols[i]=gfx.pal_to_rgb(d[pp+32*i:pp+32*i+32])
    for i in range(7,13): cols[i]=gfx.pal_to_rgb(d[sp+32*i:sp+32*i+32])
    def tile(idx,pal,hf,vf):
        data=pt if idx<640 else st; o=(idx if idx<640 else idx-640)*32
        im=Image.new('RGBA',(8,8),(0,0,0,0))
        if o+32>len(data): return im
        for y in range(8):
            for x in range(4):
                b=data[o+y*4+x]
                for dx,ix in ((0,b&15),(1,b>>4)):
                    if ix: im.putpixel((2*x+dx,y),cols[pal][ix]+(255,))
        if hf: im=im.transpose(Image.FLIP_LEFT_RIGHT)
        if vf: im=im.transpose(Image.FLIP_TOP_BOTTOM)
        return im
    def block(m):
        src=pm if m<640 else sm; o=src+16*(m if m<640 else m-640)
        ents=struct.unpack('<8H',d[o:o+16]); im=Image.new('RGBA',(16,16),(0,0,0,255))
        for layer in (0,1):
            for q in range(4):
                e=ents[layer*4+q]; im.alpha_composite(tile(e&0x3ff,e>>12,(e>>10)&1,(e>>11)&1),((q%2)*8,(q//2)*8))
        return im
    def beh(m):
        a=struct.unpack('<I',d[(pa+4*m) if m<640 else (sa+4*(m-640)):][:4])[0]
        return a&0x1ff,(a>>29)&3
    return block,beh
def sheet(d,g,n,ids,cols=16,scale=3,out='sheet.png'):
    block,beh=make_renderer(d,g,n)
    rows=(len(ids)+cols-1)//cols; W=Image.new('RGB',(cols*18*scale,rows*(18*scale+10)),(40,40,40)); dr=ImageDraw.Draw(W)
    for i,m in enumerate(ids):
        im=block(m).convert('RGB').resize((16*scale,16*scale),Image.NEAREST)
        x,y=(i%cols)*18*scale,(i//cols)*(18*scale+10); W.paste(im,(x,y)); dr.text((x,y+16*scale),'%d/%x'%(m,beh(m)[0]),fill=(255,255,0))
    W.save(out)
if __name__=='__main__':
    d=open(sys.argv[1],'rb').read(); ids=list(range(int(sys.argv[3]),int(sys.argv[4]))); sheet(d,2,int(sys.argv[2]),ids,out=sys.argv[5])

import sys,struct
sys.path.insert(0,'/home/claude/work/tools')
from gfx import lz_decomp
from PIL import Image
def load(path,g=3,n=0):
    d=open(path,'rb').read()
    r32=lambda o:struct.unpack('<I',d[o:o+4])[0]
    G=0x3526A8; gp=r32(G+4*g)-0x08000000; h=r32(gp+4*n)-0x08000000
    lay=r32(h)-0x08000000
    return d,lay
def tileset(d,p):
    r32=lambda o:struct.unpack('<I',d[o:o+4])[0]
    comp=d[p]; sec=d[p+1]
    tiles=r32(p+4)-0x08000000; pals=r32(p+8)-0x08000000; mt=r32(p+12)-0x08000000; at=r32(p+20)-0x08000000
    return dict(comp=comp,sec=sec,tiles=tiles,pals=pals,mt=mt,at=at,p=p)
def rgb555(v): return (((v&31)*255//31),(((v>>5)&31)*255//31),(((v>>10)&31)*255//31))
if __name__=='__main__':
    d,lay=load(sys.argv[1],int(sys.argv[3]) if len(sys.argv)>3 else 3,int(sys.argv[4]) if len(sys.argv)>4 else 0)
    r32=lambda o:struct.unpack('<I',d[o:o+4])[0]
    w,h=r32(lay),r32(lay+4); border=r32(lay+8)-0x08000000; mp=r32(lay+12)-0x08000000
    pp=r32(lay+16)-0x08000000; sp=r32(lay+20)-0x08000000
    P=tileset(d,pp); S=tileset(d,sp)
    print('layout',hex(lay),w,h,'prim',P,'sec',S)
    def decode(T,sz=None):
        t=lz_decomp(d,T['tiles']) if T['comp'] else d[T['tiles']:T['tiles']+sz]
        return t
    pt=decode(P); st=decode(S)
    print('prim tiles',len(pt)//32,'sec tiles',len(st)//32)
    def pals(T,rng):
        out={}
        for i in rng:
            out[i]=[rgb555(struct.unpack('<H',d[T['pals']+32*i+2*c:T['pals']+32*i+2*c+2])[0]) for c in range(16)]
        return out
    PAL=pals(P,range(0,7)); PAL.update(pals(S,range(7,13)))
    def tile_img(idx,pal,hf,vf):
        if idx<640: data=pt[idx*32:idx*32+32]
        else: data=st[(idx-640)*32:(idx-640)*32+32] 
        px=[]
        for y in range(8):
            row=[]
            for x in range(8):
                b=data[y*4+x//2]; c=(b>>4) if x&1 else (b&15); row.append(c)
            px.append(row)
        if hf: px=[r[::-1] for r in px]
        if vf: px=px[::-1]
        return px
    def metatile(m):
        if m<640: base=P['mt']+16*m
        else: base=S['mt']+16*(m-640)
        return [struct.unpack('<H',d[base+2*i:base+2*i+2])[0] for i in range(8)]
    def render_mt(m):
        e=metatile(m); img=Image.new('RGB',(16,16),PAL[0][0])
        for layer in (0,1):
            for q in range(4):
                v=e[layer*4+q]; idx=v&0x3ff; hf=(v>>10)&1; vf=(v>>11)&1; pl=v>>12
                px=tile_img(idx,pl,hf,vf)
                for y in range(8):
                    for x in range(8):
                        c=px[y][x]
                        if c==0 and True: continue
                        img.putpixel(((q&1)*8+x,(q>>1)*8+y),PAL[pl][c])
        return img
    out=Image.new('RGB',(w*16,h*16))
    for y in range(h):
        for x in range(w):
            b=struct.unpack('<H',d[mp+2*(y*w+x):mp+2*(y*w+x)+2])[0]
            out.paste(render_mt(b&0x3ff),(x*16,y*16))
    out.save(sys.argv[2])

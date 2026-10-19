"""Render FireRed map layouts and metatile sheets from a ROM (read only).
usage: tilemap_render.py ROM.gba map G N OUT.png [scale]   |   tilemap_render.py ROM.gba sheet PRIMARY_PTR SECONDARY_PTR OUT.png
In 'sheet' mode every metatile is drawn with its id and layer type (N normal, C covered, S split); 'map' mode draws bottom then top layer."""
import sys,struct,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from PIL import Image,ImageDraw
import gfx
class TS:
    def __init__(s,d,p,sec):
        r32=lambda o:struct.unpack('<I',d[o:o+4])[0]
        o=p-0x8000000; s.comp=d[o]; tp=r32(o+4)-0x8000000; s.pal=r32(o+8)-0x8000000; s.meta=r32(o+12)-0x8000000; s.attr=r32(o+20)-0x8000000
        s.tiles=gfx.lz_decomp(d,tp) if s.comp else d[tp:tp+(640 if not sec else 384)*32]
        if isinstance(s.tiles,tuple): s.tiles=s.tiles[0]
def load(d,p1,p2):
    a=TS(d,p1,0); b=TS(d,p2,1)
    pals=[]
    for i in range(16):
        src=a.pal if i<7 else b.pal
        pals.append([struct.unpack('<H',d[src+32*i+2*c:src+32*i+2*c+2])[0] for c in range(16)])
    rgb=[[((v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31) for v in p] for p in pals]
    return a,b,rgb
def tile_px(a,b,t):
    src,i=(a.tiles,t) if t<640 else (b.tiles,t-640)
    raw=bytes(src[32*i:32*i+32]) if 32*i+32<=len(src) else bytes(32)
    return [[(raw[y*4+x//2]>>(4*(x&1)))&15 for x in range(8)] for y in range(8)]
def meta_entries(d,a,b,m):
    base,idx=(a.meta,m) if m<640 else (b.meta,m-640)
    e=struct.unpack('<8H',d[base+16*idx:base+16*idx+16])
    at=struct.unpack('<I',d[(a.attr if m<640 else b.attr)+4*idx:(a.attr if m<640 else b.attr)+4*idx+4])[0]
    return e,at
def draw_meta(img,ox,oy,d,a,b,rgb,m,layers=(0,1),bg=(255,0,255)):
    e,at=meta_entries(d,a,b,m)
    for L in layers:
        for q in range(4):
            v=e[L*4+q]; t=v&0x3ff; hf=v>>10&1; vf=v>>11&1; pal=v>>12
            px=tile_px(a,b,t)
            for y in range(8):
                for x in range(8):
                    c=px[7-y if vf else y][7-x if hf else x]
                    if c==0 and L==1: continue
                    col=rgb[pal][c] if c else (rgb[pal][0] if L==0 else None)
                    if col: img.putpixel((ox+(q&1)*8+x,oy+(q>>1)*8+y),col)
    return at
def main():
    d=open(sys.argv[1],'rb').read(); r32=lambda o:struct.unpack('<I',d[o:o+4])[0]
    if sys.argv[2]=='map':
        import leg1
        g,n=int(sys.argv[3]),int(sys.argv[4]); out=sys.argv[5]; sc=int(sys.argv[6]) if len(sys.argv)>6 else 2
        gp=r32(leg1.GROUPS+4*g)-0x8000000; h=r32(gp+4*n)-0x8000000; lay=r32(h)-0x8000000
        w,hh=struct.unpack('<II',d[lay:lay+8]); mp=r32(lay+12)-0x8000000
        a,b,rgb=load(d,r32(lay+16),r32(lay+20))
        img=Image.new('RGB',(w*16,hh*16))
        for y in range(hh):
            for x in range(w):
                v=struct.unpack('<H',d[mp+2*(y*w+x):mp+2*(y*w+x)+2])[0]; draw_meta(img,x*16,y*16,d,a,b,rgb,v&0x3ff)
        img=img.resize((w*16*sc,hh*16*sc),Image.NEAREST); dr=ImageDraw.Draw(img)
        for y in range(hh):
            for x in range(w):
                v=struct.unpack('<H',d[mp+2*(y*w+x):mp+2*(y*w+x)+2])[0]
                dr.text((x*16*sc+1,y*16*sc+1),'%d'%(v&0x3ff),fill=(255,255,0)); 
                if (v>>10)&3: dr.text((x*16*sc+1,y*16*sc+11*sc//2+4),'#',fill=(255,0,0))
        img.save(out)
    else:
        p1,p2=int(sys.argv[3],16),int(sys.argv[4],16); out=sys.argv[5]
        a,b,rgb=load(d,p1,p2)
        ids=list(range(640,640+int(os.environ.get('NSEC','192'))))+([] if not os.environ.get('PRIM') else list(range(0,int(os.environ['PRIM']))))
        cols=int(os.environ.get('COLS','16')); S=int(os.environ.get('SC','3')); cw=16*S+4
        img=Image.new('RGB',(cols*cw,((len(ids)+cols-1)//cols)*(cw+10)),(40,40,40)); dr=ImageDraw.Draw(img)
        for k,m in enumerate(ids):
            t=Image.new('RGB',(16,16),(255,0,255)); at=draw_meta(t,0,0,d,a,b,rgb,m)
            X=(k%cols)*cw; Y=(k//cols)*(cw+10)
            img.paste(t.resize((16*S,16*S),Image.NEAREST),(X,Y+10))
            dr.text((X,Y),'%d %s%x'%(m,'NCS?'[(at>>29)&3],at&0x1ff),fill=(255,255,0))
        img.save(out)
if __name__=='__main__': main()

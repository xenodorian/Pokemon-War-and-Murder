import sys,struct
sys.path.insert(0,'/home/claude/work/tools')
import maprender
from PIL import ImageDraw
d=open(sys.argv[1],'rb').read(); g,n=int(sys.argv[2]),int(sys.argv[3])
im=maprender.render(d,g,n).convert('RGB')
dr=ImageDraw.Draw(im)
r32=lambda o: struct.unpack('<I',d[o:o+4])[0]
gp=r32(0x3526A8+4*g)-0x08000000; h=r32(gp+4*n)-0x08000000; lay=r32(h)-0x08000000
w,hh=r32(lay),r32(lay+4)
for x in range(0,w,5):
    dr.line([(x*16,0),(x*16,hh*16)],fill=(255,255,255)); dr.text((x*16+2,2),str(x),fill=(255,255,0))
for y in range(0,hh,5):
    dr.line([(0,y*16),(w*16,y*16)],fill=(255,255,255)); dr.text((2,y*16+2),str(y),fill=(255,255,0))
ev=r32(h+4)-0x08000000
po=r32(ev+4)-0x08000000
for i in range(d[ev]):
    x,y=struct.unpack('<hh',d[po+24*i+4:po+24*i+8]); dr.rectangle([x*16+3,y*16+3,x*16+12,y*16+12],outline=(255,0,0))
wp=r32(ev+8)-0x08000000
for i in range(d[ev+1]):
    x,y=struct.unpack('<hh',d[wp+8*i:wp+8*i+4]); dr.rectangle([x*16+2,y*16+2,x*16+13,y*16+13],outline=(0,255,255))
print(w,hh)
im.save(sys.argv[4])

import sys
sys.path.insert(0,'/home/claude/work/tools')
import maprender
from PIL import ImageDraw
d=open(sys.argv[1],'rb').read(); g,n,x0,x1,y0,y1=map(int,sys.argv[2:8])
im=maprender.render(d,g,n).convert('RGB').crop((x0*16,y0*16,x1*16,y1*16)); dr=ImageDraw.Draw(im)
for x in range(x0,x1):
    dr.line([((x-x0)*16,0),((x-x0)*16,im.height)],fill=(255,255,255)); dr.text(((x-x0)*16+2,1),str(x),fill=(255,255,0))
for y in range(y0,y1):
    dr.line([(0,(y-y0)*16),(im.width,(y-y0)*16)],fill=(255,255,255)); dr.text((1,(y-y0)*16+2),str(y),fill=(255,255,0))
im=im.resize((im.width*2,im.height*2),0); im.save(sys.argv[8])

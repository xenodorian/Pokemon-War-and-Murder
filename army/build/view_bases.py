import sys,struct
sys.path.insert(0,'/home/claude/work/tools')
import maprender
from PIL import Image,ImageDraw
d=open(sys.argv[1],'rb').read()
exec(open('/home/claude/work/tools/army.py').read().split("# ----------------------------------------------------------------------------------------------- exterior sites")[1].split("def carve_exterior")[0].replace("HOUSE=(32,8,5,4)","HOUSE=(32,8,5,4)\n",1)) if False else None
import army
EXT=army.EXT
ims=[]
for name,n in [('PALLET',0),('VIRIDIAN',1),('PEWTER',2),('CERULEAN',3),('VERMILION',5),('LAVENDER',4),('CELADON',6),('SAFFRON',10),('FUCHSIA',7),('CINNABAR',8)]:
    im=maprender.render(d,3,n).convert('RGB'); dr=ImageDraw.Draw(im)
    e=EXT.get(name) or dict(bx=33,by=2,guards=[(33,6,10),(38,6,9)],sign=(39,6))
    for x,y,k in e['guards']: dr.rectangle([x*16+2,y*16+2,x*16+13,y*16+13],outline=(255,0,0),width=2)
    x,y=e['sign']; dr.rectangle([x*16+2,y*16+4,x*16+13,y*16+13],outline=(255,255,0),width=2)
    bx,by=e['bx'],e['by']; W,H=im.size
    cx0=max(0,bx-8); cx1=min(W//16,bx+14); cy0=max(0,by-5); cy1=min(H//16,by+11)
    cr=im.crop((cx0*16,cy0*16,cx1*16,cy1*16)); ImageDraw.Draw(cr).text((3,2),name,fill=(255,255,0)); ims.append(cr)
cw=max(i.width for i in ims); 
rows=[ims[i:i+2] for i in range(0,10,2)]
sheet=Image.new('RGB',(cw*2+8,sum(max(i.height for i in rw)+4 for rw in rows)),(30,30,30)); y=0
for rw in rows:
    x=0
    for i in rw: sheet.paste(i,(x,y)); x+=cw+8
    y+=max(i.height for i in rw)+4
sheet.save(sys.argv[2]); print(sheet.size)

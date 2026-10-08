import sys,struct
sys.path.insert(0,'/home/claude/work/tools')
import maprender
from PIL import Image,ImageDraw
d=open(sys.argv[1],'rb').read()
r32=lambda o: struct.unpack('<I',d[o:o+4])[0]
names={69:'3 PEWTER',70:'1 PALLET',71:'2 VIRIDIAN',72:'4 CERULEAN',73:'5 VERMILION',74:'6 LAVENDER',75:'7 CELADON',76:'8 SAFFRON',77:'9 FUCHSIA',78:'10 CINNABAR'}
ims=[]
for num in sorted(names,key=lambda k:int(names[k].split()[0])):
    im=maprender.render(d,2,num).convert('RGB'); dr=ImageDraw.Draw(im)
    gp=r32(0x3526A8+8)-0x08000000; h=r32(gp+4*num)-0x08000000; ev=r32(h+4)-0x08000000
    po=r32(ev+4)-0x08000000
    for i in range(d[ev]):
        x,y=struct.unpack('<hh',d[po+24*i+4:po+24*i+8]); gfx=d[po+24*i+1]
        col=(255,0,0) if gfx==0x9f else (255,255,0)
        dr.rectangle([x*16+1,y*16+1,x*16+14,y*16+14],outline=col,width=2)
    wp=r32(ev+8)-0x08000000
    for i in range(d[ev+1]):
        x,y=struct.unpack('<hh',d[wp+8*i:wp+8*i+4]); dr.rectangle([x*16,y*16,x*16+15,y*16+15],outline=(0,255,255),width=2)
    dr.rectangle([0,0,110,12],fill=(0,0,0)); dr.text((2,1),'BASE '+names[num],fill=(255,255,255)); ims.append(im)
W=max(i.width for i in ims); 
rows=[ims[i:i+2] for i in range(0,10,2)]
sheet=Image.new('RGB',(W*2+8,sum(max(i.height for i in rw)+4 for rw in rows)),(30,30,30)); y=0
for rw in rows:
    x=0
    for i in rw: sheet.paste(i,(x,y)); x+=W+8
    y+=max(i.height for i in rw)+4
sheet.save(sys.argv[2]); print(sheet.size)

import sys,json
sys.path.insert(0,'/home/claude/work/tools')
import maprender
from PIL import Image,ImageDraw
d=open(sys.argv[1],'rb').read(); specs=json.loads(sys.argv[3])
ims=[]
cache={}
for name,g,n,x,y,w,h in specs:
    if (g,n) not in cache: cache[(g,n)]=maprender.render(d,g,n).convert('RGB')
    im=cache[(g,n)]
    x0,y0=max(0,x-1),max(0,y-1); cr=im.crop((x0*16,y0*16,(x+w+1)*16,(y+h+1)*16)).copy()
    dr=ImageDraw.Draw(cr)
    dr.rectangle([(x-x0)*16,(y-y0)*16,(x-x0+w)*16-1,(y-y0+h)*16-1],outline=(255,0,255))
    cr=cr.resize((cr.width*2,cr.height*2),0); dr=ImageDraw.Draw(cr); dr.text((2,2),'%s %d,%d %dx%d'%(name,x,y,w,h),fill=(255,255,0))
    ims.append(cr)
W=sum(i.width for i in ims)+10*len(ims); H=max(i.height for i in ims)
sheet=Image.new('RGB',(W,H),(30,30,30)); xx=0
for i in ims: sheet.paste(i,(xx,0)); xx+=i.width+10
sheet.save(sys.argv[2])

import sys,struct,json
sys.path.insert(0,'/home/claude/work/tools')
from inc import *
import army_sites as A, maprender, reach
from PIL import Image,ImageDraw
r=Rom('/home/claude/work/out/c16.gba')
T=3
SPECS=[
 dict(name='PALLET',n=0,ext=14,src=(5,3,5,5,1,4),bx=28,by=12,yg=17,carve=[(22,17,36,18)],clear=[(24,11,35,16)],ground=(20,18),G=[(27,17,0),(33,17,1)],sign=(34,17),num=1),
 dict(name='VIRIDIAN',n=1,ext=8,src=(24,8,5,4,1,3),bx=45,by=16,yg=20,carve=[(42,20,52,21)],clear=[(42,15,52,19)],ground=(36,14),G=[(44,20,0),(50,20,1)],sign=(51,20),num=2),
 dict(name='CERULEAN',n=3,ext=14,src=(8,8,7,4,2,3),bx=50,by=14,yg=18,carve=[],clear=[(48,13,59,17)],ground=(39,14),G=[(49,18,0),(57,18,1)],sign=(58,18),num=4),
 dict(name='VERMILION',n=5,ext=12,src=(33,9,5,4,2,3),bx=50,by=14,yg=18,carve=[],clear=[(48,13,58,17)],ground=(35,15),G=[(49,18,0),(55,18,1)],sign=(56,18),num=5),
 dict(name='LAVENDER',n=4,ext=14,src=(9,8,5,4,2,3),bx=27,by=9,yg=13,carve=[(22,13,34,14)],clear=[(24,8,34,12)],ground=(20,13),G=[(26,13,0),(32,13,1)],sign=(33,13),num=6),
 dict(name='CELADON',n=6,ext=12,src=(36,25,4,5,1,4),bx=62,by=7,yg=12,carve=[],clear=[(60,6,69,11)],ground=(46,16),G=[(61,12,0),(66,12,1)],sign=(67,12),num=7),
 dict(name='SAFFRON',n=10,ext=0,src=(21,11,4,4,1,3),bx=10,by=21,yg=25,carve=[],clear=[(9,20,13,23)],ground=(12,25),G=[(9,25,0),(11,28,2)],sign=(13,25),num=8),
 dict(name='FUCHSIA',n=7,ext=0,src=(39,28,5,5,2,4),bx=35,by=12,yg=17,carve=[],clear=[],ground=(34,17),G=[(34,17,0),(40,17,1)],sign=(33,17),num=9),
]
out=[]
def apply(s):
    n=s['n']
    if s['ext']: A.extend_right(r,T,n,s['ext'])
    gx,gy=s['ground']; gv=A.get_block(r,T,n,gx,gy)
    for (x0,y0,x1,y1) in s['carve']+s['clear']: A.fill(r,T,n,x0,y0,x1,y1,gv)
    sx,sy,sw,sh,dx,dy=s['src']; A.copy_rect(r,T,n,sx,sy,sw,sh,s['bx'],s['by'])
for s in SPECS: apply(s)
# Cinnabar
n=8; A.insert_rows(r,T,n,15,10,[13,14])
gv=A.get_block(r,T,n,10,14)
A.copy_rect(r,T,n,5,0,7,4,8,16); A.copy_rect(r,T,n,7,4,3,1,10,20)
SPEC_C=dict(name='CINNABAR',n=8,bx=8,by=16,yg=21,G=[(7,21,0),(15,21,1)],sign=(16,21),num=10,door=(11,19))
d=bytes(r.b)
def mark(im,s,off=(0,0)):
    dr=ImageDraw.Draw(im)
    for x,y,k in s['G']:
        dr.rectangle([x*16+2,y*16+2,x*16+13,y*16+13],outline=(255,0,0),width=2)
        dr.text((x*16+4,y*16+2),'G',fill=(255,255,255))
    x,y=s['sign']; dr.rectangle([x*16+2,y*16+4,x*16+13,y*16+13],outline=(255,255,0),width=2)
    if 'door' in s: x,y=s['door']
    else: x,y=s['bx']+s['src'][4],s['by']+s['src'][5]
    dr.rectangle([x*16,y*16,x*16+15,y*16+15],outline=(0,255,255),width=2)
crops=[]
for s in SPECS+[SPEC_C]:
    g,n=3,s['n']; im=maprender.render(d,g,n).convert('RGB'); mark(im,s)
    W,H=im.size
    cx0=max(0,min(W//16-1,s['bx']-7)); cx1=min(W//16,s['bx']+14); cy0=max(0,s['by']-5); cy1=min(H//16,s['yg']+6)
    cr=im.crop((cx0*16,cy0*16,cx1*16,cy1*16)); dr=ImageDraw.Draw(cr); dr.rectangle([0,0,150,12],fill=(0,0,0)); dr.text((2,1),'#%d %s'%(s['num'],s['name']),fill=(255,255,0))
    crops.append(cr)
# Pewter existing
pw=maprender.render(open('/home/claude/work/out/c16.gba','rb').read(),3,2).convert('RGB')
cr=pw.crop((26*16,0,46*16,12*16)); ImageDraw.Draw(cr).text((2,1),'#3 PEWTER (built)',fill=(255,255,0)); crops.insert(2,cr)
colw=max(c.width for c in crops); 
rows=[]
for i in range(0,len(crops),2): rows.append(crops[i:i+2])
Wd=colw*2+10; Hd=sum(max(c.height for c in rw)+6 for rw in rows)
sheet=Image.new('RGB',(Wd,Hd),(30,30,30)); y=0
for rw in rows:
    x=0
    for c in rw: sheet.paste(c,(x,y)); x+=colw+10
    y+=max(c.height for c in rw)+6
sheet.save('/home/claude/work/out/mock_ext.png'); print(sheet.size)

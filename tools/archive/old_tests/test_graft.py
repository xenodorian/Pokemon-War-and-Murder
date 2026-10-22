import sys,struct
sys.path.insert(0,'/home/claude/work/tools')
from inc import *
import army_tiles as AT, army_sites as A, maprender
from PIL import Image
r=Rom('/home/claude/work/out/c16.gba')
src=AT.Tileset(r,3,2)
house=AT.House(src,(32,8,5,4))
print('house palette colours',len(house.palette),'pairs',len(house.pairs))
res=[]
for n,name,(px,py) in [(2,'Pewter',(33,2)),(1,'Viridian',(14,20)),(3,'Cerulean',(2,30)),(10,'Saffron',(10,21)),(8,'Cinnabar',(10,16))]:
    ts=AT.Tileset(r,3,n); slot=ts.free_slot(); print(name,'free slot',slot,'nreal',ts.nreal,'used',sorted(ts.slots_used()))
    blocks=house.graft(ts,slot)
    for j,row in enumerate(blocks):
        for i,v in enumerate(row): A.set_block(r,3,n,px+i,py+j,v)
    if name=='Pewter': AT.recolor_brown(ts,[8,9])
    ts.commit()
    d=bytes(r.b); im=maprender.render(d,3,n).convert('RGB')
    cr=im.crop((max(0,px-6)*16,max(0,py-4)*16,(px+12)*16,(py+9)*16)); res.append((name,cr))
W=sum(c.width for _,c in res[:3]); 
sheet=Image.new('RGB',(max(sum(c.width for _,c in res[:3]),sum(c.width for _,c in res[3:])),max(c.height for _,c in res)*2+4),(30,30,30))
x=0
for _,c in res[:3]: sheet.paste(c,(x,0)); x+=c.width
x=0
for _,c in res[3:]: sheet.paste(c,(x,max(cc.height for _,cc in res)+4)); x+=c.width
sheet.save('out/test_graft.png'); print(sheet.size)
im=maprender.render(bytes(r.b),3,2).convert('RGB'); im.save('out/test_pewter_full.png')

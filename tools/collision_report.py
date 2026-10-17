"""Render the collision layer of the custom/patched maps with decals, objects, warps and coord triggers, and flag outlier tiles (a metatile whose collision bit
differs from what the same metatile has in >=90% of its other uses with the same tileset pair). Read only.
usage: collision_report.py ROM.gba OUTPREFIX     -> OUTPREFIX_<name>.png and OUTPREFIX_outliers.txt"""
import sys,struct,os,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(1,'/home/claude/work/tools')
import leg1
from PIL import Image,ImageDraw
from collision_diff import maps as allmaps
SETS={'cities_a':[(3,0),(3,1),(3,2),(3,3)],'cities_b':[(3,4),(3,5),(3,6),(3,7)],'misc':[(3,8),(3,10),(3,18),(3,66),(4,0),(1,1),(1,2),(1,3)],
      'afterlife_camp':[(2,68),(2,80),(2,79),(2,81)],'bases_a':[(2,60),(2,64),(2,69),(2,70),(2,71),(2,72)],'bases_b':[(2,73),(2,74),(2,75),(2,76),(2,77),(2,78)]}
NAMES={(3,0):'Pallet',(3,1):'Viridian',(3,2):'Pewter',(3,3):'Cerulean',(3,4):'Lavender',(3,5):'Vermilion',(3,6):'Celadon',(3,7):'Fuchsia',(3,8):'Cinnabar?',(3,10):'(3,10)',(3,18):'(3,18)',(3,66):'house copy',(4,0):'player house',(1,1):'Mt Moon 1',(1,2):'Mt Moon 2',(1,3):'Mt Moon B2F',(2,68):'Hell',(2,80):'Heaven',(2,79):'Final camp',(2,81):'(2,81)'}
DECAL={152:(220,0,0),153:(150,0,150),161:(255,120,0),155:(0,120,255)}
def main(rom,pre):
    d=open(rom,'rb').read(); r32=lambda o:struct.unpack('<I',d[o:o+4])[0]
    M=allmaps(rom)
    stats=collections.defaultdict(lambda:[0,0])
    for k,(w,h,m,t1,t2) in M.items():
        for v in m: stats[(t1,t2,v&0x3ff)][(v>>10)&3!=0]+=1
    out=open(pre+'_outliers.txt','w')
    for sname,keys in SETS.items():
        ims=[]
        for k in keys:
            if k not in M: continue
            w,h,m,t1,t2=M[k]
            gp=r32(leg1.GROUPS+4*k[0])-0x8000000; hd=r32(gp+4*k[1])-0x8000000
            ev=r32(hd+4)-0x8000000; no,nw,nc=d[ev],d[ev+1],d[ev+2]; po=r32(ev+4)-0x8000000; wp=r32(ev+8)-0x8000000; cp=r32(ev+12)-0x8000000
            S=8; im=Image.new('RGB',(w*S,h*S+12),(20,20,20)); dr=ImageDraw.Draw(im)
            out_n=[]
            for y in range(h):
                for x in range(w):
                    v=m[y*w+x]; c=(v>>10)&3; col=(40,40,40) if c else (200,220,200)
                    dr.rectangle([x*S,12+y*S,x*S+S-2,12+y*S+S-2],fill=col)
                    st=stats[(t1,t2,v&0x3ff)]; tot=sum(st)
                    if tot>=15:
                        dom=st[1]>st[0]; share=max(st)/tot
                        if share>=0.9 and (c!=0)!=dom:
                            dr.rectangle([x*S,12+y*S,x*S+S-2,12+y*S+S-2],outline=(255,0,255)); out_n.append((x,y,'blocked' if c else 'walkable',v&0x3ff,st))
            for i in range(nc):
                x,y=struct.unpack('<HH',d[cp+16*i:cp+16*i+4]); dr.rectangle([x*S+2,12+y*S+2,x*S+S-4,12+y*S+S-4],fill=(230,200,0))
            for i in range(nw):
                x,y=struct.unpack('<HH',d[wp+8*i:wp+8*i+4]); dr.rectangle([x*S+1,12+y*S+1,x*S+S-3,12+y*S+S-3],fill=(0,200,220))
            for i in range(no):
                o=po+24*i; x,y=struct.unpack('<hh',d[o+4:o+8]); g=d[o+1]
                dr.ellipse([x*S+1,12+y*S+1,x*S+S-3,12+y*S+S-3],fill=DECAL.get(g,(0,160,0)))
                if g in DECAL and (m[y*w+x]>>10)&3: out_n.append((x,y,'DECAL ON BLOCKED TILE',g,0))
            dr.text((2,0),f'{k} {NAMES.get(k,"")} {w}x{h}  dark=blocked  yellow=trigger cyan=warp green=npc red/purple/blue=decal magenta=outlier',fill=(255,255,255))
            ims.append(im)
            out.write(f'{k} {NAMES.get(k,"")}: {len(out_n)} outlier tiles\n')
            for o in out_n: out.write(f'   {o}\n')
        if not ims: continue
        W=max(i.width for i in ims); cols=2 if sname not in('afterlife_camp',) else 2
        rows=[ims[i:i+cols] for i in range(0,len(ims),cols)]
        H=sum(max(i.height for i in r) for r in rows); Wd=sum(i.width for i in rows[0]) if rows else 0
        Wd=max(sum(i.width for i in r) for r in rows)
        sh=Image.new('RGB',(Wd+4*cols,H+4*len(rows)),(0,0,0)); y=0
        for r in rows:
            x=0
            for i in r: sh.paste(i,(x,y)); x+=i.width+4
            y+=max(i.height for i in r)+4
        sh.save(f'{pre}_{sname}.png'); print(sname,sh.size)
    out.close(); print(open(pre+'_outliers.txt').read()[:3000])
main(sys.argv[1],sys.argv[2])

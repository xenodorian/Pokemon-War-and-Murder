import sys,struct
sys.path.insert(0,'/home/claude/work/tools')
import reach,maprender
d=open(sys.argv[1],'rb').read()
W_,H_=int(sys.argv[2]) if len(sys.argv)>2 else 7,int(sys.argv[3]) if len(sys.argv)>3 else 8
TOWNS=[(3,0,'Pallet'),(3,1,'Viridian'),(3,2,'Pewter'),(3,3,'Cerulean'),(3,4,'Lavender'),(3,5,'Vermilion'),(3,6,'Celadon'),(3,7,'Fuchsia'),(3,8,'Cinnabar'),(3,10,'Saffron')]
def grassmap(g,n):
    im=maprender.render(d,g,n).convert('RGB'); w,h,grid,beh,objs=reach.load(d,g,n)
    gm=[[False]*w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            v=grid[y][x]
            if (v>>10)&3 or beh(v&0x3ff)!=0 or (x,y) in objs: continue
            px=im.crop((x*16,y*16,x*16+16,y*16+16)).resize((1,1),1).getpixel((0,0))
            if px[1]>px[0]+10 and px[1]>px[2]+10: gm[y][x]=True
    return w,h,gm
def pts_of(g,n):
    r32=lambda o: struct.unpack('<I',d[o:o+4])[0]
    gp=r32(0x3526A8+4*g)-0x08000000; hh=r32(gp+4*n)-0x08000000; ev=r32(hh+4)-0x08000000
    wp=r32(ev+8)-0x08000000; bp=r32(ev+16)-0x08000000
    return [struct.unpack('<hh',d[wp+8*i:wp+8*i+4]) for i in range(d[ev+1])]+[struct.unpack('<HH',d[bp+12*i:bp+12*i+4]) for i in range(d[ev+3])]
if __name__=='__main__':
    for g,n,name in TOWNS:
        w,h,gm=grassmap(g,n); pts=pts_of(g,n); c=[]
        for y in range(1,h-H_):
            for x in range(1,w-W_):
                if all(gm[y+j][x+i] for i in range(W_) for j in range(H_)) and not any(x-1<=px<x+W_+1 and y-1<=py<y+H_+1 for px,py in pts): c.append((x,y))
        picks=[]
        for x,y in c:
            if all(abs(x-a)>=W_ or abs(y-b)>=H_ for a,b in picks): picks.append((x,y))
        print(name,(w,h),picks[:12],'of',len(c))

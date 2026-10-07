# usage: mapinfo.py rom group num  -> prints block grid (. walkable, # blocked), objects, warps, coords, signs
import sys,struct
d=open(sys.argv[1],'rb').read(); g,n=int(sys.argv[2]),int(sys.argv[3])
def r32(o):return struct.unpack('<I',d[o:o+4])[0]
G=0x3526A8
gp=r32(G+4*g)-0x08000000; h=r32(gp+4*n)-0x08000000
lay=r32(h)-0x08000000; ev=r32(h+4)-0x08000000
w,hh=r32(lay),r32(lay+4); mp=r32(lay+12)-0x08000000
print('map',g,n,w,'x',hh,'mapsec',hex(d[h+20]),'events',[d[ev+i] for i in range(4)])
no,nw,nc,nb=d[ev:ev+4]; po,wp,cp,bp=[r32(ev+4+4*i)-0x08000000 for i in range(4)]
objs={}
for i in range(no):
    t=po+24*i; x,y=struct.unpack('<hh',d[t+4:t+8]); objs[(x,y)]=('O%d'%d[t],d[t+1])
wps={}
for i in range(nw):
    x,y=struct.unpack('<hh',d[wp+8*i:wp+8*i+4]); wps[(x,y)]=('W',d[wp+8*i+6],d[wp+8*i+7])
sg={}
for i in range(nb):
    x,y=struct.unpack('<HH',d[bp+12*i:bp+12*i+4]); sg[(x,y)]='S'
print('objects',[(k,v) for k,v in objs.items()]); print('warps',wps)
print('    '+''.join('%3d'%x for x in range(w)))
for y in range(hh):
    row=''
    for x in range(w):
        b=struct.unpack('<H',d[mp+2*(y*w+x):mp+2*(y*w+x)+2])[0]
        c='#' if b&0xc00 else '.'
        if (x,y) in objs: c='O'
        elif (x,y) in wps: c='W'
        elif (x,y) in sg: c='S'
        row+='  '+c
    print('%3d '%y+row)

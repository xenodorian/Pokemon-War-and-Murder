import sys,struct
d=open(sys.argv[1],'rb').read(); g,n=int(sys.argv[2]),int(sys.argv[3])
r32=lambda o: struct.unpack('<I',d[o:o+4])[0]
gp=r32(0x3526A8+4*g)-0x08000000; h=r32(gp+4*n)-0x08000000; lay=r32(h)-0x08000000
print('layout',r32(lay),r32(lay+4),'mapsec',d[h+20],'conn ptr',hex(r32(h+12)))
c=r32(h+12)-0x08000000
if c>0:
    cnt=r32(c); cp=r32(c+4)-0x08000000
    for i in range(cnt):
        t,off,mg,mn=struct.unpack('<IIBB',d[cp+12*i:cp+12*i+10]); print(' conn',['?','down','up','left','right','dive','emerge'][t] if t<7 else t,'offset',struct.unpack('<i',struct.pack('<I',off))[0],'->',mg,mn)
ev=r32(h+4)-0x08000000
po=r32(ev+4)-0x08000000
for i in range(d[ev]):
    o=po+24*i; print(' obj',d[o],'gfx',d[o+1],struct.unpack('<hh',d[o+4:o+8]),'trainer',struct.unpack('<H',d[o+12:o+14])[0])
wp=r32(ev+8)-0x08000000
for i in range(d[ev+1]):
    print(' warp',i,struct.unpack('<hhBBBB',d[wp+8*i:wp+8*i+8]))
bp=r32(ev+16)-0x08000000
for i in range(d[ev+3]):
    print(' bg',struct.unpack('<HHBBHI',d[bp+12*i:bp+12*i+12])[:3])

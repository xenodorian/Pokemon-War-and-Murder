# usage: mil_preview.py in.gba out.gba group num x y [recolor]   (test ROM: QUESTS warps there; secondary tileset of that map recolored olive)
import sys,struct,colorsys
sys.path.insert(0,'/home/claude/work/tools')
sys.path.insert(0,'/home/claude/work/tools')
d=bytearray(open(sys.argv[1],'rb').read()); g,n,x,y=[int(v) for v in sys.argv[3:7]]; rec=len(sys.argv)>7 and sys.argv[7]=='1'
def r32(o): return struct.unpack('<I',d[o:o+4])[0]
def mil(c):
    r,g_,b=[v/31 for v in c]
    y=0.30*r+0.59*g_+0.11*b                      # luminance, so every colour becomes a grey of the same brightness
    r2,g2,b2=y*0.98,y*1.0,y*1.03                 # a hint of cool steel
    return tuple(max(0,min(31,int(round(t*31)))) for t in (r2,g2,b2))
GROUPS=0x3526A8
gp=r32(GROUPS+4*g)-0x08000000; hdr=r32(gp+4*n)-0x08000000; lay=r32(hdr)-0x08000000
ts=r32(lay+20)-0x08000000; pal=r32(ts+8)-0x08000000
if rec:
    for p in range(6,13):
        for i in range(1,16):
            o=pal+32*p+2*i; v=struct.unpack('<H',d[o:o+2])[0]
            c=(v&31,(v>>5)&31,(v>>10)&31); r,g2,b=mil(c); d[o:o+2]=struct.pack('<H',r|(g2<<5)|(b<<10))
end=max(i for i in range(0xA00000,len(d)) if d[i]!=0xff)+1; a=(end+3)&~3
sc=bytes([0x39,g,n,0xff])+struct.pack('<HH',x,y)+bytes([0x27,0x02]); d[a:a+len(sc)]=sc
d[0xa01a38:0xa01a3c]=struct.pack('<I',0x08000000+a); open(sys.argv[2],'wb').write(d)

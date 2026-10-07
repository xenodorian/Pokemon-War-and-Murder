# usage: dbgwarp.py in.gba out.gba group num x y   -> QUESTS menu entry warps there (test ROM only)
import sys,struct
d=bytearray(open(sys.argv[1],'rb').read()); g,n,x,y=[int(v) for v in sys.argv[3:7]]
end=max(i for i in range(0xA00000,len(d)) if d[i]!=0xff)+1; a=(end+3)&~3
sc=bytes([0x39,g,n,0xff])+struct.pack('<HH',x,y)+bytes([0x27,0x02]); d[a:a+len(sc)]=sc
d[0xa01a38:0xa01a3c]=struct.pack('<I',0x08000000+a); open(sys.argv[2],'wb').write(d)

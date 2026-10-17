"""Parse /tmp/viri_ram.txt (gSprites dumps from VIRI_RAM=frame:202063c:4352) and print every in-use sprite: images ptr, size, subpriority, oam priority, screen pos. TEST ONLY.
usage: sprite_ram_report.py [file]   exit 1 if a decal (splatter 0x8f1e6a0 or feather 0x8eb90d4 image table) is not at subpriority 0xFF"""
import sys,re,struct
DECAL={0x8f1e6a0:'splatter',0x8eb90d4:'feather'}
bad=0
for ln in open(sys.argv[1] if len(sys.argv)>1 else '/tmp/viri_ram.txt',errors='ignore'):
    m=re.match(r'RAM f(\d+) ([0-9a-f]+):(.*)',ln)
    if not m: continue
    d=bytes(int(v,16) for v in m.group(3).split())
    print('frame',m.group(1))
    for i in range(len(d)//0x44):
        s=d[i*0x44:(i+1)*0x44]
        if not s[0x3E]&1 or not struct.unpack('<I',s[0xC:0x10])[0]: continue
        a0,a1,a2=struct.unpack('<HHH',s[0:6]); im=struct.unpack('<I',s[0xC:0x10])[0]
        x,y=struct.unpack('<hh',s[0x20:0x24]); x2,y2=struct.unpack('<hh',s[0x24:0x28])
        kind=DECAL.get(im,'')
        pr=(a2>>10)&3; sub=s[0x43]
        if kind or True:
            if kind: print(f'  sprite {i:2d} {kind:9s} img {im:08x} subprio {sub:#04x} oam prio {pr} pos {x+x2},{y+y2}',end='')
            else: print(f'  sprite {i:2d} object    img {im:08x} subprio {sub:#04x} oam prio {pr} pos {x+x2},{y+y2}',end='')
            if kind and sub!=0xFF: print('   <-- NOT 0xFF'); bad=1
            else: print()
sys.exit(bad)

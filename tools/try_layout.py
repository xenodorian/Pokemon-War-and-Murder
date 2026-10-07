import sys,struct,subprocess
src='out/Pokemon Outlaw Quest Log (Mimikyu).gba'
d0=open(src,'rb').read()
def r32(d,o):return struct.unpack('<I',d[o:o+4])[0]
G=0x3526A8
def run(layout,tag):
    d=bytearray(d0)
    g1=r32(d,G+4)-0x08000000
    h=r32(d,g1+4*89)-0x08000000
    d[h:h+4]=struct.pack('<I',0x08000000+layout)
    w,hh=r32(d,layout),r32(d,layout+4)
    open('out/_t.gba','wb').write(d)
    subprocess.run(['python3','tools/dbgwarp.py','out/_t.gba','out/_t2.gba','1','89',str(w//2),str(hh//2)],check=True)
    subprocess.run(['./tools/shot_after_warp.sh','out/_t2.gba','/tmp/claude-0/o_'+tag],capture_output=True)
if __name__=='__main__':
    for a in sys.argv[1:]: run(int(a,16),a)

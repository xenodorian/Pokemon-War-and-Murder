import sys,os,struct,subprocess
sys.path.insert(0,'/home/claude/work/tools'); os.chdir('/home/claude/work')
import gun_t3 as t
ROM=os.environ.get('WALK_ROM','/home/user/Pokemon-Outlaw-Mod/roms/Pokemon War and Murder.gba')
KEY={'U':'40','D':'80','L':'20','R':'10'}
def test(name,g,n,sx,sy,k,t0=900,hold=64):
    t.mkw(ROM,'out/wt_%s.gba'%name,g,n,sx,sy,[])
    L=[]
    for f,kk in [(200,'1'),(440,'8'),(500,'40'),(540,'40'),(580,'40'),(640,'1')]: L+=[f"{f} {kk}",f"{f+4} 0"]
    L+=[f"{t0} {KEY[k]}",f"{t0+hold} 0"]
    L+=["ram %d 3005008 4"%(t0-6),"ram %d 2000000 262144"%(t0-5),"ram %d 3005008 4"%(t0+hold+25),"ram %d 2000000 262144"%(t0+hold+26),"end %d"%(t0+hold+40)]
    open('/tmp/claude-0/wt.txt','w').write('\n'.join(L))
    r=subprocess.run(['./tools/harness_new','out/wt_%s.gba'%name,'/tmp/claude-0/wt.txt','shots/wt_'+name],env=dict(os.environ,LOADSTATE='out/user_new.raw'),capture_output=True,text=True,timeout=600)
    rams=[l.split() for l in (r.stdout+r.stderr).splitlines() if l.startswith('RAM')]
    def pos(i):
        sb=struct.unpack('<I',bytes(int(x,16) for x in rams[i][3:]))[0]; ew=bytes(int(x,16) for x in rams[i+1][3:]); off=sb-0x2000000
        return struct.unpack('<hh',ew[off:off+4])
    return pos(0),pos(2)
CASES=[
 # name, map, start, key, what we expect
 ('ctrl_open_grass',(3,3),(50,19),'R','moves right (control: movement works)'),
 ('cer_fence_h',(3,3),(59,17),'U','blocked by the fence at (59,16)'),
 ('cer_fence_v',(3,3),(56,14),'R','blocked by the fence pole at (57,14)'),
 ('cer_fence_corner',(3,3),(57,17),'U','blocked by the corner at (57,16)'),
 ('cer_fence_connected',(3,3),(46,18),'U','blocked by the connected fence at (46,17)'),
 ('fuc_former_wall',(3,7),(36,20),'U','free: walks through the old invisible wall at (36,19)'),
 ('lav_fence_v',(3,4),(14,9),'R','blocked by the vertical fence at (15,9)'),
 ('lav_fence_v_r',(3,4),(22,9),'L','blocked by the vertical fence at (21,9)'),
 ('lav_rock',(3,4),(25,7),'U','blocked by the rock face at (25,6)'),
 ('verm_trees',(3,5),(50,13),'U','blocked by the trees at row 11 after one step'),
 ('base_pot',(2,69),(17,5),'U','blocked by the pot at (17,2)'),
 ('church_pot',(2,67),(1,5),'U','blocked by the pot at (1,2)'),
]
if __name__=='__main__':
    sel=sys.argv[1:] or [c[0] for c in CASES]
    for name,(g,n),(sx,sy),k,exp in CASES:
        if name not in sel: continue
        try:
            a,b=test(name,g,n,sx,sy,k)
            print('%-18s map (%d,%d) start (%d,%d) press %s -> before %s after %s | expect: %s'%(name,g,n,sx,sy,k,a,b,exp))
        except Exception as e: print(name,'error',repr(e)[:200])

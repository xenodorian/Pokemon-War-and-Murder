"""Visual audit of every decal object (splatter 0x98, body 0x99, feather 155, army splatter alias 0xA1) on a ROM copy, emulator only.
For each decal: native screenshot in place (player two tiles away), standing on it, and walking over it; crops 96x64 at 3x -> shots/splatter_crops/*.png and shots/splatter_all_sheet*.png.
usage: splatter_sheet.py [ROM.gba]   (builds a TEST ROM with the final apply_all chain, TEST_BATTLE + a house door warp that is patched per decal)"""
import sys,os,subprocess,glob,struct,shutil
from PIL import Image,ImageDraw
ROOT='/home/claude/work'; os.chdir(ROOT); sys.path.insert(0,'tools')
from collision_diff import maps
M=None
BASE_ROM='/tmp/splat_test_base.gba'
# (name, map, x, y, gfxkind, pokes, flags, clear)
B='0x4f8'
D=[('viridian_splat_a',(3,1),24,33,'splat','','0x848',''),('viridian_splat_b',(3,1),23,33,'splat','','0x848',''),
 ('viridian_body',(3,1),24,20,'body','','',B),('viridian_feather',(3,1),25,20,'feather','','',B),
 ('pallet_body',(3,0),11,12,'body','','',B),('pallet_feather',(3,0),12,12,'feather','','',B),
 ('pewter_site_splat',(3,2),33,15,'splat','0x1130=2','',''),('pewter_body',(3,2),24,10,'body','','',B),('pewter_feather',(3,2),23,10,'feather','','',B),
 ('cerulean_siteA_splat',(3,3),25,22,'splat','0x112A=2','',''),('cerulean_body',(3,3),22,14,'body','','',B),('cerulean_feather',(3,3),23,14,'feather','','',B),
 ('lavender_site_splat',(3,4),27,15,'splat','0x1132=2','','')]
for i,(x,y) in enumerate([(17,8),(18,8),(19,8),(17,9),(19,9),(17,10),(18,10),(19,10)]): D.append((f'lavender_body{i+1}',(3,4),x,y,'body','0x11E4=1','',''))
D+=[('vermilion_siteB_splat',(3,5),34,19,'splat','0x112C=2','',''),('vermilion_body',(3,5),24,20,'body','','',B),('vermilion_feather',(3,5),25,20,'feather','','',B),
 ('celadon_site_splat',(3,6),21,15,'splat','0x1134=2','',''),('fuchsia_site_splat',(3,7),26,24,'splat','0x1136=2','',''),
 ('camp_sniper_splat',(2,79),15,13,'splat','0x1138=2','',''),
 ('ARMY_ALIAS_0xA1_on_pewter_site',(3,2),33,15,'army_splat','0x1130=2','','')]
def main():
    global M
    M=maps('/tmp/d1.gba' if not len(sys.argv)>1 else sys.argv[1])
    env=dict(os.environ,TEST_BATTLE='1',TEST_WARP='3,0,5,5')
    subprocess.run(['sh','tools/apply_all.sh',BASE_ROM],check=True,env=env,capture_output=True)
    base=open(BASE_ROM,'rb').read(); pat=b'\x39\x03\x00\xff\x05\x00\x05\x00\x27'; assert base.count(pat)==1
    at=base.index(pat)
    import leg1
    cells=[]
    for name,(g,n),x,y,kind,pokes,flags,clear in D:
        w,h,m,_,_=M[(g,n)]
        col=lambda a,b: (m[b*w+a]>>10)&3
        best=None
        for dx,dy,key in ((-1,0,'R'),(1,0,'L'),(0,1,'U'),(0,-1,'D')):
            tiles=[(x+dx*k,y+dy*k) for k in (1,2)]
            if any(col(*t) for t in tiles): continue
            beyond=[(x-dx*k,y-dy*k) for k in (1,2)]
            sc=sum(1 for t in beyond if not col(*t))
            if best is None or sc>best[0]: best=(sc,dx,dy,key,tiles[1])
        assert best,name
        _,dx,dy,key,(sx,sy)=best
        rom=bytearray(base); rom[at:at+9]=bytes([0x39,g,n,0xff,sx&255,sx>>8,sy&255,sy>>8,0x27])
        if kind=='army_splat':     # TEST ONLY: switch the object's graphics id to the army alias 0xA1
            gp=struct.unpack('<I',rom[leg1.GROUPS:leg1.GROUPS+4])[0]
            gpg=struct.unpack('<I',rom[leg1.GROUPS+4*g:leg1.GROUPS+4*g+4])[0]-0x8000000
            hd=struct.unpack('<I',rom[gpg+4*n:gpg+4*n+4])[0]-0x8000000
            ev=struct.unpack('<I',rom[hd+4:hd+8])[0]-0x8000000; po=struct.unpack('<I',rom[ev+4:ev+8])[0]-0x8000000
            for i in range(rom[ev]):
                o=po+24*i; px,py=struct.unpack('<hh',rom[o+4:o+8])
                if (px,py)==(x,y) and rom[o+1]==0x98: rom[o+1]=0xA1
        open('/tmp/splat_one.gba','wb').write(rom)
        keys=f'W60 {key}2 W20 {key}2 W30'
        e=dict(os.environ,VIRI_ROM='/tmp/splat_one.gba',VIRI_POKE=pokes,VIRI_FLAGS=flags,VIRI_CLEAR=clear)
        subprocess.run(['python3','tools/viri_test.py',keys,'/tmp/_s.png','5','1450'],env=e,capture_output=True)
        fr={}
        for p in glob.glob('shots/vt_*.ppm'):
            f=int(p.split('_')[-1].split('.')[0]); d=open(p,'rb').read(); pa=d.split(b'\n',3); ww,hh=map(int,pa[1].split()); fr[f]=Image.frombytes('RGB',(ww,hh),pa[3])
        fs=sorted(fr)
        ax,ay=-dx*0+ (x-sx),(y-sy)       # decal offset in tiles from the start tile
        def crop(im,cx,cy): return im.crop((cx-48,cy-32,cx+48,cy+32)).resize((288,192),Image.NEAREST)
        cx0,cy0=120+16*ax,80+16*ay
        a=fr[1450]; b=fr[1500] if 1500 in fr else fr[fs[len(fs)//2]]
        c=fr[1535] if 1535 in fr else fr[fs[-3]]
        trip=[crop(a,cx0,cy0),crop(b,120,80),crop(c,120+16*(-(x-sx)//2) if False else 120-16*(0),80)]
        # walking over: decal one tile behind/at the player: centre between player and decal tile
        trip[2]=crop(c,120-8*(1 if ax==0 and False else 0)+0,80)
        for lab,im in zip(('inplace','standing_on','walking_over'),trip): im.save(f'shots/splatter_crops/{name}_{lab}.png')
        cells.append((name,(g,n),x,y,kind,trip)); print(name,(g,n),x,y,'start',(sx,sy),key)
    # sheets
    cw,ch=288,192; per=2
    def sheet(items,out):
        rows=(len(items)+per-1)//per; S=Image.new('RGB',(per*(3*cw+10),rows*(ch+22)),(25,25,25)); dr=ImageDraw.Draw(S)
        for k,(name,mp,x,y,kind,trip) in enumerate(items):
            X=(k%per)*(3*cw+10); Y=(k//per)*(ch+22)
            dr.text((X+3,Y+4),f'{name}  map {mp} tile ({x},{y})  [{kind}]   in place | standing on | walking over',fill=(255,255,0))
            for j,im in enumerate(trip): S.paste(im,(X+j*cw,Y+18))
        S.save(out); print(out,S.size)
    sheet(cells,'shots/splatter_all_sheet.png')
    sheet([c for c in cells if c[4]=='splat' or c[4]=='army_splat'],'shots/splatter_all_sheet_splatters.png')
    sheet([c for c in cells if c[4] in('body','feather')],'shots/splatter_all_sheet_bodies_feathers.png')
main()

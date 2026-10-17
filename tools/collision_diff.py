"""Compare map block data (metatile + collision bits) of two ROMs for every map; list the maps and tiles whose collision bit changed, and metatile changes.
usage: collision_diff.py BASE.gba FINAL.gba [OUT.json]   (read only)"""
import sys,struct,json,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(1,'/home/claude/work/tools')
import leg1
def maps(path):
    d=open(path,'rb').read(); r32=lambda o:struct.unpack('<I',d[o:o+4])[0]
    seen={}; 
    for g in range(0,6):
        try: gp=r32(leg1.GROUPS+4*g)-0x8000000
        except Exception: break
        n=0
        while True:
            hp=r32(gp+4*n)
            if not (0x8000000<=hp<0x8000000+len(d)-64): break
            h=hp-0x8000000
            try:
                lay=r32(h)-0x8000000; w,hh=struct.unpack('<II',d[lay:lay+8]); mp=r32(lay+12)-0x8000000
            except Exception: break
            if not(1<=w<=400 and 1<=hh<=400) or mp<0 or mp+2*w*hh>len(d): break
            if (g,n) not in seen: seen[(g,n)]=(w,hh,struct.unpack('<%dH'%(w*hh),d[mp:mp+2*w*hh]),r32(lay+16),r32(lay+20))
            n+=1
    return seen
if __name__=='__main__':
    A=maps(sys.argv[1]); B=maps(sys.argv[2]); res={}
    for k,(w,h,m,t1,t2) in sorted(B.items()):
        if k not in A: res[k]=dict(new=True,size=(w,h)); continue
        w0,h0,m0,u1,u2=A[k]
        if (w0,h0)!=(w,h): res[k]=dict(resized=((w0,h0),(w,h))); continue
        col=[];met=[]
        for i,(a,b) in enumerate(zip(m0,m)):
            if a!=b:
                x,y=i%w,i//w
                (col if (a>>10)&3!=(b>>10)&3 else met).append((x,y,(a>>10)&3,(b>>10)&3,a&0x3ff,b&0x3ff))
        if col or met or (t1,t2)!=(u1,u2): res[k]=dict(collision_changed=col,metatile_only=len(met),tilesets_changed=(t1,t2)!=(u1,u2),size=(w,h),met=met[:400])
    for k,v in res.items():
        print(k,{a:(len(b) if isinstance(b,list) and a!='met' else b) for a,b in v.items() if a!='met'})
    print(len(res),'maps differ of',len(B))
    if len(sys.argv)>3: json.dump({str(k):v for k,v in res.items()},open(sys.argv[3],'w'))

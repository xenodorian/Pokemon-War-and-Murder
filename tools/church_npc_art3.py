import sys; sys.path.insert(0,'/home/claude/work/tools')
import numpy as np
from PIL import Image
from scipy.cluster.vq import kmeans2
from church_npc_art2 import canvas,render,U
def reduce(f,w,h,dark_thr,dark_lum=95,cov_thr=0.5,ncol=14,seed=1):
    f=f.convert('RGBA'); f=f.crop(f.getchannel('A').point(lambda v:255 if v>128 else 0).getbbox())
    a=np.array(f).astype(float); H,W=a.shape[:2]; al=(a[...,3]>128)
    lum=0.3*a[...,0]+0.59*a[...,1]+0.11*a[...,2]
    ys=np.linspace(0,H,h+1).astype(int); xs=np.linspace(0,W,w+1).astype(int)
    out=np.zeros((h,w,3)); op=np.zeros((h,w),bool)
    for y in range(h):
      for x in range(w):
        sl=(slice(ys[y],ys[y+1]),slice(xs[x],xs[x+1])); m=al[sl]; 
        if m.mean()<cov_thr: continue
        op[y,x]=True; rgb=a[sl][...,:3]; L=lum[sl]
        dk=m&(L<dark_lum); nd=m&(L>=dark_lum)
        if dk.sum()/m.sum()>=dark_thr or nd.sum()==0: out[y,x]=rgb[dk].mean(0) if dk.any() else rgb[m].mean(0)
        else:
            # prefer the more saturated half of the non-dark pixels (avoid washed-out blends)
            v=rgb[nd]; ch=v.max(1)-v.min(1); sel=v[ch>=np.median(ch)]; out[y,x]=sel.mean(0)
    np.random.seed(seed); c,l=kmeans2(out[op],ncol,minit='++',seed=seed); c=np.clip(c.round(),0,255).astype(int)
    idx=np.zeros((h,w),int); idx[op]=l+1
    return idx,c
if __name__=='__main__':
    S='/tmp/claude-0/-home-user-Pokemon-Outlaw-Mod/aec82f34-6a53-5709-b1a8-a60bf5c1545c/scratchpad/'
    pi,pc=reduce(Image.open(U+'66e66e4a-image.webp'),16,23,0.45,ncol=14)
    fi,fc=reduce(Image.open(U+'c0f4bc8f-image.png'),16,21,0.2,dark_lum=110,ncol=10,seed=2)
    P=canvas(pi,bottom=30); F=canvas(fi,bottom=29)
    for n,i,c in (('priest',P,pc),('font',F,fc)): np.save('/home/claude/work/church/%s_idx.npy'%n,i); np.save('/home/claude/work/church/%s_col.npy'%n,c)
    grass=(170,225,190)
    tiles=[render(P,pc),render(P,pc,grass),render(F,fc),render(F,fc,grass)]
    out=Image.new('RGB',(4*(16*16+16),32*16),(255,255,255))
    for i,t in enumerate(tiles): out.paste(t,(i*(16*16+16),0))
    out.save(S+'npc_art2.png')

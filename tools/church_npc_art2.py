# Priest and font built directly from the user's art: alpha-aware BOX downsample + k-means palette, 16x32 frames.
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.cluster.vq import kmeans2
U='/root/.claude/uploads/aec82f34-6a53-5709-b1a8-a60bf5c1545c/'
def load_priest():
    im=Image.open(U+'66e66e4a-image.webp').convert('RGBA'); return im
def load_font():
    im=Image.open(U+'c0f4bc8f-image.png').convert('RGBA'); a=np.array(im).astype(int)
    white=(a[...,0]>228)&(a[...,1]>228)&(a[...,2]>228)
    lab,n=ndi.label(white)
    border=set(lab[0,:])|set(lab[-1,:])|set(lab[:,0])|set(lab[:,-1]); border.discard(0)
    out=np.isin(lab,list(border)); a[...,3]=np.where(out,0,255)
    return Image.fromarray(a.astype('uint8'),'RGBA')
def fit(im,w,h,ncol,seed=3):
    bb=im.getbbox() if im.getchannel('A').getbbox() is None else im.getchannel('A').getbbox()
    im=im.crop(bb)
    s=im.resize((w,h),Image.BOX)           # RGBA box (premultiplied internally)
    a=np.array(s).astype(float); op=a[...,3]>=110
    px=a[op][:,:3]
    np.random.seed(seed); c,l=kmeans2(px,ncol,minit='++',seed=seed)
    c=np.clip(c.round(),0,255).astype(int)
    idx=np.zeros((h,w),int); idx[op]=l+1
    return idx,c
def canvas(idx,H=32,W=16,bottom=31):
    h,w=idx.shape; out=np.zeros((H,W),int)
    y0=bottom+1-h; x0=(W-w)//2; out[y0:y0+h,x0:x0+w]=idx; return out
def render(idx,cols,bg=(255,0,255),K=16):
    rgb=np.zeros(idx.shape+(3,),'uint8'); rgb[:]=bg
    for i,c in enumerate(cols): rgb[idx==i+1]=c
    return Image.fromarray(rgb).resize((idx.shape[1]*K,idx.shape[0]*K),Image.NEAREST)
if __name__=='__main__':
    S='/tmp/claude-0/-home-user-Pokemon-Outlaw-Mod/aec82f34-6a53-5709-b1a8-a60bf5c1545c/scratchpad/'
    pi,pc=fit(load_priest(),16,23,14); fi,fc=fit(load_font(),16,21,10)
    P=canvas(pi,bottom=30); F=canvas(fi,bottom=29)
    np.save('/home/claude/work/church/priest_idx.npy',P); np.save('/home/claude/work/church/priest_col.npy',pc)
    np.save('/home/claude/work/church/font_idx.npy',F); np.save('/home/claude/work/church/font_col.npy',fc)
    grass=(170,225,190)
    tiles=[render(P,pc),render(P,pc,grass),render(F,fc),render(F,fc,grass)]
    out=Image.new('RGB',(4*(16*16+16),32*16),(255,255,255))
    for i,t in enumerate(tiles): out.paste(t,(i*(16*16+16),0))
    out.save(S+'npc_art2.png')

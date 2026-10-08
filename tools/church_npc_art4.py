# Final pixel art for the church: priest + font, built from the user's art. Writes church/{priest,font}_{idx,col}.npy and a preview.
import sys; sys.path.insert(0,'/home/claude/work/tools')
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from church_npc_art3 import reduce,canvas,render,U
S='/tmp/claude-0/-home-user-Pokemon-Outlaw-Mod/aec82f34-6a53-5709-b1a8-a60bf5c1545c/scratchpad/'
pi,pc=reduce(Image.open(U+'66e66e4a-image.webp'),16,23,0.45,ncol=14)
P=canvas(pi,bottom=30)
fi,fc=reduce(Image.open(U+'c0f4bc8f-image.png'),16,21,0.5,dark_lum=60,ncol=7,seed=2)
mask=fi>0; cols=[tuple(int(v) for v in c) for c in fc]+[(56,40,32),(130,92,58)]; iO=len(cols)-1; iC=len(cols)
idx=fi.copy(); er=ndi.binary_erosion(mask,structure=np.array([[0,1,0],[1,1,1],[0,1,0]])); idx[mask&~er]=iO
for y in range(6,11):
    for x in (7,8):
        if mask[y,x]: idx[y,x]=iC
for x in range(5,11):
    if mask[8,x] and idx[8,x]!=iO: idx[8,x]=iC
F=canvas(idx,bottom=29)
np.save('/home/claude/work/church/priest_idx.npy',P); np.save('/home/claude/work/church/priest_col.npy',pc)
np.save('/home/claude/work/church/font_idx.npy',F); np.save('/home/claude/work/church/font_col.npy',np.array(cols))
grass=(170,225,190)
tiles=[render(P,pc),render(P,pc,grass),render(F,cols),render(F,cols,grass)]
out=Image.new('RGB',(4*(16*16+16),32*16),(255,255,255))
for i,t in enumerate(tiles): out.paste(t,(i*(16*16+16),0))
out.save(S+'npc_art_final.png')

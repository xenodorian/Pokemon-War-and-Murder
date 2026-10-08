import sys; sys.path.insert(0,'/home/claude/work/tools')
import numpy as np
from PIL import Image
from church_art import draw,PAL
S='/tmp/claude-0/-home-user-Pokemon-Outlaw-Mod/aec82f34-6a53-5709-b1a8-a60bf5c1545c/'
im=draw(); a=np.array(im)
rgb=np.zeros(a.shape+(3,),'uint8')+np.array((170,225,190),'uint8')
for i,c in enumerate(PAL):
    if i: rgb[a==i]=c
m=Image.open(S+'images/8.webp').convert('RGB').resize((384,320),Image.BOX).crop((96,144,160,256))
out=Image.new('RGB',(64*6*2+24,112*6),(255,255,255))
out.paste(m.resize((384,672),Image.NEAREST),(0,0)); out.paste(Image.fromarray(rgb).resize((384,672),Image.NEAREST),(408,0))
out.save(S+'scratchpad/church_cmp.png')

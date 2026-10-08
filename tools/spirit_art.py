# 16x32 spirit flame for the Dark Spirit encounters, drawn with the shared story palette (tag 0x1120) so it never clashes with the splatter or feather.
# palette indices used: 2 black outline, 1 light blue body, 5 grey-blue shade, 8 white
from PIL import Image,ImageDraw
import numpy as np
from scipy import ndimage as ndi
SHARED=[(255,0,255),(156,189,222),(0,0,0),(246,205,180),(90,24,24),(98,115,139),(148,57,57),(213,148,106),(255,255,255),(197,123,32),(0,0,0),(222,0,0),(238,0,0),(164,0,0),(180,0,0),(0,0,0)]
def wisp():
    out=np.zeros((32,16),int)
    ys,xs=np.mgrid[0:32,0:16]
    cx=7.5
    head=((xs-cx)**2/36.0+(ys-12.5)**2/42.0)<=1.0            # rounded head
    torso=(abs(xs-cx)<=6.3)&(ys>=12)&(ys<=24)
    # wavy hem: three scallops
    hem=np.zeros_like(torso)
    for x in range(16):
        depth=24+int(round(2.2*abs(np.sin((x-1.5)*np.pi/4.0))))
        hem[24:depth+1,x]=abs(x-cx)<=6.3
    body=(head|torso|hem)
    inner=ndi.binary_erosion(body,iterations=1)
    out[body]=2
    out[inner]=1
    shade=inner&(((xs-cx)*0.9+(ys-14)*0.5)>3.4)               # right side shading
    out[shade]=5
    hl=inner&(((xs-4.5)**2/2.5+(ys-9)**2/5.0)<=1.0)           # head highlight
    out[hl]=8
    # eyes: black ovals with a white glint, and a wailing mouth
    for x0 in (4,9):
        out[13:17,x0:x0+2]=2
        out[13,x0]=8
    out[19:22,6:10]=2; out[20:21,7:9]=5
    return np.roll(out,4,axis=0)
if __name__=='__main__':
    a=wisp(); rgb=np.zeros(a.shape+(3,),'uint8')+np.array((170,225,190),'uint8')
    for i,c in enumerate(SHARED):
        if i: rgb[a==i]=c
    Image.fromarray(rgb).resize((16*16,32*16),Image.NEAREST).save('/tmp/claude-0/-home-user-Pokemon-Outlaw-Mod/aec82f34-6a53-5709-b1a8-a60bf5c1545c/scratchpad/wisp.png')

# Procedural 64x112 native-resolution church sprite, indexed (0 = transparent), 15 colors.
from PIL import Image, ImageDraw
PAL=[(0,0,0),            # 0 transparent
 (74,76,92),             # 1 outline
 (232,120,92),           # 2 roof light
 (208,88,72),            # 3 roof mid
 (160,64,64),            # 4 roof dark
 (240,232,200),          # 5 cream light
 (216,200,160),          # 6 stone
 (184,168,128),          # 7 brick line
 (160,106,56),           # 8 door
 (120,78,40),            # 9 door dark
 (44,48,80),             # 10 window navy
 (84,104,160),           # 11 window light
 (168,172,184),          # 12 steps
 (200,144,56),           # 13 bell
 (255,255,255)]          # 14 white (door handle) 
def draw():
    W,H=64,112
    im=Image.new('P',(W,H),0); im.putpalette([c for p in PAL for c in p]+[0]*(768-3*len(PAL)))
    d=ImageDraw.Draw(im)
    def poly(pts,fill,outline=1):
        d.polygon(pts,fill=fill,outline=outline)
    # ---- stone gable + walls (behind roof)
    poly([(1,69),(31,47),(32,47),(62,69),(62,98),(1,98)],6)
    for y in range(74,98,5): d.line([(2,y),(61,y)],fill=7)
    for y in range(52,70,5):
        half=int((y-47)*1.4)
        d.line([(31-half+2,y),(32+half-2,y)],fill=7)
    for y in range(74,98,10):
        for x in range(8,60,12): d.line([(x,y),(x,y+4)],fill=7)
    d.rectangle([1,69,4,98],fill=5,outline=1); d.rectangle([59,69,62,98],fill=5,outline=1)
    # ---- main roof slabs
    poly([(0,39),(22,29),(22,52),(31,47),(0,69)],3)
    poly([(63,39),(41,29),(41,52),(32,47),(63,69)],4)
    for x in range(3,22,3):
        y0=int(39-0.45*x)+2; y1=int(69-0.7*x)-2
        d.line([(x,y0),(x,y1)],fill=2)
    for x in range(42,62,3):
        y0=int(39-0.45*(63-x))+2; y1=int(69-0.7*(63-x))-2
        d.line([(x,y0),(x,y1)],fill=3)
    d.line([(0,69),(31,47)],fill=1); d.line([(32,47),(63,69)],fill=1)
    d.line([(0,70),(31,48)],fill=4); d.line([(32,48),(63,70)],fill=4)
    # ---- steeple tower body
    d.rectangle([21,18,42,49],fill=5,outline=1)
    d.rectangle([25,27,38,40],fill=10,outline=1)       # bell opening
    d.point((25,27),fill=5); d.point((38,27),fill=5)
    d.ellipse([29,30,34,37],fill=13)                   # bell
    d.line([(31,37),(32,37)],fill=9)
    d.rectangle([25,41,38,47],fill=6,outline=1)        # sill
    # ---- steeple roof
    poly([(19,13),(22,9),(41,9),(44,13),(44,25),(32,19),(31,19),(19,25)],3)
    poly([(32,10),(40,10),(43,13),(43,24),(32,19)],4,outline=None)
    d.line([(32,10),(32,19)],fill=4)
    for x in range(22,31,3): d.line([(x,12),(x,21)],fill=2)
    for x in range(35,42,3): d.line([(x,12),(x,21)],fill=3)
    d.line([(19,25),(31,19)],fill=1); d.line([(32,19),(44,25)],fill=1)
    d.line([(19,26),(31,20)],fill=4); d.line([(32,20),(44,26)],fill=4)
    # cross
    d.rectangle([31,2,32,12],fill=1); d.rectangle([28,5,35,6],fill=1)
    # ---- windows (arched, brown frame)
    for x0 in (6,48):
        d.rectangle([x0,76,x0+9,91],fill=9,outline=1)
        d.rectangle([x0+2,78,x0+7,88],fill=10)
        d.point((x0+2,78),fill=9); d.point((x0+7,78),fill=9)
        d.point((x0,76),fill=6); d.point((x0+9,76),fill=6); d.point((x0+1,76),fill=1); d.point((x0+8,76),fill=1)
        d.line([(x0+4,79),(x0+4,88)],fill=11); d.line([(x0+5,79),(x0+5,88)],fill=11)
        d.line([(x0+2,83),(x0+7,83)],fill=11)
        d.rectangle([x0,90,x0+9,91],fill=5,outline=1)
    # ---- porch
    d.rectangle([21,78,42,98],fill=5,outline=1)
    d.rectangle([26,83,37,98],fill=9,outline=1)
    d.rectangle([27,84,36,98],fill=8)
    d.line([(31,84),(31,98)],fill=9); d.line([(32,84),(32,98)],fill=9)
    d.point((35,92),fill=14)
    d.rectangle([24,79,39,83],fill=6)
    poly([(17,74),(31,65),(32,65),(46,74),(46,87),(32,76),(31,76),(17,87)],3)
    poly([(32,66),(45,74),(45,86),(32,77)],4,outline=None)
    d.line([(31,66),(31,76)],fill=4); d.line([(32,66),(32,76)],fill=4)
    d.line([(17,74),(31,65)],fill=1); d.line([(32,65),(46,74)],fill=1)
    for x in range(19,30,3): d.line([(x,75),(x,82)],fill=2)
    for x in range(34,45,3): d.line([(x,75),(x,82)],fill=3)
    d.line([(17,74),(17,87)],fill=1); d.line([(46,74),(46,87)],fill=1)
    d.line([(17,87),(31,77)],fill=1); d.line([(32,77),(46,87)],fill=1)
    d.line([(17,86),(31,76)],fill=4); d.line([(32,76),(46,86)],fill=4)
    # ---- steps
    d.rectangle([24,99,39,105],fill=12,outline=1)
    d.line([(25,101),(38,101)],fill=1); d.line([(25,103),(38,103)],fill=1)
    return im
if __name__=='__main__':
    import sys
    im=draw(); im.save('/home/claude/work/church/church.png')
    S='/tmp/claude-0/-home-user-Pokemon-Outlaw-Mod/aec82f34-6a53-5709-b1a8-a60bf5c1545c/'
    m=Image.open(S+'images/8.webp').convert('RGB').resize((384,320),Image.BOX).crop((96,144,160,256))
    c=im.convert('RGBA'); bgc=Image.new('RGBA',c.size,(170,225,190,255)); 
    t=Image.new('P',im.size,0)
    rgba=im.convert('RGB').copy(); a=Image.eval(im.point(lambda v:255 if v else 0),lambda v:v).convert('L')
    comp=Image.new('RGB',(64*2+4,112),(255,0,255)); 
    b=Image.new('RGB',im.size,(170,225,190)); b.paste(rgba,mask=a)
    out=Image.new('RGB',((64*2+4)*6,112*6)); out.paste(m.resize((64*6,112*6),Image.NEAREST),(0,0)); out.paste(b.resize((64*6,112*6),Image.NEAREST),((64+4)*6,0)); out.save(S+'scratchpad/church_cmp.png')

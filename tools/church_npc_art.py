# Native-resolution pixel art for the church interior: priest (16x32 NPC frame) and baptismal font (16x32 object frame).
from PIL import Image
import numpy as np
def build(rows,pal):
    h=len(rows); w=len(rows[0]); a=np.zeros((h,w),np.uint8)
    for y,r in enumerate(rows):
        assert len(r)==w,(y,len(r))
        for x,ch in enumerate(r): a[y,x]=pal.index(ch)
    return a
# ---------------------------------------------------------------- priest
PRIEST_PAL=['.','K','b','B','p','w','g','o','O','s','r','R','D']   # idx 0..12
PRIEST_COL={'.':(0,0,0),
 'K':(40,36,48),   # outline
 'b':(72,112,208), # mitre blue
 'B':(48,72,160),  # blue dark
 'p':(176,144,240),# purple highlight / lens
 'w':(244,244,244),# white
 'g':(168,168,176),# gray shade
 'o':(232,152,72), # orange (hair / beard)
 'O':(192,112,48), # orange dark
 's':(248,196,140),# skin
 'r':(224,96,112), # red book
 'R':(176,56,72),  # red dark
 'D':(24,24,32)}   # glasses black
PRIEST=[
"................",
"................",
".....KKKKKK.....",
"....KbbppbbK....",
"....KbppppbK....",
"...KKbbppbbKK...",
"..KwKBbbbbBKwK..",
"..KwwKooooKwwK..",
".KwwKooooooKwwK.",
".KwKoooooooKwK..",
"..KKOoooooooKK..",
".KODDDDDDDDDDOK.",
".KODpwpDDpwpDOK.",
".KODpppDDpppDOK.",
".KODDDDDDDDDDOK.",
".KOossssssssoOK.",
".KOoooossssoooOK",
"..KOooooooooOK..",
"...KKOooooOKK...",
"...KKKwwwwKKK...",
"..KrrrKwppwKbbK.",
".KrrRrrKwwwKwbbK",
".KrwwRrKbbbKwbbK",
".KRrRRrKbbbKbbBK",
".KRrrRrKBbbKbBBK",
".KsKRRKKBbbKBBBK",
".KsKKKKBBbbBBBBK",
"..KK.KBBBbbBBBK.",
".....KBBBBBBBK..",
".....KBBBBBBBK..",
"......KKBBBKK...",
"......KKKKKKK..."]
# ---------------------------------------------------------------- font
FONT_PAL=['.','K','t','T','d','a','l','c']
FONT_COL={'.':(0,0,0),
 'K':(60,44,36),   # outline
 't':(224,200,152),# tan light
 'T':(200,168,116),# tan mid
 'd':(168,136,92), # tan dark
 'a':(152,188,196),# water
 'l':(228,242,242),# wave highlight
 'c':(140,100,60)} # cross
def font_rows():
    from PIL import ImageDraw
    im=Image.new('P',(16,32),0); d=ImageDraw.Draw(im)
    idx={c:i for i,c in enumerate(FONT_PAL)}
    K,T,t,dk,aq,l,c=idx['K'],idx['T'],idx['t'],idx['d'],idx['a'],idx['l'],idx['c']
    d.ellipse([0,6,15,15],fill=K); d.ellipse([1,7,14,14],fill=T)           # rim
    d.ellipse([3,8,12,12],fill=K); d.ellipse([4,9,11,11],fill=aq)            # water
    d.point((6,10),fill=l); d.point((7,10),fill=l); d.point((9,9),fill=l); d.point((10,10),fill=l)
    d.polygon([(2,11),(13,11),(12,17),(10,20),(5,20),(3,17)],fill=K)         # bowl
    d.polygon([(3,12),(12,12),(11,17),(9,19),(6,19),(4,17)],fill=t)
    d.line([(11,13),(11,16)],fill=dk); d.line([(10,17),(10,18)],fill=dk)
    d.line([(4,12),(11,12)],fill=T)                                          # rim shadow
    d.rectangle([7,14,8,18],fill=c); d.rectangle([5,15,10,16],fill=c)        # cross
    d.rectangle([6,20,9,24],fill=K); d.rectangle([7,20,8,24],fill=t); d.point((8,21),fill=dk); d.point((8,23),fill=dk)
    d.rectangle([5,19,10,20],fill=K); d.rectangle([6,19,9,19],fill=T)         # neck ring
    d.polygon([(3,25),(12,25),(14,27),(14,29),(1,29),(1,27)],fill=K)        # base
    d.polygon([(4,26),(11,26),(13,27),(13,28),(2,28),(2,27)],fill=t)
    d.line([(2,28),(13,28)],fill=dk)
    return [''.join(FONT_PAL[v] for v in row) for row in np.array(im)]
FONT=font_rows()
def render(rows,pal,col):
    a=build(rows,pal); im=Image.new('RGBA',(a.shape[1],a.shape[0]),(0,0,0,0))
    px=im.load()
    for y in range(a.shape[0]):
        for x in range(a.shape[1]):
            c=pal[a[y,x]]
            if c!='.': px[x,y]=col[c]+(255,)
    return im
if __name__=='__main__':
    S='/tmp/claude-0/-home-user-Pokemon-Outlaw-Mod/aec82f34-6a53-5709-b1a8-a60bf5c1545c/scratchpad/'
    pr=render(PRIEST,PRIEST_PAL,PRIEST_COL); fo=render(FONT,FONT_PAL,FONT_COL)
    pr.save('/home/claude/work/church/priest.png'); fo.save('/home/claude/work/church/font.png')
    K=16; grass=(170,225,190,255)
    W=(16+2)*K*4; out=Image.new('RGBA',(W,32*K+8),(255,255,255,255))
    x=0
    for im,bgc in ((pr,(255,0,255,255)),(pr,grass),(fo,(255,0,255,255)),(fo,grass)):
        t=Image.new('RGBA',im.size,bgc); t.alpha_composite(im)
        out.paste(t.resize((16*K,32*K),Image.NEAREST),(x,4)); x+=18*K
    out.convert('RGB').save(S+'npc_art.png')

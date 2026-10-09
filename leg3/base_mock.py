# Mockup of a military base interior in the GBA tile style (16x16 metatiles, limited palette). Art preview only, not in the ROM.
from PIL import Image
import random
random.seed(7)
T=16; W,H=16,12
img=Image.new('RGB',(W*T,H*T),(0,0,0)); P=img.load()
C=dict(
 blk=(16,16,20), wall=(92,100,96), walld=(66,74,72), wallh=(124,134,128), steel=(150,158,160), steeld=(104,112,118),
 floor=(176,172,156), floord=(150,146,132), floorh=(196,192,176), seam=(128,124,112),
 olive=(84,98,56), olived=(58,70,40), oliveh=(112,128,76), tan=(196,172,120), tand=(150,128,84), tanh=(224,204,152),
 red=(176,40,40), redd=(120,24,28), white=(240,240,236), yel=(228,196,48), black=(30,30,34),
 skin=(240,200,164), skind=(200,150,116), wood=(120,84,52), woodd=(84,56,34), woodh=(156,116,76),
 green=(60,140,84), blue=(60,96,160), paper=(228,220,184), sand=(188,164,108), sandd=(148,124,76))
def px(x,y,c):
    if 0<=x<W*T and 0<=y<H*T: P[x,y]=C[c] if isinstance(c,str) else c
def rect(x0,y0,x1,y1,c):
    for y in range(y0,y1+1):
        for x in range(x0,x1+1): px(x,y,c)
def box(x0,y0,x1,y1,fill,edge='blk'):
    rect(x0,y0,x1,y1,edge); rect(x0+1,y0+1,x1-1,y1-1,fill)
def floor_tile(tx,ty):
    x0,y0=tx*T,ty*T
    rect(x0,y0,x0+15,y0+15,'floor')
    for i in range(16): px(x0+i,y0,'floorh'); px(x0,y0+i,'floorh'); px(x0+i,y0+15,'seam'); px(x0+15,y0+i,'seam')
    for _ in range(5): px(x0+random.randint(2,13),y0+random.randint(2,13),'floord')
def wall_tile(tx,ty,vent=False):
    x0,y0=tx*T,ty*T
    rect(x0,y0,x0+15,y0+15,'wall')
    for i in range(16): px(x0+i,y0,'wallh'); px(x0+i,y0+15,'walld'); px(x0+i,y0+7,'walld'); px(x0+i,y0+8,'wallh')
    for yy in (y0+3,y0+11):
        for xx in (x0+2,x0+13): px(xx,yy,'steel'); px(xx+1,yy+1,'walld')
    if vent:
        rect(x0+4,y0+3,x0+11,y0+12,'blk')
        for k in range(4,13,2): rect(x0+5,y0+k-1,x0+10,y0+k-1,'steeld')
def hazard(x0,y0,x1,y1):
    for y in range(y0,y1+1):
        for x in range(x0,x1+1): px(x,y,'yel' if ((x+y)//4)%2==0 else 'black')
def crate(x0,y0,s=16):
    box(x0,y0,x0+s-1,y0+s-1,'woodh','blk')
    rect(x0+1,y0+1,x0+s-2,y0+2,'woodh'); rect(x0+1,y0+s-3,x0+s-2,y0+s-2,'woodd')
    for i in range(1,s-1): px(x0+i,y0+i,'woodd'); px(x0+s-1-i,y0+i,'woodd')
    rect(x0+s//2-2,y0+s//2-1,x0+s//2+1,y0+s//2+1,'tan')
def sandbags(x0,y0,n):
    for i in range(n):
        for row in (0,1):
            bx=x0+i*14+(row*7); by=y0+row*7
            box(bx,by,bx+14,by+8,'sand'); rect(bx+2,by+2,bx+11,by+3,'tan'); rect(bx+2,by+6,bx+12,by+6,'sandd')
def locker(x0,y0):
    box(x0,y0,x0+14,y0+30,'steel'); rect(x0+1,y0+1,x0+13,y0+2,'steeld')
    rect(x0+7,y0+1,x0+7,y0+29,'steeld'); rect(x0+5,y0+14,x0+5,y0+17,'blk'); rect(x0+9,y0+14,x0+9,y0+17,'blk')
    for k in (5,8,11): rect(x0+2,y0+k,x0+5,y0+k,'steeld'); rect(x0+9,y0+k,x0+12,y0+k,'steeld')
def cot(x0,y0):
    box(x0,y0,x0+30,y0+14,'olive'); rect(x0+1,y0+1,x0+8,y0+13,'white'); rect(x0+1,y0+1,x0+8,y0+2,'floorh')
    for k in range(10,30,6): rect(x0+k,y0+3,x0+k,y0+12,'olived')
    rect(x0+2,y0+15,x0+3,y0+18,'blk'); rect(x0+27,y0+15,x0+28,y0+18,'blk')
def flag(x0,y0):
    rect(x0,y0,x0+1,y0+30,'steeld')
    box(x0+2,y0+1,x0+24,y0+20,'redd'); rect(x0+3,y0+2,x0+23,y0+19,'red')
    # star
    cx,cy=x0+13,y0+10
    for dx,dy in [(0,-5),(0,-4),(0,-3),(-1,-2),(1,-2),(-5,-1),(-4,-1),(-3,-1),(-2,-1),(2,-1),(3,-1),(4,-1),(5,-1),(-3,0),(-2,0),(-1,0),(0,0),(1,0),(2,0),(3,0),(-2,1),(-1,1),(0,1),(1,1),(2,1),(-2,2),(-1,2),(1,2),(2,2),(-3,3),(3,3)]: px(cx+dx,cy+dy,'yel')
def map_panel(x0,y0,w,h):
    box(x0,y0,x0+w-1,y0+h-1,'paper','blk')
    # region outline (a crude Kanto-like blob) with pins
    pts=[(x0+4+i*3, y0+5+int(3*((i*7)%5)/4)) for i in range(0,(w-8)//3)]
    for (a,b) in pts: rect(a,b,a+2,b+2,'green')
    for (a,b) in pts[::2]: px(a+1,b-1,'red'); px(a+1,b-2,'red')
    for i in range(3): rect(x0+3,y0+h-5+i,x0+w-4,y0+h-5+i,'seam') if i==0 else None
def war_table(x0,y0,w,h):
    box(x0,y0,x0+w-1,y0+h-1,'woodh','blk'); rect(x0+1,y0+h-5,x0+w-2,y0+h-2,'woodd')
    box(x0+4,y0+3,x0+w-5,y0+h-8,'paper','blk')
    for k in range(6,w-8,5): rect(x0+k,y0+6,x0+k+2,y0+8,'green'); px(x0+k+1,y0+5,'red')
    for k in range(4): px(x0+8+k*7,y0+h-10,'blue')
def soldier(x0,y0,face='d',captain=False):
    # 14x22 sprite, feet at y0+21
    helmet='olived' if not captain else 'black'
    body='olive' if not captain else 'tand'
    bodyh='oliveh' if not captain else 'tanh'
    bodyd='olived' if not captain else 'woodd'
    rect(x0+4,y0+2,x0+9,y0+6,helmet); rect(x0+3,y0+4,x0+10,y0+5,helmet); rect(x0+5,y0+1,x0+8,y0+1,helmet)
    if captain: rect(x0+3,y0+6,x0+10,y0+6,'blk'); rect(x0+6,y0+3,x0+7,y0+3,'yel')
    if face=='d':
        rect(x0+4,y0+7,x0+9,y0+10,'skin'); px(x0+5,y0+8,'blk'); px(x0+8,y0+8,'blk'); rect(x0+5,y0+10,x0+8,y0+10,'skind')
    elif face=='u': rect(x0+4,y0+7,x0+9,y0+10,helmet)
    else:
        rect(x0+4,y0+7,x0+9,y0+10,'skin'); px(x0+4 if face=='l' else x0+9,y0+8,'blk')
    rect(x0+3,y0+11,x0+10,y0+17,body); rect(x0+3,y0+11,x0+10,y0+11,bodyh); rect(x0+3,y0+16,x0+10,y0+16,'black')
    rect(x0+1,y0+12,x0+2,y0+16,body); rect(x0+11,y0+12,x0+12,y0+16,body); px(x0+1,y0+17,'skin'); px(x0+12,y0+17,'skin')
    if captain:
        for k in (0,2): rect(x0+4+k*3,y0+12,x0+5+k*3,y0+12,'yel')
    rect(x0+4,y0+18,x0+6,y0+21,bodyd); rect(x0+7,y0+18,x0+9,y0+21,bodyd); rect(x0+4,y0+21,x0+6,y0+21,'blk'); rect(x0+7,y0+21,x0+9,y0+21,'blk')
    # outline
    for yy in range(y0,y0+23):
        for xx in range(x0,x0+14):
            if P[xx,yy]==C['floor'] or P[xx,yy]==C['floorh'] or P[xx,yy]==C['seam'] or P[xx,yy]==C['floord']:
                n=[(xx+1,yy),(xx-1,yy),(xx,yy+1),(xx,yy-1)]
                if any(0<=a<W*T and 0<=b<H*T and P[a,b] in (C['olive'],C['olived'],C['oliveh'],C['skin'],C['black'],C['tand'],C['tanh'],C['woodd']) for a,b in n): P[xx,yy]=C['blk']
# ----- floor, walls
for ty in range(H):
    for tx in range(W): floor_tile(tx,ty)
for tx in range(W):
    wall_tile(tx,0,vent=(tx in (1,14))); wall_tile(tx,1)
for ty in range(2,H):
    for tx in (0,15):
        wall_tile(tx,ty)
for tx in range(W):
    if tx not in (7,8): wall_tile(tx,H-1)
# hazard lane in front of the entrance and along the north wall base
hazard(16,2*T,W*T-17,2*T+3)
hazard(7*T,(H-2)*T,9*T-1,(H-2)*T+3)
# wall decor
flag(3*T-2,5); flag(12*T-6,5)
map_panel(5*T+4,6,6*T-8,24)
# captain desk
box(6*T,3*T-2,10*T-1,4*T+2,'woodh'); rect(6*T+1,4*T-4,10*T-2,4*T+1,'woodd')
rect(6*T+10,3*T,6*T+17,3*T+4,'paper'); rect(8*T+8,3*T+1,8*T+13,3*T+4,'blk'); px(8*T+10,3*T+2,'green')
# lockers left, cots right
for k in range(3): locker(16+k*15,2*T+8)
cot(12*T+8,3*T+4); cot(12*T+8,5*T+2)
# sandbags and crates
sandbags(2*T,6*T+4,3); sandbags(10*T+8,6*T+4,3)
war_table(6*T+2,7*T+4,4*T-4,2*T-2)
crate(1*T+2,9*T); crate(2*T+6,9*T+4); crate(1*T+2,8*T-4) if False else None
crate(13*T,9*T); crate(12*T+2,8*T+6) if False else None
# entrance mat and door gap
rect(7*T+2,(H-1)*T+2,9*T-3,H*T-3,'redd'); rect(7*T+3,(H-1)*T+3,9*T-4,H*T-4,'red')
# ----- people
soldier(4*T+1,3*T+2,'d'); soldier(11*T-2,4*T+6,'l')
soldier(5*T-4,8*T+8,'r'); soldier(10*T+4,8*T+8,'l')
soldier(7*T+1,2*T-2+6,'d',captain=True)
img.save('/home/claude/work/leg3/base_mock_1x.png')
img.resize((W*T*4,H*T*4),Image.NEAREST).save('/home/claude/work/shots/base_mock.png')
print(img.size)

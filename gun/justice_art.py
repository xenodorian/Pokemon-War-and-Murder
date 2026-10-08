"""16x16 tiles for the HALL OF JUSTICE (palette indices 1..15). Marble floor, red and gold carpet, stone walls with navy banners, columns, glass display cases, a dais with the scales of justice."""
import numpy as np
PAL=[(50,54,72),(226,230,240),(203,209,226),(171,180,205),(168,170,186),(122,124,146),(176,32,44),(128,22,34),(236,196,64),(170,128,30),(34,52,112),(250,250,250),(126,176,224),(150,100,60),(212,196,164)]
# indices: 1 outline, 2 marble light, 3 marble mid, 4 marble dark, 5 stone light, 6 stone dark, 7 carpet, 8 carpet dark, 9 gold, 10 gold dark, 11 navy, 12 white, 13 glass, 14 bronze, 15 dais
def new(c): return np.full((16,16),c,int)
def rect(a,x0,y0,x1,y1,c): a[y0:y1+1,x0:x1+1]=c
def floor(kind):
    a=new(2 if kind==0 else 3); edge=3 if kind==0 else 4
    a[0,:]=edge; a[:,0]=edge
    rs=np.random.RandomState(3+kind)
    for _ in range(5): a[rs.randint(1,16),rs.randint(1,16)]=12 if kind==0 else 2
    return a
def carpet(kind):
    a=new(7)
    for x in (3,12): a[:,x]=8
    for y in range(2,16,4):
        for x in range(2,16,4):
            if kind==1 and (x+y)%8==4: a[y,x]=9
    if kind==0:
        rect(a,0,0,1,15,9); a[:,2]=10; a[:,3]=8
    if kind==2:
        rect(a,14,0,15,15,9); a[:,13]=10; a[:,12]=8
    return a
def brick(a,y0=0,y1=15):
    for y in range(y0,y1+1):
        if y%5==0: a[y,:]=6
        else:
            off=(y//5%2)*4
            for x in range(off,16,8): a[y,x]=6
def wall_top():
    a=new(5); brick(a); a[0,:]=1; return a
def wall_mid():
    a=new(5); brick(a); a[13,:]=6; a[14,:]=6; a[15,:]=1; return a
def emblem(a,cx,cy):
    """scales of justice, gold, about 9 wide"""
    a[cy-3:cy+5,cx]=9; a[cy-3,cx-4:cx+5]=9
    for dx in (-4,4):
        a[cy-2:cy+1,cx+dx]=10; a[cy+1,cx+dx-2:cx+dx+3]=9; a[cy+2,cx+dx-1:cx+dx+2]=10
    a[cy+5,cx-2:cx+3]=9
def banner(kind):
    a=wall_top() if kind==0 else wall_mid()
    rect(a,4,0,11,15 if kind==0 else 10,11)
    a[:,4]=9 if kind==0 else a[:,4];
    if kind==0:
        a[:,4]=9; a[:,11]=9; emblem(a,7,7)
    else:
        a[0:11,4]=9; a[0:11,11]=9
        rect(a,4,11,11,12,9); a[13,5:11]=9; a[14,6:10]=9; a[15,7:9]=1
        a[13:15,4]=a[13:15,4]
    return a
def wall_emblem():
    a=wall_top(); emblem(a,7,8); return a
def column():
    a=floor(0)
    rect(a,4,3,11,13,12); a[3:14,4]=3; a[3:14,11]=4; a[3:14,5]=2; a[3:14,10]=3
    rect(a,2,1,13,2,2); rect(a,2,14,13,14,4)
    for x in range(2,14): a[1,x]=1; a[15,x]=1
    a[1:15,2]=1; a[1:15,13]=1
    a[3:14,3]=1; a[3:14,12]=1
    return a
def cabinet():
    a=floor(0)
    rect(a,2,2,13,14,10); rect(a,3,3,12,12,9); rect(a,4,4,11,10,13)
    # medal: gold disc and a red ribbon
    for y in range(6,10):
        for x in range(6,10): a[y,x]=9
    a[5,7:9]=7; a[4,7:9]=7
    rect(a,5,11,10,12,14); a[11,5:11]=10
    a[2,2:14]=1; a[14,2:14]=1; a[2:15,2]=1; a[2:15,13]=1
    return a
def dais():
    a=new(15); a[15,:]=10; a[14,:]=3; a[0,:]=3
    for x in range(2,16,6): a[:,x]=3 if False else a[:,x]
    return a
def statue_top():
    a=dais()
    a[3:16,7]=9; a[3:16,8]=9; a[0:3,7:9]=10
    a[3,2:14]=9; a[4,2:14]=10
    for dx in (2,13):
        a[5:9,dx]=10
    a[9,0:6]=9; a[10,1:5]=10; a[9,10:16]=9; a[10,11:15]=10
    a[8,2]=10; a[8,13]=10
    return a
def statue_bot():
    a=dais()
    rect(a,4,0,11,12,14); a[0,4:12]=10; rect(a,5,5,10,8,9); a[5,5:11]=10
    for x in range(4,12): a[12,x]=1
    a[0:13,4]=1; a[0:13,11]=1
    return a
def doormat():
    a=floor(0); rect(a,2,4,13,11,7); a[4,2:14]=9; a[11,2:14]=9; a[4:12,2]=9; a[4:12,13]=9; return a
TILES=[floor(0),floor(1),carpet(1),carpet(0),carpet(2),wall_top(),wall_mid(),banner(0),banner(1),column(),cabinet(),dais(),statue_top(),statue_bot(),doormat(),wall_emblem()]
(F0,F1,CC,CL,CR,WT,WM,BT,BB,COL,CAB,DAIS,STT,STB,MAT,WEM)=range(16)
BLOCKED={WT,WM,BT,BB,COL,CAB,STT,STB,WEM}

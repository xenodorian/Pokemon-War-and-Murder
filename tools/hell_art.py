# 16x16 tiles for HELL: ash floor (two variants), lava (two variants), rock wall, exit portal. Palette indices 1..14 (0 transparent).
import numpy as np
PAL=[(20,12,12),(52,36,36),(84,60,56),(116,84,76),(156,28,20),(212,60,24),(248,132,32),(255,216,96),(255,240,200),(36,24,28),(68,48,48),(100,72,68),(136,64,200),(216,176,255)]
def rng(seed): return np.random.RandomState(seed)
def floor(seed):
    r=rng(seed); a=np.full((16,16),2,int)
    for _ in range(26): a[r.randint(0,16),r.randint(0,16)]=3
    for _ in range(10): a[r.randint(0,16),r.randint(0,16)]=4
    for _ in range(8): a[r.randint(0,16),r.randint(0,16)]=1
    # cracks
    x=r.randint(3,12); y=r.randint(0,4)
    for k in range(9):
        a[(y+k)%16,(x+(k//3))%16]=1
    return a
def lava(seed):
    r=rng(seed); a=np.full((16,16),6,int)
    for y in range(16):
        for x in range(16):
            v=np.sin((x+seed*3)*0.9)+np.cos((y*1.1)+x*0.4)
            if v>1.1: a[y,x]=7
            elif v<-1.2: a[y,x]=5
    for _ in range(5): a[r.randint(0,16),r.randint(0,16)]=8
    return a
def rock(seed):
    r=rng(seed); a=np.full((16,16),10,int)
    for y in range(0,16,4):
        a[y,:]=1
        off=(y//4%2)*4
        for x in range(off,16,8): a[y:y+4,x]=1
    for _ in range(30): a[r.randint(0,16),r.randint(0,16)]=11
    for _ in range(12): a[r.randint(0,16),r.randint(0,16)]=12
    return a
def portal():
    a=floor(7).copy()
    cx=cy=7.5
    for y in range(16):
        for x in range(16):
            d=((x-cx)**2+(y-cy)**2)**.5
            if d<7.5: a[y,x]=13 if d>5.2 else (14 if d>3.2 else 12)
            if d<2.3: a[y,x]=14
            if abs(d-5.3)<0.7 and (x+y)%3==0: a[y,x]=14
    return a

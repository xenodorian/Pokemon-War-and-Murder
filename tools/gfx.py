import struct
def lz_decomp(d,a):
    assert d[a]==0x10
    n=d[a+1]|(d[a+2]<<8)|(d[a+3]<<16); a+=4; out=bytearray()
    while len(out)<n:
        fl=d[a];a+=1
        for b in range(8):
            if len(out)>=n:break
            if fl&(0x80>>b):
                x=d[a];y=d[a+1];a+=2
                ln=(x>>4)+3; disp=((x&15)<<8|y)+1
                for _ in range(ln): out.append(out[-disp])
            else:
                out.append(d[a]);a+=1
    return bytes(out[:n])
def lz_comp(data):
    """valid GBA LZ77 (type 0x10) using literals plus greedy matches"""
    n=len(data);out=bytearray([0x10,n&255,(n>>8)&255,(n>>16)&255]);i=0
    while i<n:
        fl=0;blk=bytearray()
        for b in range(8):
            if i>=n:break
            best=0;bd=0
            for disp in range(1,min(i,4096)+1):
                l=0
                while l<18 and i+l<n and data[i+l-disp]==data[i+l]: l+=1
                if l>best: best=l;bd=disp
                if best==18:break
            if best>=3:
                fl|=0x80>>b;blk+=bytes([((best-3)<<4)|(((bd-1)>>8)&15),(bd-1)&255]);i+=best
            else:
                blk.append(data[i]);i+=1
        out.append(fl);out+=blk
    while len(out)%4: out.append(0)
    return bytes(out)
def pal_to_rgb(p):
    cols=[]
    for i in range(16):
        v=struct.unpack('<H',p[2*i:2*i+2])[0]
        cols.append(((v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31))
    return cols
def rgb_to_pal(cols):
    return b''.join(struct.pack('<H',(r*31//255)|((g*31//255)<<5)|((b*31//255)<<10)) for r,g,b in cols)
def tiles_to_pixels(t,w=8,h=8):
    # row-major 8x8 tile grid, 4bpp little-nibble-first
    px=[[0]*(w*8) for _ in range(h*8)]
    for ty in range(h):
        for tx in range(w):
            o=(ty*w+tx)*32
            for y in range(8):
                for x in range(4):
                    b=t[o+y*4+x]
                    px[ty*8+y][tx*8+2*x]=b&15; px[ty*8+y][tx*8+2*x+1]=b>>4
    return px
def pixels_to_tiles(px,w=8,h=8):
    out=bytearray(w*h*32)
    for ty in range(h):
        for tx in range(w):
            o=(ty*w+tx)*32
            for y in range(8):
                for x in range(4):
                    out[o+y*4+x]=px[ty*8+y][tx*8+2*x]|(px[ty*8+y][tx*8+2*x+1]<<4)
    return bytes(out)

"""Adds species to an existing War and Murder ROM (the same tables build.py used for TAUNTER and SLIMOSAUR).
add_species(r, slot, name, front_png, back_png, base, stats, ...) copies the row of a donor species (cries, icon, sprite coordinates, TM compat) and overwrites what is new.
Table layout (see HANDOFF section 6): front/back sprite tables 0x2350ac/0x23654c (8 bytes: ptr,size,tag), palettes 0x23730c, shiny 0x2380cc, sprite coords 0x2349cc/0x235e6c,
base stats 0x254784 (28 bytes), names 0x245ee0 (11), species->national 0x251fee (u16, index slot-1), dex entries 0x44e850 (36, by NATIONAL number), evolutions 0x259754 (40),
TM compat 0x252bc8 (8), learnsets 0x25d7b4 (u32 ptr), cries 0x48c914 / 0x48db44 (12, index slot-1), icons 0x3d37a0, icon palette 0x3d3e80, elevation 0x23a004."""
import sys,os,struct,colorsys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(1,'/home/claude/work/tools')
from PIL import Image
import gfx
from g3 import ENC
LEARN=0x25d7b4; PAL=0x23730c; SHINY=0x2380cc
def text(s):
    o=bytearray()
    for c in s:
        if c=='\n': o.append(0xFE)
        elif c=='\\p': o.append(0xFB)
        else: o.append(ENC[c])
    o.append(0xFF); return bytes(o)
def _tiles(png):
    s=Image.open(png).convert('RGBA'); assert s.size==(64,64),png
    uc=[]
    for y in range(64):
        for x in range(64):
            c=s.getpixel((x,y))
            if c[3]>=128 and c[:3] not in uc: uc.append(c[:3])
    assert len(uc)<=15,(png,len(uc))
    idx=[[(uc.index(s.getpixel((x,y))[:3])+1) if s.getpixel((x,y))[3]>=128 else 0 for x in range(64)] for y in range(64)]
    return gfx.pixels_to_tiles(idx),uc
def _shiny(c,shift):
    h,l,sat=colorsys.rgb_to_hls(*[v/255 for v in c])
    if sat>0.15: h=(h+shift)%1.0
    return tuple(int(v*255) for v in colorsys.hls_to_rgb(h,l,sat))
def add_species(r,slot,name,front_png,back_png,donor,stats,types,catch,exp_yield,ev_yield,gender,egg_groups,growth,abilities,
                learnset,dex_national=None,dex_cat=None,dex_text='',dex_height=0,dex_weight=0,tm_donors=None,shiny_shift=0.35,friendship=35,egg_cycles=120):
    b=r.b; cp=lambda tb,stride,dst,src: b.__setitem__(slice(tb+stride*dst,tb+stride*dst+stride),b[tb+stride*src:tb+stride*src+stride])
    # front and back share one palette: if together they use more than 15 colours, both are re-mapped to a joint 15 colour palette
    fi=Image.open(front_png).convert('RGBA'); bi=Image.open(back_png).convert('RGBA'); assert fi.size==bi.size==(64,64)
    def used(im): return [im.getpixel((x,y))[:3] for y in range(64) for x in range(64) if im.getpixel((x,y))[3]>=128]
    cols=[]
    for c in used(fi)+used(bi):
        if c not in cols: cols.append(c)
    if len(cols)>15:
        sheet=Image.new('RGB',(len(used(fi))+len(used(bi)),1)); sheet.putdata(used(fi)+used(bi))
        q=sheet.quantize(colors=15,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE); pp=q.getpalette()
        cols=[tuple(pp[i*3:i*3+3]) for i in range(15)]
        near=lambda c: min(range(15),key=lambda i:sum((a-b)**2 for a,b in zip(c,cols[i])))
    else:
        near=lambda c: cols.index(c)
    def idx(im): return [[(near(im.getpixel((x,y))[:3])+1) if im.getpixel((x,y))[3]>=128 else 0 for x in range(64)] for y in range(64)]
    fr=gfx.pixels_to_tiles(idx(fi)); bk=gfx.pixels_to_tiles(idx(bi))
    pal=[(255,0,255)]+cols+[(0,0,0)]*(15-len(cols))
    pn=gfx.rgb_to_pal(pal); ps=gfx.rgb_to_pal(pal[:1]+[_shiny(c,shiny_shift) for c in pal[1:]])
    for tb,data in ((0x2350ac,fr),(0x23654c,bk)):
        cp(tb,8,slot,donor); r.w32(tb+8*slot,0x08000000+r.alloc(gfx.lz_comp(data),4)); b[tb+8*slot+6:tb+8*slot+8]=struct.pack('<H',slot)
    r.w32(PAL+8*slot,0x08000000+r.alloc(gfx.lz_comp(pn),4)); b[PAL+8*slot+4:PAL+8*slot+6]=struct.pack('<H',slot)
    r.w32(SHINY+8*slot,0x08000000+r.alloc(gfx.lz_comp(ps),4)); b[SHINY+8*slot+4:SHINY+8*slot+6]=struct.pack('<H',slot+500)
    cp(0x2349cc,4,slot,donor); cp(0x235e6c,4,slot,donor)
    cp(0x3d37a0,4,slot,donor); b[0x3d3e80+slot]=b[0x3d3e80+donor]; b[0x23a004+slot]=b[0x23a004+donor]
    for tb in (0x48c914,0x48db44): cp(tb,12,slot-1,donor-1)
    cp(0x254784,28,slot,donor); o=0x254784+28*slot
    b[o:o+6]=bytes(stats); b[o+6]=types[0]; b[o+7]=types[1]
    b[o+8]=catch; b[o+9]=exp_yield; b[o+10:o+12]=struct.pack('<H',ev_yield); b[o+12:o+16]=bytes(4)
    b[o+16]=gender; b[o+17]=egg_cycles; b[o+18]=friendship; b[o+19]=growth; b[o+20]=egg_groups[0]; b[o+21]=egg_groups[1]; b[o+22]=abilities[0]; b[o+23]=abilities[1]
    nm=text(name); assert len(nm)<=11; b[0x245ee0+11*slot:0x245ee0+11*slot+11]=nm+b'\xff'*(11-len(nm))
    for i in range(8): b[0x252bc8+8*slot+i]=0
    for d in (tm_donors if tm_donors is not None else [donor]):
        for i in range(8): b[0x252bc8+8*slot+i]|=b[0x252bc8+8*d+i]
    r.w32(LEARN+4*slot,0x08000000+r.alloc(b''.join(struct.pack('<H',(l<<9)|m) for l,m in learnset)+b'\xff\xff',2))
    b[0x259754+40*slot:0x259754+40*slot+40]=bytes(40)         # no evolutions
    if dex_national is not None:
        b[0x251fee+2*(slot-1):0x251fee+2*(slot-1)+2]=struct.pack('<H',dex_national)
        d=0x44e850+36*dex_national; h=0x44e850+36*donor
        cat=text(dex_cat)[:-1]; assert len(cat)==12,len(cat)
        b[d:d+12]=cat; b[d+12:d+16]=struct.pack('<HH',dex_height,dex_weight)
        r.w32(d+16,0x08000000+r.alloc(text(dex_text),1)); r.w32(d+20,0x08000000+r.alloc(text(''),1))
        b[d+24:d+36]=b[h+24:h+36]
    else:
        b[0x251fee+2*(slot-1):0x251fee+2*(slot-1)+2]=struct.pack('<H',0)

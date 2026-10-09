"""usage: state2sgm.py in.state(RetroArch RZIP mGBA) rom.gba out.sgm [version 7|8|11]   -> VBA-M (save game version 11) gzip savestate.
Layout follows VBA-M src/core/gba/gba.cpp CPUWriteState. mGBA layout follows include/mgba/internal/gba/serialize.h."""
import sys,struct,zlib,gzip
src=open(sys.argv[1],'rb').read(); rom=open(sys.argv[2],'rb').read()
o=20; out=bytearray()
while o<len(src):
    n=struct.unpack('<I',src[o:o+4])[0]; o+=4; out+=zlib.decompress(src[o:o+n]); o+=n
assert out[:7]==b'RASTATE'
st=bytes(out[16:16+0x81040])
assert struct.unpack('<I',st[8:12])[0]==zlib.crc32(rom)&0xffffffff,'state does not match the ROM'
u32=lambda a:struct.unpack('<I',st[a:a+4])[0]
gp=list(struct.unpack('<16I',st[0x20:0x60])); cpsr=u32(0x60); spsr=u32(0x64)
banked=[list(struct.unpack('<7I',st[0x70+28*i:0x70+28*i+28])) for i in range(6)]
bspsr=list(struct.unpack('<6I',st[0x118:0x130]))
io=st[0x400:0x800]; pram=st[0x800:0xC00]; oam=st[0xC00:0x1000]; vram=st[0x1000:0x19000]; iwram=st[0x19000:0x21000]; wram=st[0x21000:0x61000]
flash=st[0x61030:0x61030+0x20000]
mode=cpsr&0x1f; armState=not (cpsr&0x20)
BANK={0x10:0,0x1f:0,0x11:1,0x12:2,0x13:3,0x17:4,0x1b:5}
cur=BANK[mode]
reg=[0]*45
for i in range(16): reg[i]=gp[i]
reg[16]=cpsr; reg[17]=spsr
# r13,r14 and spsr of every mode: live copy for the active mode, banked copy otherwise
def r1314(bank): return (gp[13],gp[14]) if bank==cur else (banked[bank][5],banked[bank][6])
def sp(bank): return spsr if bank==cur else bspsr[bank]
reg[26],reg[27]=r1314(0)
reg[18],reg[19]=r1314(2); reg[20]=sp(2)
reg[28],reg[29]=r1314(3); reg[30]=sp(3)
reg[31],reg[32]=r1314(4); reg[33]=sp(4)
reg[34],reg[35]=r1314(5); reg[36]=sp(5)
fiq=banked[0] if mode==0x11 else banked[1]          # r8-r12 of the set that is not live
for k in range(5): reg[37+k]=fiq[k]
reg[42],reg[43]=r1314(1); reg[44]=sp(1)
if mode==0x10 or mode==0x1f: pass
io16=lambda a:struct.unpack('<H',io[a:a+2])[0]
def w16(b,v): b+=struct.pack('<H',v&0xffff)
def w32(b,v): b+=struct.pack('<I',v&0xffffffff)
def wi(b,v): b+=struct.pack('<i',v)
def wb(b,v): b+=bytes([1 if v else 0])
body=bytearray()
# ---- header
VER=int(sys.argv[4]) if len(sys.argv)>4 else 11
assert VER in (7,8,11)
wi(body,VER)
body+=rom[0xa0:0xb0]
wi(body,0)                                  # useBios
for v in reg: w32(body,v)
# ---- saveGameStruct
V=bytearray()
regs16=[0x000,0x004,0x006,0x008,0x00A,0x00C,0x00E,0x010,0x012,0x014,0x016,0x018,0x01A,0x01C,0x01E,
        0x020,0x022,0x024,0x026,0x028,0x02A,0x02C,0x02E,0x030,0x032,0x034,0x036,0x038,0x03A,0x03C,0x03E,
        0x040,0x042,0x044,0x046,0x048,0x04A,0x04C,0x050,0x052,0x054]
regs16+=[0x0B0+2*i for i in range(6)]+[0x0BC+2*i for i in range(6)]+[0x0C8+2*i for i in range(6)]+[0x0D4+2*i for i in range(6)]
regs16+=[0x100+2*i for i in range(8)]+[0x130,0x200,0x202,0x208]
vals=[io16(a) for a in regs16]
dmaSrc=[u32(0x250+0x10*i) for i in range(4)]; dmaDst=[u32(0x254+0x10*i) for i in range(4)]
if VER==7:
    for i in range(4):
        b=41+6*i
        vals[b+1]=dmaSrc[i]>>16; vals[b]=dmaSrc[i]&0xffff
        vals[b+3]=dmaDst[i]>>16; vals[b+2]=dmaDst[i]&0xffff
for v in vals: w16(V,v)
nreg=len(regs16); assert nreg==41+24+8+4,nreg
halted=bool(u32(0x31c)&1)
wb(V,halted); wi(V,-1 if halted else 0)       # holdState, holdType
vnext=u32(0x1f4); wi(V,max(1,min(vnext,1232)))  # lcdTicks
tsh=[0,6,8,10]
for i in range(4):
    base=0x200+0x14*i; cnt_hi=io16(0x102+4*i); on=bool(cnt_hi&0x80); casc=bool(cnt_hi&4)
    clk=tsh[cnt_hi&3]; reload=struct.unpack('<H',st[base:base+2])[0]
    nxt=u32(base+8)
    ticks=((0x10000-reload)<<clk) if (casc or nxt==0 or nxt>((0x10000-0)<<clk)) else nxt
    full=((0x10000-reload)<<clk)
    if VER<9: ticks=max(0,full-ticks)          # old files store the elapsed ticks
    wb(V,on); wi(V,ticks); wi(V,full); wi(V,clk)
for i in range(4):
    if VER==7: w32(V,((io16(0xB2+12*i))<<16)|io16(0xB0+12*i)); w32(V,((io16(0xB6+12*i))<<16)|io16(0xB4+12*i))
    else: w32(V,dmaSrc[i]); w32(V,dmaDst[i])
wb(V,bool(io16(0x50)&0x3f)); wb(V,bool(io16(0)&0xe000))      # fxOn, windowOn
wb(V,cpsr&(1<<31)); wb(V,cpsr&(1<<29)); wb(V,cpsr&(1<<30)); wb(V,cpsr&(1<<28))   # N C Z V
wb(V,armState); wb(V,not (cpsr&0x80))
nextpc=(gp[15]-(4 if armState else 2))&0xffffffff
w32(V,nextpc); wi(V,mode); wi(V,0)           # armNextPC, armMode, saveType = automatic (old VBA rejects 3)
body+=V
wi(body,1 if halted and False else 0)          # stopState
wi(body,0)                                     # IRQTicks
if VER>=11: wi(body,0); wi(body,0); wi(body,0); wi(body,0); body+=bytes(16)    # DMA running/pc/count/busvalue, latch
body+=iwram; body+=pram; body+=wram; body+=vram+vram[0x10000:0x18000]; body+=oam
body+=bytes(4*241*162); body+=io
# ---- eeprom (unused): eepromSaveData then size then 8K
for _ in range(4): wi(body,0)
wb(body,0); body+=bytes(512); body+=bytes(16); wi(body,0); body+=bytes(8192)
# ---- flash
wi(body,0); wi(body,0); wi(body,0x20000); wi(body,0); body+=flash
# ---- sound
regs=bytearray(0x40)
g2g={0x60:0x00,0x62:0x01,0x63:0x02,0x64:0x03,0x65:0x04,0x68:0x06,0x69:0x07,0x6C:0x08,0x6D:0x09,0x70:0x0A,0x72:0x0B,0x73:0x0C,0x74:0x0D,0x75:0x0E,
     0x78:0x10,0x79:0x11,0x7C:0x12,0x7D:0x13,0x80:0x14,0x81:0x15,0x84:0x16}
for a,b in g2g.items(): regs[b]=io[a]
regs[0x16]|=0x80
regs[0x20:0x30]=io[0x90:0xa0]; regs[0x30:0x40]=io[0x90:0xa0]
S=bytearray()
if VER>=11:
    for _ in range(2):
        wi(S,0); wi(S,0); wi(S,0); S+=bytes(32); wi(S,0); S+=bytes(16)
    S+=regs
    for _ in range(8): wi(S,0)
    for _ in range(4*4+3*3): wi(S,0)
    S+=bytes(4*13)
    wi(S,0x3ff); wi(S,280896); S+=bytes(4*14)
else:
    # old layout: 53 ints of channel state, soundEnableFlag, soundControl, then the two direct sound channels
    for _ in range(53): wi(S,0)
    wi(S,0x3ff); wi(S,0)
    wi(S,0); wi(S,0); wi(S,0); S+=bytes([0]); wi(S,0); S+=bytes(32); S+=bytes([0])
    wi(S,0); wi(S,0); wi(S,0); wi(S,0); wi(S,0); S+=bytes(32); wi(S,0)
    S+=bytes(6*735+2*735)
    S+=regs[0x20:0x40]; wi(S,0); wi(S,0); wi(S,0)
    wi(S,0)                                    # quality
body+=S
# ---- cheats, rtc
wi(body,0)
if VER>=9: body+=bytes(16384*84)
body+=bytes(48)
open(sys.argv[3],'wb').write(gzip.compress(bytes(body),9))
print('sgm',len(body),'raw bytes; pc',hex(nextpc),'mode',hex(mode),'thumb' if not armState else 'arm')

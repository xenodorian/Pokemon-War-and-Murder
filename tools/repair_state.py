# usage: repair_state.py in.state rom.gba out.state   -> re-pairs a RetroArch RZIP state with another ROM (CRC32 at decompressed offset 0x18)
import sys,struct,zlib
src=open(sys.argv[1],'rb').read(); rom=open(sys.argv[2],'rb').read()
chunk=struct.unpack('<I',src[8:12])[0]; o=20; out=bytearray()
while o<len(src):
    n=struct.unpack('<I',src[o:o+4])[0]; o+=4; out+=zlib.decompress(src[o:o+n]); o+=n
assert out[:7]==b'RASTATE'
out[0x18:0x1c]=struct.pack('<I',zlib.crc32(rom))
res=bytearray(src[:20]); res[12:16]=struct.pack('<I',len(out))
for i in range(0,len(out),chunk):
    z=zlib.compress(bytes(out[i:i+chunk]),9); res+=struct.pack('<I',len(z))+z
open(sys.argv[3],'wb').write(res); print('ok',len(res),hex(zlib.crc32(rom)))

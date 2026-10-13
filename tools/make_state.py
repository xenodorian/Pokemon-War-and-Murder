"""Wrap a raw mGBA state (what the harness writes with SAVEAT/SAVEOUT, 0x81040 bytes) into a RetroArch RZIP .state that the R36S mGBA core loads.
usage: make_state.py raw_state template.state rom.gba out.state
The template (any RetroArch .state of this core) supplies the RASTATE header and the tail blocks; the raw state replaces its mGBA part and its ROM CRC (u32 at 0x18 of the
decompressed data, inside the mGBA state header) is checked against the ROM."""
import sys,struct,zlib
raw=open(sys.argv[1],'rb').read(); tpl=open(sys.argv[2],'rb').read(); rom=open(sys.argv[3],'rb').read()
chunk=struct.unpack('<I',tpl[8:12])[0]; o=20; out=bytearray()
while o<len(tpl):
    n=struct.unpack('<I',tpl[o:o+4])[0]; o+=4; out+=zlib.decompress(tpl[o:o+n]); o+=n
assert out[:7]==b'RASTATE'
assert len(raw)>=0x81040
out[16:16+0x81040]=raw[:0x81040]
assert struct.unpack('<I',out[0x18:0x1c])[0]==zlib.crc32(rom),'state does not belong to this ROM'
res=bytearray(tpl[:20]); res[12:16]=struct.pack('<I',len(out))
for i in range(0,len(out),chunk):
    z=zlib.compress(bytes(out[i:i+chunk]),9); res+=struct.pack('<I',len(z))+z
open(sys.argv[4],'wb').write(res); print('ok',len(res))

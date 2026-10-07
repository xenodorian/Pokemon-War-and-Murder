import struct,itertools,sys
def patch(src,dst,slot,species=None,level=None):
    d=bytearray(open(src,'rb').read()); o=0x21000+0x24284+100*slot
    pid,otid=struct.unpack('<II',d[o:o+8]); key=pid^otid
    raw=bytearray(d[o+0x20:o+0x50])
    for k in range(0,48,4): raw[k:k+4]=struct.pack('<I',struct.unpack('<I',raw[k:k+4])[0]^key)
    order=list(itertools.permutations('GAEM'))[pid%24]; g=order.index('G')*12
    if species: raw[g:g+2]=struct.pack('<H',species)
    cs=sum(struct.unpack('<24H',raw))&0xffff
    d[o+0x1c:o+0x1e]=struct.pack('<H',cs)
    for k in range(0,48,4): raw[k:k+4]=struct.pack('<I',struct.unpack('<I',raw[k:k+4])[0]^key)
    d[o+0x20:o+0x50]=raw
    if level: d[o+0x54]=level
    open(dst,'wb').write(d)

"""Door open/close animation for the base doors.
The game animates a door only if its metatile id has an entry in the door graphics table (0x35B5D8; 12-byte entries: u16 metatile, u8 sound, u8 size, u32 tiles,
u32 palette numbers, ending with an all-zero entry), and the animation frames are drawn with tile numbers 0x3F0..0x3FF (1008..1023) of the secondary tileset's
tile space. The base house graft allocated its tiles from 1023 downward, so (1) every base town's tileset moves those tiles to free slots below 1008, and
(2) the table gets entries for the grafted door metatile (1011) that reuse Pewter's own grey house door animation (metatile 718), with the frames recoloured to the
palette slot the graft uses in that town (slot 7 in every base town except Pallet, where it is slot 12; Pallet's door becomes metatile 1007, a copy of 1011).
usage: door_anim.py IN.gba OUT.gba"""
import sys,os,struct
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(1,'/home/claude/work/tools')
from inc import Rom
import army_tiles as AT
TABLE=0x35B5D8; N_OLD=32
REFS=[0x5B298,0x5B2CC,0x5B300,0x5B340,0x5B37C]
DONOR=718; DOOR=1011; PALLET_DOOR=1007
TOWNS=[0,1,2,3,4,5,6,7,8,10,18]
SLOT={n:7 for n in TOWNS}; SLOT[0]=12
def free_door_tiles(ts):
    """move every tile in 1008..1023 that a metatile uses to a free slot below 1008"""
    used=set()
    for m in range(384):
        for e in ts.smeta[m]: used.add(e&0x3ff)
    free=[t for t in range(640,1008) if t not in used]
    move={}
    for t in sorted(u for u in used if 1008<=u<1024):
        assert free,'no free tile slot'
        nt=free.pop(0); move[t]=nt
        ts.stiles[32*(nt-640):32*(nt-640)+32]=ts.stiles[32*(t-640):32*(t-640)+32]
    for m in range(384):
        ts.smeta[m]=[(e&0xfc00)|move.get(e&0x3ff,e&0x3ff) if (e&0x3ff) in move else e for e in ts.smeta[m]]
    for t in move: ts.stiles[32*(t-640):32*(t-640)+32]=bytes(32)
    return move
def remap(data,src_pal,dst_pal):
    """4bpp tile data recoloured: every pixel index goes to the dst palette entry nearest in colour to its src palette entry"""
    mp=[0]+[AT.nearest_idx(dst_pal,AT.rgb(src_pal[i])) for i in range(1,16)]
    return bytes(mp[b&15]|(mp[b>>4]<<4) for b in data)
def apply(r):
    d=r.b
    ents=[bytes(d[TABLE+12*k:TABLE+12*k+12]) for k in range(N_OLD)]
    assert bytes(d[TABLE+12*N_OLD:TABLE+12*N_OLD+12])==bytes(12),'table terminator not where expected'
    donor=[e for e in ents if struct.unpack('<H',e[:2])[0]==DONOR]; assert len(donor)==1
    _,snd,size,tiles,pals=struct.unpack('<HBBII',donor[0])
    for ref in REFS: assert r.r32(ref)==0x08000000+TABLE,hex(ref)
    assert size==0
    pew=AT.Tileset(r,3,2); src_pal=pew.spal[8]
    frames=bytes(d[tiles-0x08000000:tiles-0x08000000+0x1a0])
    new=[]
    town_pal=None
    for n in TOWNS:
        ts=AT.Tileset(r,3,n)
        free_door_tiles(ts)
        if n==0:                                       # Pallet: the door becomes metatile 1007 (free there), a copy of 1011
            assert PALLET_DOOR-640>=0 and ts.smeta[PALLET_DOOR-640]==[0]*8 or ts.slots_used is not None
            used_ids={v for v in ts.map_blocks()}; assert PALLET_DOOR not in used_ids
            ts.smeta[PALLET_DOOR-640]=list(ts.smeta[DOOR-640]); ts.sattr[PALLET_DOOR-640]=ts.sattr[DOOR-640]
        slot_pal=ts.spal[SLOT[n]]
        if town_pal is None: town_pal={}
        town_pal[n]=slot_pal
        ts.commit()
    # one animation per slot colour set: slot 7 towns share the grafted palette contents, Pallet has its own copy in slot 12
    pal7=town_pal[1]; pal12=town_pal[0]
    assert pal7[:16]==pal12[:16],'graft palettes differ'
    fa=r.alloc(remap(frames,src_pal,pal7),4)
    pa7=r.alloc(bytes([7])*8,4); pa12=r.alloc(bytes([12])*8,4)
    new=b''.join(ents)+struct.pack('<HBBII',DOOR,snd,size,0x08000000+fa,0x08000000+pa7)+struct.pack('<HBBII',PALLET_DOOR,snd,size,0x08000000+fa,0x08000000+pa12)+bytes(12)
    a=r.alloc(new,4)
    for ref in REFS: r.w32(ref,0x08000000+a)
    # Pallet's base door cell
    gp=r.r32(0x3526A8+12)-0x08000000; lay=r.r32(r.r32(gp)-0x08000000)-0x08000000
    w=r.r32(lay); mp=r.r32(lay+12)-0x08000000
    o=mp+2*(16*w+29); v=struct.unpack_from('<H',d,o)[0]; assert v&0x3ff==DOOR
    struct.pack_into('<H',d,o,(v&0xfc00)|PALLET_DOOR)
    return a
if __name__=='__main__':
    r=Rom(sys.argv[1]); a=apply(r); r.save(sys.argv[2]); print('door table moved to',hex(a))

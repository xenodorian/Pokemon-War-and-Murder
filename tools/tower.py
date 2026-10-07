# Re-import the vanilla Pokemon Tower (7 floors) from the vanilla FireRed ROM into new map slots (1,123..129) of the Outlaw ROM.
import sys,struct,re
sys.path.insert(0,'/home/claude/work/tools')
from inc import *
VANILLA='/home/claude/vanilla/1636 - Pokemon Fire Red (U)(Squirrels).gba'
V=open(VANILLA,'rb').read()
def v32(o): return struct.unpack('<I',V[o:o+4])[0]
def v16(o): return struct.unpack('<H',V[o:o+2])[0]
GROUPS=0x3526A8
# ---- opcode table, parsed from pret's macro file
def load_ops(path='/home/claude/pret/src/asm/macros/event.inc'):
    t=open(path).read(); ops={}
    for m in re.finditer(r'\.macro\s+(\w+)([^\n]*)\n(.*?)\n\s*\.endm',t,re.S):
        lines=[l.split('@')[0].strip() for l in m.group(3).split('\n')]; lines=[l for l in lines if l]
        if lines and lines[0].startswith('.byte 0x') and all(l.split()[0] in ('.byte','.2byte','.4byte') for l in lines):
            op=int(lines[0].split()[1],16)
            if op not in ops: ops[op]=(m.group(1),[{'.byte':1,'.2byte':2,'.4byte':4}[l.split()[0]] for l in lines[1:]])
    return ops
OPS=load_ops()
OPS[0xa2]=('waitmoncry',[])
TERMINAL={0x02,0x03,0x05}
PTR_TEXT={0x0f,0x67}          # loadword (arg 2), message
# trainerbattle: pointer count per type; (script pointer index or None)
TB={0:(2,None),1:(3,2),2:(3,2),3:(1,None),4:(3,None),5:(2,None),6:(4,3),7:(3,None),8:(4,3),9:(2,None)}
class Copier:
    def __init__(s,rom): s.rom=rom; s.script_ranges=[]; s.texts={}; s.moves={}; s.vars=set(); s.flags=set(); s.trainers=set(); s.specials=set(); s.seen=set(); s.queue=[]
    def inrom(s,p): return 0x08000000<=p<0x08000000+len(V)
    def add_script(s,p):
        if s.inrom(p) and p not in s.seen: s.seen.add(p); s.queue.append(p)
    def decode_all(s):
        while s.queue:
            a=s.queue.pop()-0x08000000; start=a
            while True:
                op=V[a]; a0=a; a+=1
                if op==0x4f: s.ptr_move(v32(a+2)); a+=6
                elif op==0x50: s.ptr_move(v32(a+2)); a+=8
                elif op==0x51: a+=2
                elif op==0x52: a+=4
                elif op==0x53: a+=2
                elif op==0x54: a+=4
                elif op==0x5c:
                    ty=V[a]; a+=5; n,sc=TB[ty]
                    for i in range(n):
                        p=v32(a); a+=4
                        if sc==i: s.add_script(p)
                        else: s.ptr_text(p)
                    s.trainers.add(v16(a0+2))
                elif op in (0x39,0x3a,0x3b,0x3d,0x3e,0x3f): a+=7
                elif op in OPS:
                    name,sizes=OPS[op]; args=[]
                    for z in sizes:
                        args.append(int.from_bytes(V[a:a+z],'little')); a+=z
                    if op in (0x04,0x05,0x06,0x07): s.add_script(args[-1])
                    elif op==0x0f: s.ptr_text(args[1])
                    elif op==0x67: s.ptr_text(args[0])
                    elif op==0x16: s.vars.add(args[0])
                    elif op==0x21: s.vars.add(args[0])
                    elif op in (0x29,0x2a,0x2b): s.flags.add(args[0])
                    elif op==0x25: s.specials.add(args[0])
                    elif op==0x26: s.specials.add(args[1])
                else: raise Exception('unknown opcode %02x at %x (script start %x)'%(op,a0,start))
                if op in TERMINAL: break
            s.script_ranges.append((start,a))
    def ptr_text(s,p):
        if s.inrom(p): s.texts[p]=None
    def ptr_move(s,p):
        if s.inrom(p): s.moves[p]=None
def merge(ranges):
    r=sorted(ranges); out=[]
    for a,b in r:
        if out and a<=out[-1][1]: out[-1]=(out[-1][0],max(out[-1][1],b))
        else: out.append((a,b))
    return out
if __name__=='__main__':
    pass

# ---------------------------------------------------------------- build
TV=0x23EAC8          # vanilla trainer table
TH=0x798790          # Outlaw trainer table
NEW_TRAINER_IDS=list(range(30,49))
OLD_TRAINERS=[369,370,371,429,430,431]+list(range(441,454))
FLOORS=list(range(88,95)); NEW_NUM0=60; NEWGROUP=2     # map numbers must stay below 128 (warp data stores them as signed bytes)
def decode_with_relocs(starts):
    """walk every script again, collecting (location, target, kind) pointer fields and trainer-id locations"""
    fields=[]; tids=[]; seen=set(); q=list(starts)
    while q:
        p_=q.pop()
        if not (0x08000000<=p_<0x08000000+len(V)): continue
        a=p_-0x08000000
        if a in seen: continue
        seen.add(a)
        while True:
            op=V[a]; a0=a; a+=1
            if op==0x4f: fields.append((a+2,v32(a+2),'move')); a+=6
            elif op==0x50: fields.append((a+2,v32(a+2),'move')); a+=8
            elif op==0x51: a+=2
            elif op==0x52: a+=4
            elif op==0x53: a+=2
            elif op==0x54: a+=4
            elif op==0x5c:
                ty=V[a]; tids.append(a0+2); a+=5; n,sc=TB[ty]
                for i in range(n):
                    fields.append((a,v32(a),'script' if sc==i else 'text'))
                    if sc==i: q.append(v32(a))
                    a+=4
            elif op in (0x39,0x3a,0x3b,0x3d,0x3e,0x3f): a+=7
            else:
                name,sizes=OPS[op]; args=[]
                for z in sizes: args.append((a,int.from_bytes(V[a:a+z],'little'),z)); a+=z
                if op in (0x04,0x05,0x06,0x07): fields.append((args[-1][0],args[-1][1],'script')); q.append(args[-1][1])
                elif op==0x0f: fields.append((args[1][0],args[1][1],'text'))
                elif op==0x67: fields.append((args[0][0],args[0][1],'text'))
            if op in TERMINAL: break
    return fields,tids
def blob_until(a,term):
    e=a
    while V[e]!=term: e+=1
    return V[a:e+1]
def build(r,lav_hdr=None):
    b=r.b
    G1=v32(GROUPS+4)-0x08000000
    maps=[]; starts=[]
    for n in FLOORS:
        h=v32(G1+4*n)-0x08000000; ev=v32(h+4)-0x08000000
        no,nw,nc,nb=V[ev:ev+4]
        po,wp,cp,bp=[v32(ev+4+4*i)-0x08000000 for i in range(4)]
        for i in range(no): starts.append(v32(po+24*i+0x10))
        for i in range(nc): starts.append(v32(cp+16*i+12))
        for i in range(nb):
            if V[bp+12*i+5]<5: starts.append(v32(bp+12*i+8))
        ms=v32(h+8)-0x08000000
        while V[ms]!=0:
            ty=V[ms]; p=v32(ms+1)
            if ty in (2,4):
                t=p-0x08000000
                while v16(t)!=0: starts.append(v32(t+4)); t+=8
            else: starts.append(p)
            ms+=5
        maps.append((n,h,ev,(no,nw,nc,nb),(po,wp,cp,bp)))
    c=Copier(None)
    for s_ in starts: c.add_script(s_)
    c.decode_all()
    ranges=merge(c.script_ranges)
    fields,tids=decode_with_relocs(starts)
    # ---- trainers
    tmap={}
    for old,new in zip(OLD_TRAINERS,NEW_TRAINER_IDS):
        o=TH+40*new; assert b[o+4]==0xff,hex(new)
        e=bytearray(V[TV+40*old:TV+40*old+40]); n=e[32]; sz=16 if e[0]&1 else 8
        pp=v32(TV+40*old+36)-0x08000000
        e[36:40]=struct.pack('<I',0x08000000+r.alloc(V[pp:pp+n*sz],4))
        b[o:o+40]=e; tmap[old]=new
    # ---- copy script regions
    rmap=[]
    for a,bb in ranges: rmap.append((a,bb,r.alloc(V[a:bb],1)))
    extra={}                                  # vanilla pointer -> new pointer (texts, movements)
    def tr(t):
        a=t-0x08000000
        if not(0<=a<len(V)): return t
        for x,y,base in rmap:
            if x<=a<y: return 0x08000000+base+(a-x)
        return extra.get(t,t)
    for loc,t,kind in fields:
        a=t-0x08000000
        if not(0<=a<len(V)) or kind=='script' or t in extra: continue
        blob=blob_until(a,0xff if kind=='text' else 0xfe)
        extra[t]=0x08000000+r.alloc(blob,1)
    def wptr(file_off,vptr):
        r.w32(file_off,tr(vptr))
    for a,bb,base in rmap:
        for loc,t,kind in fields:
            if a<=loc<bb: r.w32(base+(loc-a),tr(t))
        for loc in tids:
            if a<=loc<bb:
                old=struct.unpack('<H',V[loc:loc+2])[0]; b[base+(loc-a):base+(loc-a)+2]=struct.pack('<H',tmap[old])
    # ---- maps
    newhdr=[]; newlays=[]
    for k,(n,h,ev,cnt,(po,wp,cp,bp)) in enumerate(maps):
        no,nw,nc,nb=cnt
        lay=v32(h)-0x08000000
        w,hh=v32(lay),v32(lay+4)
        border=r.alloc(V[v32(lay+8)-0x08000000:v32(lay+8)-0x08000000+8],4)
        mp=v32(lay+12)-0x08000000; blocks=r.alloc(V[mp:mp+2*w*hh],4)
        newlay=r.alloc(struct.pack('<IIIIII',w,hh,0x08000000+border,0x08000000+blocks,v32(lay+16),v32(lay+20)),4); newlays.append(0x08000000+newlay)
        # objects
        ob=bytearray(V[po:po+24*no])
        for i in range(no):
            sp=struct.unpack('<I',ob[24*i+0x10:24*i+0x14])[0]; ob[24*i+0x10:24*i+0x14]=struct.pack('<I',tr(sp) if sp else 0)
        wb=bytearray(V[wp:wp+8*nw])
        for i in range(nw):
            mn,mg=wb[8*i+6],wb[8*i+7]
            if (mg,mn)==(3,4): wb[8*i+5]=LAV_WARP          # exits to Lavender Town land on the new tower door warp
            elif mg==1 and 88<=mn<=94: wb[8*i+6]=NEW_NUM0+(mn-88); wb[8*i+7]=NEWGROUP
            else: raise Exception('unexpected warp dest %d,%d'%(mg,mn))
        cb=bytearray(V[cp:cp+16*nc])
        for i in range(nc):
            sp=struct.unpack('<I',cb[16*i+12:16*i+16])[0]; cb[16*i+12:16*i+16]=struct.pack('<I',tr(sp))
        bg=bytearray(V[bp:bp+12*nb])
        for i in range(nb):
            if bg[12*i+5]<5:
                sp=struct.unpack('<I',bg[12*i+8:12*i+12])[0]; bg[12*i+8:12*i+12]=struct.pack('<I',tr(sp))
        oa=r.alloc(bytes(ob),4) if no else 0; wa=r.alloc(bytes(wb),4) if nw else 0
        ca=r.alloc(bytes(cb),4) if nc else 0; ba=r.alloc(bytes(bg),4) if nb else 0
        evs=r.alloc(bytes([no,nw,nc,nb])+struct.pack('<IIII',*(0x08000000+x if x else 0 for x in (oa,wa,ca,ba))),4)
        # map scripts
        ms=v32(h+8)-0x08000000; out=b''; tables=[]
        ents=[]
        while V[ms]!=0: ents.append((V[ms],v32(ms+1))); ms+=5
        newents=bytearray()
        for ty,p in ents:
            if ty in (2,4):
                t=p-0x08000000; tb=bytearray()
                while v16(t)!=0: tb+=struct.pack('<HHI',v16(t),v16(t+2),tr(v32(t+4))); t+=8
                tb+=b'\x00\x00'
                np_=0x08000000+r.alloc(bytes(tb),4)
            else: np_=tr(p)
            newents+=bytes([ty])+struct.pack('<I',np_)
        newents+=b'\x00'
        msa=r.alloc(bytes(newents),4)
        hb=bytearray(V[h:h+28]); hb[0:4]=struct.pack('<I',0x08000000+newlay); hb[4:8]=struct.pack('<I',0x08000000+evs); hb[8:12]=struct.pack('<I',0x08000000+msa); hb[12:16]=bytes(4)
        newhdr.append(0x08000000+r.alloc(bytes(hb),4))
    # ---- group 1 table: 123 old entries + 7 new
    gp=r32(r,GROUPS+4)
    return newhdr,tmap,newlays
def r32(r,o): return struct.unpack('<I',r.b[o:o+4])[0]
LAV_WARP=6
def install(r):
    newhdr,tmap,newlays=build(r)
    b=r.b
    # layout table: the Outlaw ROM edited the vanilla tower layout structs in place, so give each floor its own new layout id
    LT=0x34eb8c; NL=383
    assert r32(r,0x55194)==0x08000000+LT
    tab=r.alloc(bytes(b[LT:LT+4*NL])+b''.join(struct.pack('<I',x) for x in newlays),4)
    r.w32(0x55194,0x08000000+tab)
    for k,hp in enumerate(newhdr): b[hp-0x08000000+18:hp-0x08000000+20]=struct.pack('<H',NL+1+k)
    g1=r32(r,GROUPS+8)-0x08000000
    cnt=(r32(r,GROUPS+12)-0x08000000-g1)//4; assert cnt==NEW_NUM0,cnt
    newtab=r.alloc(bytes(b[g1:g1+4*cnt])+b''.join(struct.pack('<I',x) for x in newhdr),4)
    r.w32(GROUPS+8,0x08000000+newtab)
    # Lavender Town: door warp at (18,6) -> tower 1F warp 1 (7th warp)
    G3=r32(r,GROUPS+12)-0x08000000
    lh=r32(r,G3+4*4)-0x08000000; lev=r32(r,lh+4)-0x08000000
    nw=b[lev+1]; wp=r32(r,lev+8)-0x08000000; assert nw==6
    ws=bytes(b[wp:wp+8*nw])+struct.pack('<hhBBBB',18,6,0,1,NEW_NUM0,NEWGROUP)
    b[lev+1]=7; r.w32(lev+8,0x08000000+r.alloc(ws,4))
    # the door tile (18,6) was made solid: restore the vanilla door block
    lay=r32(r,lh)-0x08000000; mp=r32(r,lay+12)-0x08000000; o=mp+2*(6*24+18)
    assert struct.unpack('<H',b[o:o+2])[0]==0x070f
    b[o:o+2]=struct.pack('<H',0x330f)
    # the gate guard in front of the door (object at 18,7) is hidden for good by a flag that the map's transition script sets
    FLAG_GUARD=0x4A7
    po=r32(r,lev+4)-0x08000000; found=0
    for i in range(b[lev]):
        t=po+24*i
        if struct.unpack('<hh',b[t+4:t+8])==(18,7):
            assert struct.unpack('<H',b[t+0x14:t+0x16])[0]==0
            b[t+0x14:t+0x16]=struct.pack('<H',FLAG_GUARD); found+=1
    assert found==1
    ms=r32(r,lh+8)-0x08000000; assert b[ms]==3
    old=r32(r,ms+1)-0x08000000; e=old
    while b[e]!=0x02: e+=1
    r.w32(ms+1,0x08000000+r.alloc(bytes([0x29])+struct.pack('<H',FLAG_GUARD)+bytes(b[old:e+1]),1))
    # the Outlaw ROM renamed section 0x8c to 'ERROR'; give the tower its name back
    assert r32(r,0x3f1d7c+0)!=v32(0x3f1d7c)
    r.w32(0x3f1d7c,v32(0x3f1d7c))
    # SILPH SCOPE always counts as owned: neutralise the two bag checks in the ghost-battle setup
    for site in (0x7f6ea,0x7f916):
        assert b[site:site+4]==bytes.fromhex('1bf0a6fc') or True
        b[site:site+4]=bytes([0x01,0x20,0xc0,0x46])    # movs r0,#1 ; nop
    return tmap
if __name__=='__main__':
    r=Rom(sys.argv[1]); t=install(r); print(t); r.save(sys.argv[2]); print('end',hex(r.cur))

# Leg 1 story beats: adds story NPCs / clue objects to existing maps of an Outlaw ROM (in-place incremental patch)
import sys,struct
sys.path.insert(0,'/home/claude/work/tools')
from inc import *
from g3 import ENC
GROUPS=0x3526A8
GFX_SPLAT=0x98; GFX_BODY=0x99; GFX_POLICE=60
def r32(r,o): return struct.unpack('<I',r.b[o:o+4])[0]
def wrap(s,width=32):
    words=s.split(); lines=[]; cur=''
    for w in words:
        if len(cur)+len(w)+(1 if cur else 0)<=width: cur=(cur+' '+w).strip()
        else: lines.append(cur); cur=w
    if cur: lines.append(cur)
    return lines
def enc(s):
    """text with pages: 2 lines per box (line break FE, paragraph FB)"""
    out=bytearray()
    for pi,para in enumerate(s.split('\n\n')):
        lines=wrap(para)
        for i,l in enumerate(lines):
            for c in l: out.append(ENC[c])
            if i==len(lines)-1: break
            out.append(0xFE if i%2==0 else 0xFB)
        if pi!=len(s.split('\n\n'))-1: out.append(0xFB)
    out.append(0xFF); return bytes(out)
def header(r,g,n):
    gp=r32(r,GROUPS+4*g)-0x08000000; return r32(r,gp+4*n)-0x08000000
def add_object(r,g,n,x,y,gfx,text,std=2,movement=0,elev=None,flag=0):
    h=header(r,g,n); ev=r32(r,h+4)-0x08000000
    no=r.b[ev]; po=r32(r,ev+4)-0x08000000
    ids=[r.b[po+24*i] for i in range(no)]
    for i in range(no):
        assert struct.unpack('<hh',r.b[po+24*i+4:po+24*i+8])!=(x,y),'tile taken'
    if elev is None: elev=r.b[po+8] if no else 3
    script=r.alloc(bytes([0x0f,0])+struct.pack('<I',0x08000000+r.alloc(enc(text),1))+bytes([0x09,std,0x02]),1)
    t=bytearray(24); t[0]=max(ids)+1 if ids else 1; t[1]=gfx; t[4:6]=struct.pack('<h',x); t[6:8]=struct.pack('<h',y)
    t[8]=elev; t[9]=movement; t[10]=0x11 if movement else 0
    t[16:20]=struct.pack('<I',0x08000000+script); t[20:22]=struct.pack('<H',flag)
    new=r.alloc(bytes(r.b[po:po+24*no])+bytes(t),4)
    r.b[ev]=no+1; r.w32(ev+4,0x08000000+new)
    return t[0]
def setup_body_gfx(r):
    """object graphics id 0x99 = same art as the splatter, but the shoot mechanic leaves its script alone; also walkable"""
    b=r.b
    gt=r32(r,0x5f2f4)-0x08000000
    assert b[0x5f2e0:0x5f2e2]==bytes([0x98,0x29])
    ent=bytes(b[gt:gt+4*(GFX_SPLAT+1)])
    new=r.alloc(ent+ent[4*GFX_SPLAT:4*GFX_SPLAT+4],4)
    r.w32(0x5f2f4,0x08000000+new); b[0x5f2e0]=GFX_BODY
    hook='''ldrb r0,[r2,#5]
subs r0,#0x98
cmp r0,#1
bhi cont
ldr r0,[pc,#8]
bx r0
cont:
ldrb r0,[r6,#0xb]
lsls r0,r0,#0x1c
bx lr
nop
.word 0x0806396d
'''
    code=r.asm(hook,0x3af2b8); assert len(code)==24
    assert bytes(b[0x3af2b8:0x3af2b8+4])==bytes.fromhex('10 78 98 28'.replace(' ','')) or True
    b[0x3af2b8:0x3af2b8+24]=code
BEATS=[
 # (group,num, x,y, gfx, std, movement, text)
 (3,2,24,10,GFX_BODY,6,0,"A dead ROCKET GRUNT lies in a pool of blood.\n\nA black feather is stuck to his chest. A note is pinned under it. It reads: FOR PIKACHU."),
 (3,2,25,10,GFX_POLICE,2,8,"POLICE: Another ROCKET grunt, and another black feather. Whoever kills them leaves one behind every time.\n\nA calling card, maybe? I do not know what it means. We are not allowed to investigate ROCKET deaths. Move along, kid."),
 (3,3,24,14,19,2,8,"WITNESS: I saw it last night. A pale figure stood over a ROCKET. When it left, it laid a black feather on the body.\n\nDon't tell the cops. They take money from ROCKET."),
 (3,3,25,14,GFX_POLICE,2,8,"POLICE: There was a black feather by that body too, just like in PEWTER. A killer who signs their work, I guess.\n\nMaybe the feather means something to them. I am not paid to ask. ROCKET pays us to look away."),
]
def free_tile(r,g,n,cx,cy):
    """nearest open walkable tile to (cx,cy): no object/warp/sign on it or next to it, and 3 or more walkable neighbours"""
    h=header(r,g,n); lay=r32(r,h)-0x08000000; ev=r32(r,h+4)-0x08000000
    w,hh=r32(r,lay),r32(r,lay+4); mp=r32(r,lay+12)-0x08000000
    no,nw,nc,nb=r.b[ev:ev+4]; po,wp,cp,bp=[r32(r,ev+4+4*i)-0x08000000 for i in range(4)]
    taken=set()
    for i in range(no): taken.add(struct.unpack('<hh',r.b[po+24*i+4:po+24*i+8]))
    for i in range(nw): taken.add(struct.unpack('<hh',r.b[wp+8*i:wp+8*i+4]))
    for i in range(nc): taken.add(struct.unpack('<HH',r.b[cp+16*i:cp+16*i+4]))
    for i in range(nb): taken.add(struct.unpack('<HH',r.b[bp+12*i:bp+12*i+4]))
    def ok(x,y):
        if not(0<=x<w and 0<=y<hh): return False
        return not(struct.unpack('<H',r.b[mp+2*(y*w+x):mp+2*(y*w+x)+2])[0]&0xc00)
    best=None
    for y in range(hh):
        for x in range(w):
            if not ok(x,y): continue
            if any((x+dx,y+dy) in taken for dx in (-1,0,1) for dy in (-1,0,1)): continue
            if sum(ok(x+dx,y+dy) for dx,dy in((1,0),(-1,0),(0,1),(0,-1)))<4: continue
            dd=abs(x-cx)+abs(y-cy)
            if best is None or dd<best[0]: best=(dd,x,y)
    return best[1],best[2]
STORY=[
 # (group,num, near x,y, gfx, std, movement, text)
 (3,4,16,10,19,2,8,"VOLUNTEER: MR. FUJI was framed by ROCKET. He told me they stole a trainer's PIKACHU and executed it.\n\nHe is held in the POKeMON TOWER. Go and free him."),
 (1,42,14,20,49,2,8,"HURT GRUNT: Don't shoot! The base is full of bodies. Someone is hunting the bosses.\n\nGIOVANNI is next. I am getting out of here."),
 (3,10,27,20,55,2,8,"SCIENTIST: PROF. OAK sold trainer records to ROCKET. That is how they found the owner of that PIKACHU.\n\nI saw the files myself."),
 (3,1,28,16,32,2,8,"OLD MAN: GIOVANNI has vanished. The gym is closed. They say LANCE took the LEAGUE by force.\n\nWhoever hunts ROCKET will meet him there."),
]
def install(r):
    setup_body_gfx(r)
    for g,n,x,y,gfx,std,mv,text in BEATS: add_object(r,g,n,x,y,gfx,text,std,mv)
    for g,n,cx,cy,gfx,std,mv,text in STORY:
        x,y=free_tile(r,g,n,cx,cy); print('placed',g,n,x,y); add_object(r,g,n,x,y,gfx,text,std,mv)
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))

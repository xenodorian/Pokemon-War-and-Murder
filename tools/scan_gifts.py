# Scan every map's scripts for item gifts, Pokemon gifts and flags set, to find the quests the game really contains.
import sys,struct,json,re,collections
sys.path.insert(0,'/home/claude/work/tools')
ROM=sys.argv[1]; d=open(ROM,'rb').read()
def r32(o):return struct.unpack('<I',d[o:o+4])[0]
def r16(o):return struct.unpack('<H',d[o:o+2])[0]
# opcode table from pret macros
OPS={}
t=open('/home/claude/pret/src/asm/macros/event.inc').read()
for m in re.finditer(r'\.macro\s+(\w+)([^\n]*)\n(.*?)\n\s*\.endm',t,re.S):
    lines=[l.split('@')[0].strip() for l in m.group(3).split('\n')]; lines=[l for l in lines if l]
    if lines and lines[0].startswith('.byte 0x') and all(l.split()[0] in ('.byte','.2byte','.4byte') for l in lines):
        op=int(lines[0].split()[1],16)
        if op not in OPS: OPS[op]=(m.group(1),[{'.byte':1,'.2byte':2,'.4byte':4}[l.split()[0]] for l in lines[1:]])
OPS[0xa2]=('waitmoncry',[])
for _o in (0x7d,0x7f,0x80,0x83,0x84): OPS[_o]=('buffer',[1,2])
TB={0:2,1:3,2:3,3:1,4:3,5:2,6:4,7:3,8:4,9:2}
def inrom(p): return 0x08000000<=p<0x08000000+len(d)
def scan(root,maxn=400):
    eff=dict(items=[],mons=[],setflags=[],trainers=[],warps=[],texts=[],gotos=0)
    seen=set(); q=[root]; n=0
    while q and n<maxn:
        p=q.pop()
        if not inrom(p) or p in seen: continue
        seen.add(p); a=p-0x08000000
        while True:
            n+=1
            if n>5000: break
            op=d[a]; a+=1
            if op==0x4f: a+=6
            elif op==0x50: a+=8
            elif op in (0x51,0x53,0x55): a+=2
            elif op in (0x52,0x54,0x56): a+=4
            elif op==0x5c:
                ty=d[a]; eff['trainers'].append(r16(a+1)); a+=5
                for i in range(TB.get(ty,2)):
                    pp=r32(a); a+=4
                    if i<TB.get(ty,2)-1 or ty in (0,3,4,5,7,9): pass
            elif op in (0x39,0x3a,0x3b,0x3d,0x3e,0x3f,0x40,0x41,0xd1): eff['warps'].append((d[a],d[a+1])); a+=7
            elif op in OPS:
                name,sizes=OPS[op]; args=[]
                for z in sizes: args.append(int.from_bytes(d[a:a+z],'little')); a+=z
                if op in (0x04,0x05,0x06,0x07): q.append(args[-1])
                elif op==0x0f and inrom(args[1]) and len(eff['texts'])<3: eff['texts'].append(args[1])
                elif op==0x44: eff['items'].append(args[0])
                elif op==0x1a and args[0]==0x8000: eff['items'].append(args[1])
                elif op==0x79: eff['mons'].append(args[0])
                elif op==0x29: eff['setflags'].append(args[0])
            else: break
            if op in (0x02,0x03,0x05): break
    return eff
import json as _j
_names=_j.load(open('/home/claude/pret/src/data/maps/map_groups.json'))
sizes=[len(_names[g]) for g in _names['group_order']]; sizes[2]=67
G=0x3526A8
out=[]
for gi in range(len(sizes)):
    gp=r32(G+4*gi)-0x08000000
    for n in range(sizes[gi]):
        h=r32(gp+4*n)-0x08000000; ev=r32(h+4)-0x08000000
        no,nw,nc,nb=d[ev:ev+4]; po,wp,cp,bp=[r32(ev+4+4*i)-0x08000000 for i in range(4)]
        for i in range(no):
            sp=r32(po+24*i+16)
            if inrom(sp):
                eff=scan(sp); 
                if eff['items'] or eff['mons']: out.append(dict(map=(gi,n),kind='obj',x=struct.unpack('<h',d[po+24*i+4:po+24*i+6])[0],y=struct.unpack('<h',d[po+24*i+6:po+24*i+8])[0],gfx=d[po+24*i+1],flag=r16(po+24*i+20),**eff))
        for i in range(nb):
            if d[bp+12*i+5]<5:
                sp=r32(bp+12*i+8)
                if inrom(sp):
                    eff=scan(sp)
                    if eff['items'] or eff['mons']: out.append(dict(map=(gi,n),kind='bg',x=r16(bp+12*i),y=r16(bp+12*i+2),**eff))
        for i in range(nc):
            sp=r32(cp+16*i+12)
            if inrom(sp):
                eff=scan(sp)
                if eff['items'] or eff['mons']: out.append(dict(map=(gi,n),kind='coord',x=r16(cp+16*i),y=r16(cp+16*i+2),**eff))
json.dump(out,open('/home/claude/work/gifts.json','w'))
print(len(out))

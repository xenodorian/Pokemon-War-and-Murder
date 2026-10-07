import sys,struct,json,re
sys.path.insert(0,'/home/claude/work/tools')
from g3 import *
d=open('/home/claude/work/orig.gba','rb').read()
OPS={int(k):v for k,v in json.load(open('/home/claude/work/ref/ops.json')).items()}
def parse_defs(fn):
    ns={'MAX_TRAINERS_COUNT':768}
    lines=[]
    for l in open(fn):
        mm=re.match(r'#define\s+(\w+)\s+(.*?)\s*(//.*)?$',l.rstrip())
        if mm and mm.group(2): lines.append((mm.group(1),mm.group(2)))
    for _ in range(60):
        for k,v in lines:
            if k in ns: continue
            try: ns[k]=int(eval(v,{"__builtins__":{}},ns))
            except Exception: pass
    m={}
    pref=('FLAG_','VAR_')
    for k,v in ns.items():
        if k.startswith(pref) and v not in m: m[v]=k
    return m
FLAGS=parse_defs('/home/claude/work/ref/flags.h'); VARS=parse_defs('/home/claude/work/ref/vars.h')
# resolve flag aliases like FLAG_X (FLAG_ID_START + n)
def fname(v): return FLAGS.get(v,'F%03X'%v)
def vname(v): return VARS.get(v,'V%04X'%v)
def u16(a): return struct.unpack('<H',d[a:a+2])[0]
def s16(a): return struct.unpack('<h',d[a:a+2])[0]
def u32(a): return struct.unpack('<I',d[a:a+4])[0]
def rp(a):
    v=u32(a); return v-0x08000000 if 0x08000000<=v<0x09000000 else None
def gtext(a,n=400):
    try:
        e=d.index(b'\xff',a)
        return dec(d[a:e+1]).replace('\n','|')[:n]
    except Exception: return '?'
mg=json.load(open('/home/claude/work/ref/map_groups.json'))
maps=[]  # (group,num,name,hdr)
base=0x3526a8
for gi,gname in enumerate(mg['group_order']):
    gp=rp(base+gi*4)
    for ni,mn in enumerate(mg[gname]):
        h=rp(gp+ni*4)
        maps.append((gi,ni,mn,h))
MAPNAME={(g,n):m for g,n,m,h in maps}
TB_EXTRA={0:0,1:4,2:4,3:-4,4:4,5:0,6:8,7:4,8:8}
def decomp(a,limit=300,seen=None):
    """linear decode with branch targets returned"""
    out=[];targets=[]
    n=0
    while n<limit:
        op=d[a]
        if op not in OPS: out.append('%06x: ??op %02x'%(a,op)); break
        name,sz=OPS[op][0],OPS[op][1]
        if op==0x5c:
            t=d[a+1]; ln=1+1+2+2+4+4+TB_EXTRA.get(t,0)
            ids=u16(a+2)
            args=[ 'type%d'%t,'trainer%d'%ids ]
            pos=a+2+2+2
            if t not in (3,): intro=rp(pos); pos+=4; args.append('"'+gtext(intro,80)+'"') if intro else 0
            de=rp(pos); pos+=4; 
            if de: args.append('def:"'+gtext(de,60)+'"')
            out.append('%06x: trainerbattle %s'%(a,' '.join(args)))
            if t in (1,2): 
                x=rp(pos)
                if x: targets.append(x); out[-1]+=' cont->%06x'%x
            if t in (6,8):
                x=rp(pos+4)
                if x: targets.append(x); out[-1]+=' cont->%06x'%x
            a+=ln; n+=1; continue
        ln=1+sum(sz); args=[];p=a+1
        for s in sz:
            v=d[p] if s==1 else (u16(p) if s==2 else u32(p)); args.append((v,s)); p+=s
        txt=''
        if name in('setflag','clearflag','checkflag','setflag'): txt=fname(args[0][0])
        elif name in('setvar','addvar','subvar','compare'): pass
        else: txt=' '.join('0x%x'%v if s!=4 else ('0x%x'%v) for v,s in args)
        if name=='setvar' or name=='compare' or name=='addvar' or name=='subvar' or name=='copyvar':
            txt='%s, %s'%(vname(args[0][0]),'0x%x'%args[1][0])
        if name in('message','loadword','call','goto','goto_if','call_if','trainerbattle') or any(s==4 for s in sz):
            for v,s in args:
                if s==4 and 0x08000000<=v<0x09000000:
                    t=v-0x08000000
                    if name in('message',) or (name=='loadword'): txt+=' "'+gtext(t,300)+'"'
                    else: txt+=' ->%06x'%t
                    if name in('call','goto','goto_if','call_if'): targets.append(t)
        if name in('gotostd','callstd'): txt='std%d'%args[0][0]
        out.append('%06x: %s %s'%(a,name,txt))
        n+=1; a+=ln
        if name in('end','return','goto','gotostd','endram','returnram'): break
    return out,targets
def dump_script(a,depth=0,seen=None,maxdepth=4):
    if seen is None: seen=set()
    lines=[]
    if a in seen or depth>maxdepth: return lines
    seen.add(a)
    out,tg=decomp(a)
    lines+=['  '*depth+'  '+l for l in out]
    for t in tg: lines+=dump_script(t,depth+1,seen,maxdepth)
    return lines
def dump_map(g,n,maxdepth=3):
    h=[x for x in maps if x[0]==g and x[1]==n][0][3]
    ev=rp(h+4); sc=rp(h+8)
    L=['=== (%d,%d) %s'%(g,n,MAPNAME[(g,n)])]
    if ev is None: return L
    no,nw,nc,nb=d[ev:ev+4]
    po=rp(ev+4); pw=rp(ev+8); pc=rp(ev+12); pb=rp(ev+16)
    for i in range(nw):
        a=pw+i*8
        L.append(' warp%d at(%d,%d) -> (%d,%d) w%d'%(i,s16(a),s16(a+2),d[a+7],d[a+6],d[a+5]))
    for i in range(no):
        a=po+i*0x18
        s=rp(a+16)
        L.append(' obj%d gfx%d at(%d,%d) trainer=%d flag=%s script=%s'%(d[a],d[a+1],s16(a+4),s16(a+6),u16(a+0xc),fname(u16(a+0x14)) if u16(a+0x14) else '-', '%06x'%s if s else '-'))
        if s: L+=dump_script(s,0,None,maxdepth)
    for i in range(nc):
        a=pc+i*0x10
        s=rp(a+12)
        L.append(' coord at(%d,%d) var=%s val=%d script=%06x'%(s16(a),s16(a+2),vname(u16(a+6)),u16(a+8),s if s else 0))
        if s: L+=dump_script(s,0,None,maxdepth)
    for i in range(nb):
        a=pb+i*12
        k=d[a+5]
        if k<=4:
            s=rp(a+8)
            L.append(' sign at(%d,%d) kind%d script=%06x'%(s16(a),s16(a+2),k,s if s else 0))
            if s: L+=dump_script(s,0,None,maxdepth)
    # map scripts
    if sc:
        a=sc
        while d[a]!=0:
            t=d[a]; p=rp(a+1)
            L.append(' mapscript type%d ->%06x'%(t,p if p else 0))
            if t in(2,4) and p:
                b=p
                while u16(b)!=0:
                    L.append('   var %s == %d ->'%(vname(u16(b)),u16(b+2)))
                    q=rp(b+4)
                    if q: L+=dump_script(q,1,None,maxdepth)
                    b+=8
            elif t in(1,3,5,6,7) and p: L+=dump_script(p,1,None,maxdepth)
            a+=5
    return L
if __name__=='__main__':
    g,n=int(sys.argv[1]),int(sys.argv[2])
    print('\n'.join(dump_map(g,n)))

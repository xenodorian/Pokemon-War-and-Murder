"""Quest log rework (usage: questlog_story.py IN.gba OUT.gba), run through tools/patch.sh.
The old log was stuck on FIRST POKeMON / OAK'S PARCEL / the eight gyms (the 'main' quests), and THE REAPER, none of which match the story any more.
New top menu: NEXT QUEST (the tracked side quest, else the next open story quest), STORY LIST (a checklist), SIDE QUESTS (the old paged list, unchanged), FATHER'S TEAM, CLOSE.
STORY LIST shows each story quest as (X) done, ( ) open, (/) crossed out (a path that can no longer be taken, e.g. YVELTAL once Father was chosen).
How it hooks in: the old entry script is found from the start menu literal 0xA01A38; its multichoice is replaced by a goto to the new menu (so every 'back' of the old side pages lands in the new menu),
the old main objective routine becomes a goto to the new next-quest routine, and the old menu table is copied with one new row list added."""
import sys,struct,os,textwrap
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from inc import Rom
from g3 import ENC
RESULT=0x800D
F_TOOK=0x4EF; F_FREED=0x4F7; F_FATHER_ALIVE=0x4FC; VAR_STORY=0x40E6; VAR_CHOICE=0x40F0; VAR_YV=0x40EF; VAR_NERO=0x40EA
JRA_FLAGS=list(range(0x4C0,0x4CA))
def f(x): return ('f',x)
def veq(v,n): return ('veq',v,n)
def vge(v,n): return ('vge',v,n)
def vne(v,n): return ('vne',v,n)
def anyof(*c): return ('any',list(c))
def allof(*c): return ('all',list(c))
# title (at most 25 characters), where, todo, done condition, crossed out condition
STORY=[
 ("FATHER'S POKéMON","Your house in PALLET TOWN.","Take SANDSHREW from the shelf, then go outside.",f(F_TOOK),None),
 ("FREE SHINIGAMI","PEWTER CITY, the grey JRA building north-east of the Gym.","Beat CAPT. MARLOW, take the key and open the cell. The door needs the medal of the base before it.",f(F_FREED),None),
 ("ANNE'S NEWS","Outside the PEWTER base, then your house in PALLET TOWN.","ANNE waits outside the base with news. Then go to Father's bedside.",vge(VAR_STORY,3),None),
 ("RAISE FATHER","Father's bedside, your house in PALLET TOWN.","Use the SCROLL on Father, or speak YVELTAL's name. You can only choose one.",f(F_FATHER_ALIVE),veq(VAR_CHOICE,2)),
 ("WAKE YVELTAL","The grave at the top of POKéMON TOWER, LAVENDER TOWN.","Carry the SCROLL to the grave. YVELTAL wakes: tame it, or beat it.",anyof(veq(VAR_YV,2),veq(VAR_YV,3)),veq(VAR_CHOICE,1)),
 ("BREAK THE JRA","The ten JRA bases of KANTO.","Beat all ten CAPTAINS. Each base has its own entry under SIDE QUESTS.",allof(*[f(x) for x in JRA_FLAGS]),None),
 ("FACE GENERAL NERO","SEVEN ISLAND, the JRA headquarters.","Beat GENERAL NERO. Then decide: arrest him, execute him, or be crowned.",vne(VAR_NERO,0),None),
]
def text(s):
    o=bytearray(); i=0
    while i<len(s):
        c=s[i]
        if c=='\n': o.append(0xFE)
        elif c=='\x01': o.append(0xFB)
        elif c=='\x02': o+=bytes([0xFD,0x02])
        elif c=='\x03': o+=bytes([0xFD,0x03])
        else: o.append(ENC[c])
        i+=1
    o.append(0xFF); return bytes(o)
def wrap_pages(prefix,body,width=31):
    lines=textwrap.wrap(prefix+body,width=width,break_long_words=False)
    return '\x01'.join('\n'.join(lines[i:i+2]) for i in range(0,len(lines),2))
def quest_text(title,where,todo):
    return '\x01'.join([wrap_pages('QUEST: ',title),wrap_pages('GO TO: ',where),wrap_pages('TO DO: ',todo)])
class Asm:
    def __init__(s): s.items=[]; s.n=0
    def lab(s,n): s.items.append(('L',n))
    def raw(s,*b): s.items.append(('B',bytes(b)))
    def ptr(s,op,addr): s.items.append(('B',bytes(op)+struct.pack('<I',addr)))
    def ref(s,op,label): s.items.append(('R',bytes(op),label))
    def fresh(s,p): s.n+=1; return '%s_%d'%(p,s.n)
    def goto(s,l): s.ref([0x05],l)
    def goto_if(s,cond,l): s.ref([0x06,cond],l)
    def cmpvar(s,v,n): s.raw(0x21,*struct.pack('<HH',v,n))
    def chkflag(s,fl): s.raw(0x2b,*struct.pack('<H',fl))
    def setvar(s,v,n): s.raw(0x16,*struct.pack('<HH',v,n))
    def msg(s,addr): s.ptr([0x0f,0],addr); s.raw(0x09,4)
    def yesno(s,addr): s.ptr([0x0f,0],addr); s.raw(0x09,5)
    def bufferstring(s,out,addr): s.ptr([0x85,out],addr)
    def call(s,l): s.ref([0x04],l)
    def ret(s): s.raw(0x03)
    def true_jump(s,c,l):
        k=c[0]
        if k=='f': s.chkflag(c[1]); s.goto_if(1,l)
        elif k=='veq': s.cmpvar(c[1],c[2]); s.goto_if(1,l)
        elif k=='vge': s.cmpvar(c[1],c[2]); s.goto_if(4,l)
        elif k=='vne': s.cmpvar(c[1],c[2]); s.goto_if(5,l)
        elif k=='any':
            for x in c[1]: s.true_jump(x,l)
        elif k=='all':
            no=s.fresh('no')
            for x in c[1]: s.false_jump(x,no)
            s.goto(l); s.lab(no)
        else: raise Exception(k)
    def false_jump(s,c,l):
        k=c[0]
        if k=='f': s.chkflag(c[1]); s.goto_if(0,l)
        elif k=='veq': s.cmpvar(c[1],c[2]); s.goto_if(5,l)
        elif k=='vge': s.cmpvar(c[1],c[2]); s.goto_if(0,l)
        elif k=='vne': s.cmpvar(c[1],c[2]); s.goto_if(1,l)
        else:
            ok=s.fresh('ok'); s.true_jump(c,ok); s.goto(l); s.lab(ok)
    def assemble(s,base):
        off=0; labels={}
        for it in s.items:
            if it[0]=='L': labels[it[1]]=off
            elif it[0]=='B': off+=len(it[1])
            else: off+=len(it[1])+4
        out=bytearray()
        for it in s.items:
            if it[0]=='B': out+=it[1]
            elif it[0]=='R': out+=it[1]+struct.pack('<I',0x08000000+base+labels[it[2]])
        return bytes(out),labels
def install(r):
    b=r.b; r32=lambda a: struct.unpack('<I',b[a:a+4])[0]
    rom=lambda p: p-0x08000000
    # ---- find the old script
    entry=rom(r32(0xa01a38)); assert b[entry]==0x69 and b[entry+1]==0x6f,hex(entry)
    menu_old=entry+1; mid=b[entry+4]
    tg=[r32(entry+6+11*k+7) for k in range(4)]
    for k in range(4): assert b[entry+6+11*k:entry+6+11*k+7]==bytes([0x21,0x0d,0x80,k,0,0x06,0x01]),k
    g=entry+6+44; assert b[g]==0x05; handler=rom(r32(g+1))
    m_cur,m_story,m_reaper,page0=tg
    cur=r32(rom(m_cur)+1); assert b[rom(m_cur)]==0x04
    main_obj=rom(r32(rom(m_story)+1)); assert b[rom(m_story)]==0x04 and b[main_obj]==0x04
    # father's team native: the callnative inside the old handler's 'have' branch
    fb=rom(r32(handler+7)); swap=None
    for i in range(fb,fb+120):
        if b[i]==0x23:
            p=r32(i+1)
            if 0x08000000<=p<0x0a000000 and p&1: swap=p; break
    assert swap,'swap native not found'
    # ---- menu table: copy 100 entries, add the new row list at id 100
    ref=0x9cb58; assert r32(ref)==r32(0x9cfd4)
    oldtab=rom(r32(ref)); entries=bytearray(b[oldtab:oldtab+100*8])
    titles=['NEXT QUEST','STORY LIST','SIDE QUESTS',"FATHER'S TEAM",'CLOSE']
    ls=b''.join(struct.pack('<II',0x08000000+r.alloc(text(t),1),0) for t in titles)
    entries.extend(struct.pack('<IBBBB',0x08000000+r.alloc(ls,4),len(titles),0,0,0))
    newid=100
    # ---- text
    S={}
    def st(k,t):
        if k not in S: S[k]=0x08000000+r.alloc(text(t),1)
        return S[k]
    A=Asm()
    # status routine per quest: RESULT 0 open, 1 done, 2 crossed out
    for i,(title,where,todo,done,skip) in enumerate(STORY):
        A.lab('status%d'%i)
        if skip: A.true_jump(skip,'sk%d'%i)
        A.true_jump(done,'dn%d'%i)
        A.setvar(RESULT,0); A.ret()
        A.lab('dn%d'%i); A.setvar(RESULT,1); A.ret()
        if skip: A.lab('sk%d'%i); A.setvar(RESULT,2); A.ret()
    # marker into a string buffer (1 = {STR_VAR_1}, 2 = {STR_VAR_2}); RESULT holds the status
    for buf in (1,2):
        A.lab('marker%d'%buf)
        A.cmpvar(RESULT,1); A.goto_if(1,'mk%d_x'%buf)
        A.cmpvar(RESULT,2); A.goto_if(1,'mk%d_s'%buf)
        A.bufferstring(buf-1,st('mo','( )')); A.ret()
        A.lab('mk%d_x'%buf); A.bufferstring(buf-1,st('mx','(X)')); A.ret()
        A.lab('mk%d_s'%buf); A.bufferstring(buf-1,st('ms','(/)')); A.ret()
    # next open story quest
    A.lab('next')
    for i,(title,where,todo,done,skip) in enumerate(STORY):
        A.call('status%d'%i); A.cmpvar(RESULT,0); A.goto_if(5,'next_%d'%(i+1))
        A.msg(st(('q',i),quest_text(title,where,todo))); A.ret()
        A.lab('next_%d'%(i+1))
    A.msg(st('alldone','All STORY quests are settled.\nThe war is over.')); A.ret()
    # checklist: two quests per box, lines 'marker title'
    A.lab('list')
    for i in range(0,len(STORY),2):
        pair=STORY[i:i+2]
        for k,q in enumerate(pair):
            A.call('status%d'%(i+k)); A.call('marker%d'%(k+1))
        t='\x02 %s'%pair[0][0]
        if len(pair)>1: t+='\n\x03 %s'%pair[1][0]
        A.msg(st(('l',i),t))
    A.msg(st('legend','(X) done  ( ) open\n(/) crossed out')); A.ret()
    # menu
    A.lab('menu'); A.raw(0x6f,0,0,newid,0)
    for k,l in enumerate(('m_cur','m_list','m_side','m_father')):
        A.cmpvar(RESULT,k); A.goto_if(1,l)
    A.goto('m_exit')
    A.lab('m_cur'); A.ptr([0x04],0x08000000+rom(cur)); A.raw(0x68); A.goto('menu')
    A.lab('m_list'); A.call('list'); A.raw(0x68); A.goto('menu')
    A.lab('m_side'); A.ptr([0x05],page0)
    A.lab('m_father'); A.chkflag(F_FATHER_ALIVE); A.goto_if(1,'have')
    A.msg(st('nobody','Nobody travels with you.')); A.raw(0x68); A.goto('menu')
    A.lab('have'); A.yesno(st('swap',"Swap your party with\nFATHER's team?")); A.cmpvar(RESULT,1); A.goto_if(5,'no')
    A.ptr([0x23],swap); A.msg(st('swapped',"Your party and FATHER's\nteam traded places."))
    A.lab('no'); A.raw(0x68); A.goto('menu')
    A.lab('m_exit'); A.raw(0x68); A.raw(0x6b); A.raw(0x02)
    r.cur=(r.cur+3)&~3; base=r.cur
    code,labels=A.assemble(base); a=r.alloc(code,1); assert a==base
    # ---- hook up
    newtab=r.alloc(bytes(entries),4); r.w32(ref,0x08000000+newtab); r.w32(0x9cfd4,0x08000000+newtab)
    b[menu_old:menu_old+5]=bytes([0x05])+struct.pack('<I',0x08000000+base+labels['menu'])       # old multichoice -> new menu
    b[main_obj:main_obj+5]=bytes([0x05])+struct.pack('<I',0x08000000+base+labels['next'])         # old main objective -> next story quest
    print('quest log: new code at',hex(base),len(code),'bytes, menu id',newid)
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))

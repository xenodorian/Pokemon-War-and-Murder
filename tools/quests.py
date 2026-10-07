"""Quest log data + script generator for the Outlaw quest patch.
Flags / vars below were located in this ROM's own scripts (see notes in README)."""
import struct,textwrap

# ---- flag / var ids (resolved from pokefirered constants; verified present in ROM scripts)
F=dict(POKEMON_GET=0x829, POKEDEX_GET=0x828, VS_SEEKER=None)  # placeholder, real ids loaded below
import sys
sys.path.insert(0,'/home/claude/work/tools')
import scr
NAME2FLAG={v:k for k,v in scr.FLAGS.items()}
NAME2VAR={v:k for k,v in scr.VARS.items()}
def flag(n): return NAME2FLAG[n]
def var(n): return NAME2VAR[n]

TRACK_VAR=0x40A0          # unused save var used to remember the tracked quest (0 = none)
RESULT=0x800D

# ---- quest definitions -------------------------------------------------------
# stage cond: ('f',FLAGNAME,bool) or ('v',VARNAME,'==',n)
MAIN=[
 dict(title='FIRST POKéMON', done='FLAG_SYS_POKEMON_GET', stages=[
   (None,'PALLET TOWN, then PROF. OAK\'s LAB.',
    'Leave the SLUMS and walk to the north edge of PALLET TOWN. A tourist will point you to the LAB. Take a POKé BALL from the table.')]),
 dict(title="OAK's PARCEL", done='FLAG_SYS_POKEDEX_GET', stages=[
   ([('f','FLAG_GOT_VS_SEEKER',True)],'PALLET TOWN, PROF. OAK\'s LAB.',
    "You have OAK's PARCEL. Take it to PROF. OAK in his LAB."),
   ([('v','VAR_MAP_SCENE_VIRIDIAN_CITY_MART','==',0)],'VIRIDIAN CITY. Take ROUTE 1 north from PALLET TOWN.',
    'Go into the POKéMON MART and talk to the clerk.'),
   (None,'VIRIDIAN SLUMS, the cave in VIRIDIAN CITY.',
    "Thugs stole OAK's PARCEL. Beat the two THUGS, then talk to their LEADER to get it back.")]),
 dict(title='PEWTER GYM', done='FLAG_BADGE01_GET', stages=[
   (None,'PEWTER CITY. ROUTE 2 leads north from VIRIDIAN CITY.',
    'Beat GYM LEADER BROCK to win the BOULDERBADGE.')]),
 dict(title='CERULEAN GYM', done='FLAG_BADGE02_GET', stages=[
   (None,'CERULEAN CITY. Take ROUTE 3 and ROUTE 4 east from PEWTER CITY.',
    'Beat GYM LEADER MISTY to win the CASCADEBADGE.')]),
 dict(title='VERMILION GYM', done='FLAG_BADGE03_GET', stages=[
   (None,'VERMILION CITY. Go south from CERULEAN CITY on ROUTE 5, then ROUTE 6.',
    'Beat GYM LEADER LT. SURGE to win the THUNDERBADGE.')]),
 dict(title='CELADON GYM', done='FLAG_BADGE04_GET', stages=[
   (None,'CELADON CITY. ROUTE 7 links it to SAFFRON CITY.',
    'Beat GYM LEADER ERIKA to win the RAINBOWBADGE.')]),
 dict(title='FUCHSIA GYM', done='FLAG_BADGE05_GET', stages=[
   (None,'FUCHSIA CITY. From CELADON CITY use ROUTE 16, 17 and 18.',
    'Beat GYM LEADER KOGA to win the SOULBADGE.')]),
 dict(title='SAFFRON GYM', done='FLAG_BADGE06_GET', stages=[
   (None,'SAFFRON CITY. Take ROUTE 6 from VERMILION or ROUTE 7 from CELADON.',
    'The GUARDS at the gates want a drink (TEA). Then beat GYM LEADER SABRINA to win the MARSHBADGE.')]),
 dict(title='CINNABAR GYM', done='FLAG_BADGE07_GET', stages=[
   (None,'CINNABAR ISLAND. Go south from PALLET TOWN on ROUTE 21.',
    'You need SURF to cross the sea. Beat the GYM LEADER BLAINE to win the VOLCANOBADGE.')]),
 dict(title='VIRIDIAN GYM', done='FLAG_BADGE08_GET', stages=[
   (None,'VIRIDIAN CITY GYM.',
    'The GYM opens once you hold the badges from CERULEAN through CINNABAR. Beat GYM LEADER MAY to win the EARTHBADGE.')]),
 dict(title='POKéMON LEAGUE', done='FLAG_DEFEATED_CHAMP', stages=[
   (None,'ROUTE 22 and ROUTE 23, west of VIRIDIAN CITY, then the LEAGUE.',
    'You need all 8 badges to pass ROUTE 23. Beat LORELEI, BRUNO, AGATHA, LANCE and the CHAMPION.')]),
]
SIDE=[
 dict(title='S.S. TICKET', done='FLAG_GOT_SS_TICKET', stages=[
   (None,"BILL's SEA COTTAGE on ROUTE 25. ROUTE 24 leads north from CERULEAN CITY.",
    'Meet BILL and get the S.S. TICKET.')]),
 dict(title='CUT (HM01)', done='FLAG_GOT_HM01', stages=[
   (None,"S.S. ANNE at VERMILION CITY: the CAPTAIN's office.",
    'Talk to the CAPTAIN to get HM01 CUT. You need the S.S. TICKET to board.')]),
 dict(title='SURF (HM03)', done='FLAG_GOT_HM03', stages=[
   (None,'The SAFARI ZONE at FUCHSIA CITY: the SECRET HOUSE.',
    'Find the SECRET HOUSE inside the SAFARI ZONE and talk to the attendant to get HM03 SURF.')]),
 dict(title='STRENGTH (HM04)', done='FLAG_GOT_HM02', stages=[
   (None,'The house on ROUTE 16, west of CELADON CITY.',
    'Talk to the girl inside to get HM04 STRENGTH.')]),
 dict(title='BICYCLE', done='FLAG_GOT_BICYCLE', stages=[
   ([('f','FLAG_GOT_BIKE_VOUCHER',True)],'The BIKE SHOP in CERULEAN CITY.',
    'Trade your BIKE VOUCHER for a BICYCLE.'),
   (None,'The POKéMON FAN CLUB in VERMILION CITY.',
    'Talk to the chairman and listen to his rant to get a BIKE VOUCHER. Then visit the BIKE SHOP in CERULEAN CITY.')]),
 dict(title='ROCKET HIDEOUT', done='FLAG_HIDE_CELADON_ROCKETS', stages=[
   (None,'The GAME CORNER in CELADON CITY.',
    'Push the switch behind the poster to open the hideout stairs, then defeat the ROCKETS below.')]),
 dict(title='POKé FLUTE', done='FLAG_GOT_POKE_FLUTE', unlock='FLAG_WORLD_MAP_LAVENDER_TOWN', stages=[
   (None,'The POKéMON CENTER in LAVENDER TOWN.',
    'Talk to the guy in the back left corner of the lobby for a free POKé FLUTE.')]),
]
ALL=MAIN+SIDE
for i,q in enumerate(ALL): q['id']=i+1
MENU_ENTRIES=['CURRENT QUEST','STORY QUEST','SIDE QUESTS','CLOSE']
BASE_SIDE=[q for q in SIDE if not q.get('unlock')]
UNLOCK_SIDE=[q for q in SIDE if q.get('unlock')]
SIDE_ENTRIES=[q['title'] for q in BASE_SIDE]+['BACK']          # list shown before any unlock
SIDE_ENTRIES_B=[q['title'] for q in SIDE]+['BACK']             # list once LAVENDER TOWN was entered
MENU_ID=65; SIDE_ID=66; SIDE_ID_B=67
LAV_UNLOCK='FLAG_WORLD_MAP_LAVENDER_TOWN'

def wrap_pages(prefix,body,width=31):
    lines=textwrap.wrap(prefix+body,width=width,break_long_words=False)
    pages=[]
    for i in range(0,len(lines),2): pages.append('\n'.join(lines[i:i+2]))
    return '\x01'.join(pages)

def quest_text(title,where,todo):
    return '\x01'.join([wrap_pages('QUEST: ',title),wrap_pages('GO TO: ',where),wrap_pages('TO DO: ',todo)])

class Asm:
    def __init__(s): s.items=[];s.labels={}
    def lab(s,n): s.items.append(('L',n))
    def raw(s,*b): s.items.append(('B',bytes(b)))
    def u16(s,v): return struct.pack('<H',v)
    def ref(s,op,label): s.items.append(('R',bytes(op),label))
    def ptrc(s,op,addr): s.items.append(('B',bytes(op)+struct.pack('<I',0x08000000+addr)))
    def size(s):
        n=0
        for it in s.items:
            if it[0]=='B': n+=len(it[1])
            elif it[0]=='R': n+=len(it[1])+4
        return n
    def assemble(s,base):
        off=0;labels={}
        for it in s.items:
            if it[0]=='L': labels[it[1]]=off
            elif it[0]=='B': off+=len(it[1])
            else: off+=len(it[1])+4
        out=bytearray()
        for it in s.items:
            if it[0]=='B': out+=it[1]
            elif it[0]=='R': out+=it[1]+struct.pack('<I',0x08000000+base+labels[it[2]])
        return bytes(out),{k:base+v for k,v in labels.items()}
    # --- script commands
    def lockall(s): s.raw(0x69)
    def releaseall(s): s.raw(0x6b)
    def end(s): s.raw(0x02)
    def ret(s): s.raw(0x03)
    def closemsg(s): s.raw(0x68)
    def goto(s,l): s.ref([0x05],l)
    def call(s,l): s.ref([0x04],l)
    def goto_if(s,cond,l): s.ref([0x06,cond],l)
    def cmpvar(s,v,n): s.raw(0x21,*(s.u16(v)+s.u16(n)))
    def chkflag(s,f): s.raw(0x2b,*s.u16(f))
    def setvar(s,v,n): s.raw(0x16,*(s.u16(v)+s.u16(n)))
    def msg(s,addr): s.ptrc([0x0f,0],addr); s.raw(0x09,4)
    def yesno(s,addr): s.ptrc([0x0f,0],addr); s.raw(0x09,5)
    def multichoice(s,mid): s.raw(0x6f,0,0,mid,0)
    def if_flag(s,fl,val,l): s.chkflag(fl); s.goto_if(1 if val else 0,l)
    def if_res(s,n,l): s.cmpvar(RESULT,n); s.goto_if(1,l)

def emit(alloc,text,ptr):
    """Allocate strings + script. Returns (entry_addr, menu_list_addr, side_list_addr)."""
    A=Asm()
    S={}
    def st(k,t):
        if k not in S: S[k]=alloc(text(t),1)
        return S[k]
    # info routines
    for q in ALL:
        t=q['title']; i=q['id']
        A.lab('info%d'%i)
        for si,(conds,where,todo) in enumerate(q['stages']):
            nxt='info%d_s%d'%(i,si+1)
            if conds:
                # AND of conditions: if any fails jump to next stage
                for ci,c in enumerate(conds):
                    if c[0]=='f':
                        A.chkflag(flag(c[1])); A.goto_if(0 if c[2] else 1,nxt)
                    else:
                        A.cmpvar(var(c[1]),c[3]); A.goto_if(5,nxt)   # NE -> fail
            A.msg(st(('q',i,si),quest_text(t,where,todo))); A.ret()
            A.lab(nxt)
        A.ret()   # safety
    # main objective
    A.lab('main_obj')
    for k,q in enumerate(MAIN):
        A.lab('main_%d'%k)
        A.chkflag(flag(q['done'])); A.goto_if(1,'main_%d'%(k+1))
        A.call('info%d'%q['id']); A.ret()
    A.lab('main_%d'%len(MAIN))
    A.msg(st('alldone','All MAIN quests are complete!\nNice work, champ.')); A.ret()
    # current quest
    A.lab('current')
    A.cmpvar(TRACK_VAR,0); A.goto_if(1,'cur_main')
    for q in ALL:
        A.cmpvar(TRACK_VAR,q['id']); A.goto_if(1,'cur_q%d'%q['id'])
    A.lab('cur_main'); A.call('main_obj'); A.ret()
    for q in ALL:
        A.lab('cur_q%d'%q['id'])
        A.chkflag(flag(q['done'])); A.goto_if(1,'cur_q%d_done'%q['id'])
        A.call('info%d'%q['id']); A.ret()
        A.lab('cur_q%d_done'%q['id'])
        A.setvar(TRACK_VAR,0)
        A.msg(st('trackdone','Your tracked quest is complete!')); A.closemsg(); A.goto('cur_main')
    # side quest viewer
    A.lab('side_show')
    for k,q in enumerate(SIDE):
        pass
    # entry + menu
    A.lab('entry'); A.lockall()
    A.lab('menu'); A.multichoice(MENU_ID)
    A.if_res(0,'m_cur'); A.if_res(1,'m_story'); A.if_res(2,'m_side'); A.goto('m_exit')
    A.lab('m_cur'); A.call('current'); A.closemsg(); A.goto('menu')
    A.lab('m_story'); A.call('main_obj'); A.closemsg(); A.goto('menu')
    A.lab('m_side'); A.chkflag(flag(LAV_UNLOCK)); A.goto_if(1,'m_side_b')
    A.multichoice(SIDE_ID)
    for k in range(len(BASE_SIDE)): A.if_res(k,'side%d'%k)
    A.goto('menu')
    A.lab('m_side_b'); A.multichoice(SIDE_ID_B)
    for k in range(len(SIDE)): A.if_res(k,'side%d'%k)
    A.goto('menu')
    for k,q in enumerate(SIDE):
        A.lab('side%d'%k)
        A.chkflag(flag(q['done'])); A.goto_if(1,'side%d_done'%k)
        A.call('info%d'%q['id'])
        A.yesno(st('trackq','Track this quest?\nIt will show under CURRENT QUEST.'))
        A.if_res(0,'m_side')
        A.setvar(TRACK_VAR,q['id'])
        A.msg(st('tracked','Quest tracked.')); A.closemsg(); A.goto('m_side')
        A.lab('side%d_done'%k)
        A.msg(st(('done',k),'QUEST: %s\nThis quest is complete.'%q['title'])); A.closemsg(); A.goto('m_side')
    A.lab('m_exit'); A.closemsg(); A.releaseall(); A.end()
    code,labels=A.assemble(0)  # to size
    base=alloc(b'\xff'*len(code),1)       # reserve
    code,labels=A.assemble(base)
    return base,labels['entry'],code

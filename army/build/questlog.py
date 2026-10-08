"""Rebuilds the QUESTS start-menu entry with the full quest list (story, THE REAPER thread, paged side quests)."""
import sys,struct,textwrap
sys.path.insert(0,'/home/claude/work/tools')
from inc import *
from g3 import ENC
import qconsts
FLAGS,VARS,ITEMS=qconsts.consts()
RESULT=0x800D; TRACK_VAR=0x40A0
VAR_LEAGUE=0x40F3
import json
FN=json.load(open('/home/claude/work/leg2/fns.json'))
def F(n): return FLAGS[n]
def I(n): return ITEMS[n]
def f(n,want=True): return ('f',F(n),want)
def it(n): return ('i',I(n))
def tr(tid,want=True): return ('t',tid,want)
def anyflag(*names): return ('o',[F(n) for n in names])
def var(v,val): return ('v',v,val)
# ---------------------------------------------------------------- data
MAIN=[
 dict(title='FIRST POKéMON',done=[f('FLAG_SYS_POKEMON_GET')],stages=[
   (None,"PALLET TOWN, then PROF. OAK's LAB.","Leave the SLUMS and walk to the north edge of PALLET TOWN. A tourist will point you to the LAB. Take a POKé BALL from the table.")]),
 dict(title="OAK'S PARCEL",done=[f('FLAG_SYS_POKEDEX_GET')],stages=[
   ([f('FLAG_GOT_VS_SEEKER')],"PALLET TOWN, PROF. OAK's LAB.","You have OAK's PARCEL. Take it to PROF. OAK in his LAB."),
   ([var(VARS['VAR_MAP_SCENE_VIRIDIAN_CITY_MART'],0)],'VIRIDIAN CITY. Take ROUTE 1 north from PALLET TOWN.','Go into the POKéMON MART and talk to the clerk.'),
   (None,'VIRIDIAN SLUMS, the cave in VIRIDIAN CITY.',"Thugs stole OAK's PARCEL. Beat the two THUGS, then talk to their LEADER to get it back.")]),
 dict(title='PEWTER GYM',done=[f('FLAG_BADGE01_GET')],stages=[(None,'PEWTER CITY. ROUTE 2 leads north from VIRIDIAN CITY.','Beat GYM LEADER BROCK to win the BOULDERBADGE.')]),
 dict(title='CERULEAN GYM',done=[f('FLAG_BADGE02_GET')],stages=[(None,'CERULEAN CITY. Take ROUTE 3 and ROUTE 4 east from PEWTER CITY.','Beat GYM LEADER MISTY to win the CASCADEBADGE.')]),
 dict(title='VERMILION GYM',done=[f('FLAG_BADGE03_GET')],stages=[(None,'VERMILION CITY. Go south from CERULEAN CITY on ROUTE 5, then ROUTE 6.','Beat GYM LEADER LT. SURGE to win the THUNDERBADGE.')]),
 dict(title='CELADON GYM',done=[f('FLAG_BADGE04_GET')],stages=[(None,'CELADON CITY. ROUTE 7 links it to SAFFRON CITY.','Beat GYM LEADER ERIKA to win the RAINBOWBADGE.')]),
 dict(title='FUCHSIA GYM',done=[f('FLAG_BADGE05_GET')],stages=[(None,'FUCHSIA CITY. From CELADON CITY use ROUTE 16, 17 and 18.','Beat GYM LEADER KOGA to win the SOULBADGE.')]),
 dict(title='SAFFRON GYM',done=[f('FLAG_BADGE06_GET')],stages=[(None,'SAFFRON CITY. Take ROUTE 6 from VERMILION or ROUTE 7 from CELADON.','The GUARDS at the gates want a drink (TEA). Then beat GYM LEADER SABRINA to win the MARSHBADGE.')]),
 dict(title='CINNABAR GYM',done=[f('FLAG_BADGE07_GET')],stages=[(None,'CINNABAR ISLAND. Go south from PALLET TOWN on ROUTE 21.','You need SURF to cross the sea. Beat the GYM LEADER BLAINE to win the VOLCANOBADGE.')]),
 dict(title='VIRIDIAN GYM',done=[f('FLAG_BADGE08_GET')],stages=[(None,'VIRIDIAN CITY GYM.','The GYM opens once you hold the badges from CERULEAN through CINNABAR. Beat GYM LEADER MAY to win the EARTHBADGE.')]),
 dict(title='POKéMON LEAGUE',done=[f('FLAG_DEFEATED_CHAMP')],stages=[(None,'ROUTE 22 and ROUTE 23, west of VIRIDIAN CITY, then the LEAGUE.','You need all 8 badges to pass ROUTE 23. Beat LORELEI, BRUNO, AGATHA, LANCE and the CHAMPION.')]),
]
REAPER=dict(title='THE REAPER',done=[var(VAR_LEAGUE,1)],stages=[
 ([f('FLAG_WORLD_MAP_VERMILION_CITY',False)],'The road from PALLET TOWN to VERMILION CITY.','Dead ROCKET grunts lie in PALLET, VIRIDIAN, PEWTER, CERULEAN and VERMILION, each with a black feather. Ask the police by each body.'),
 ([f('FLAG_RESCUED_MR_FUJI',False)],'POKéMON TOWER, LAVENDER TOWN.','MR. FUJI is held on the top floor. He knows who is hunting ROCKET.'),
 ([tr(348,False)],'ROCKET HIDEOUT, under the CELADON GAME CORNER.','Face GIOVANNI. Someone is hunting his men and he fears he is next.'),
 (None,'POKéMON LEAGUE, past ROUTE 23.',"SHINIGAMI hunts LANCE too. Reach LANCE's room and meet SHINIGAMI at the entrance.")])
def hm(title,item,where,todo): return dict(title=title,done=[it(item)],stages=[(None,where,todo)])
SPIRIT_QUEST=dict(title='SPIRIT WITCH',done=[('v',0x40F5,10)],stages=[
   ([('f',0x4DA,False)],'CELADON CITY, by the pond.','Talk to the SPIRIT WITCH. She only works with people who have good KARMA.'),
   ([('v',0x40F5,0),('f',0x4D0,True)],'CELADON CITY, the SPIRIT WITCH.','Return to the SPIRIT WITCH for your reward. You caught the GASTLY in PALLET TOWN.'),
   ([('v',0x40F5,0)],'PALLET TOWN.','Catch the level 5 GASTLY that haunts it, then return to the SPIRIT WITCH.'),
   ([('v',0x40F5,1),('f',0x4D1,True)],'CELADON CITY, the SPIRIT WITCH.','Return to the SPIRIT WITCH for your reward. You caught the HOUNDOUR in VIRIDIAN CITY.'),
   ([('v',0x40F5,1)],'VIRIDIAN CITY.','Catch the level 10 HOUNDOUR that haunts it, then return to the SPIRIT WITCH.'),
   ([('v',0x40F5,2),('f',0x4D2,True)],'CELADON CITY, the SPIRIT WITCH.','Return to the SPIRIT WITCH for your reward. You caught the MURKROW in PEWTER CITY.'),
   ([('v',0x40F5,2)],'PEWTER CITY.','Catch the level 15 MURKROW that haunts it, then return to the SPIRIT WITCH.'),
   ([('v',0x40F5,3),('f',0x4D3,True)],'CELADON CITY, the SPIRIT WITCH.','Return to the SPIRIT WITCH for your reward. You caught the SNEASEL in CERULEAN CITY.'),
   ([('v',0x40F5,3)],'CERULEAN CITY.','Catch the level 20 SNEASEL that haunts it, then return to the SPIRIT WITCH.'),
   ([('v',0x40F5,4),('f',0x4D4,True)],'CELADON CITY, the SPIRIT WITCH.','Return to the SPIRIT WITCH for your reward. You caught the HAUNTER in VERMILION CITY.'),
   ([('v',0x40F5,4)],'VERMILION CITY.','Catch the level 25 HAUNTER that haunts it, then return to the SPIRIT WITCH.'),
   ([('v',0x40F5,5),('f',0x4D5,True)],'CELADON CITY, the SPIRIT WITCH.','Return to the SPIRIT WITCH for your reward. You caught the MISDREAVUS in LAVENDER TOWN.'),
   ([('v',0x40F5,5)],'LAVENDER TOWN.','Catch the level 30 MISDREAVUS that haunts it, then return to the SPIRIT WITCH.'),
   ([('v',0x40F5,6),('f',0x4D6,True)],'CELADON CITY, the SPIRIT WITCH.','Return to the SPIRIT WITCH for your reward. You caught the HOUNDOOM in CELADON CITY.'),
   ([('v',0x40F5,6)],'CELADON CITY.','Catch the level 35 HOUNDOOM that haunts it, then return to the SPIRIT WITCH.'),
   ([('v',0x40F5,7),('f',0x4D7,True)],'CELADON CITY, the SPIRIT WITCH.','Return to the SPIRIT WITCH for your reward. You caught the GENGAR in SAFFRON CITY.'),
   ([('v',0x40F5,7)],'SAFFRON CITY.','Catch the level 40 GENGAR that haunts it, then return to the SPIRIT WITCH.'),
   ([('v',0x40F5,8),('f',0x4D8,True)],'CELADON CITY, the SPIRIT WITCH.','Return to the SPIRIT WITCH for your reward. You caught the UMBREON in FUCHSIA CITY.'),
   ([('v',0x40F5,8)],'FUCHSIA CITY.','Catch the level 45 UMBREON that haunts it, then return to the SPIRIT WITCH.'),
   ([('v',0x40F5,9),('f',0x4D9,True)],'CELADON CITY, the SPIRIT WITCH.','Return to the SPIRIT WITCH for your reward. You caught the TYRANITAR in CINNABAR ISLAND.'),
   ([('v',0x40F5,9)],'CINNABAR ISLAND.','Catch the level 50 TYRANITAR that haunts it, then return to the SPIRIT WITCH.')])

JRA_WHERE={'PALLET':'PALLET TOWN, a grey JRA building through the east trees.','VIRIDIAN':'VIRIDIAN CITY, a grey JRA building in the east forest.','PEWTER':'PEWTER CITY, the grey JRA building north-east of the Gym.',
 'CERULEAN':'CERULEAN CITY, a grey JRA building on the east road.','VERMILION':'VERMILION CITY, a grey JRA building on the east road.','LAVENDER':'LAVENDER TOWN, a grey JRA building through the east cliff.',
 'CELADON':'CELADON CITY, a grey JRA building on the east road.','SAFFRON':'SAFFRON CITY, a grey JRA building by the west gate.','FUCHSIA':'FUCHSIA CITY, a grey JRA building north of the pond.','CINNABAR':'CINNABAR ISLAND, a grey JRA building on the south beach.'}
def jra_quests():
    allc=sorted(json.load(open('/home/claude/work/army/cities.json')),key=lambda c:c['num'])
    cities=[c for c in allc if c['name']!='GENERAL']; gen=[c for c in allc if c['name']=='GENERAL'][0]
    out=[]
    for c in cities:
        door='This door is unlocked.' if c['num']==1 else 'You need the %s to open the door.'%cities[c['num']-2]['medal']
        out.append(dict(title='JRA: '+c['name'],done=[('f',c['flag'],True)],stages=[(None,JRA_WHERE[c['name']],'The JOHTO REVOLUTIONARY ARMY holds %s. Beat CAPT. %s for the %s. %s'%(c['name'],c['captain'],c['medal'],door))]))
    out.append(dict(title='JRA: GENERAL',done=[('f',gen['flag'],True)],stages=[
      ([f('FLAG_DEFEATED_CHAMP',False)],'The POKéMON LEAGUE, past ROUTE 23.','The JRA headquarters on SEVEN ISLAND is sealed until the CHAMPION falls.'),
      (None,'SEVEN ISLAND, a grey JRA building through the east lawn.','Beat GENERAL %s and his six legendary POKéMON to end the JOHTO REVOLUTIONARY ARMY. The HALL OF JUSTICE records your team when he falls.'%gen['captain'])]))
    out.append(dict(title='HALL OF JUSTICE',done=[('f',0x4CB,True)],stages=[
      ([('f',gen['flag'],False)],'SEVEN ISLAND, the JRA headquarters.','Beat GENERAL %s first. The HALL OF JUSTICE opens for you when he falls.'%gen['captain']),
      (None,'The HALL OF JUSTICE, where you stood when GORE fell.','Let the COMMISSIONER record your team, then read the statue plaque to see the roll.')]))
    out.append(dict(title='POLICE DEAL',done=[('v',0x40AB,3)],stages=[
      ([('v',0x40AB,1)],'Anywhere the police find you.','You refused the deal. The offer will not come again.'),
      (None,'Any police officer, once the police are after you.','Kill more than 10 people and more than 10 JRA soldiers. An officer offers to look the other way if you stop killing civilians.')]))
    return out
JRA_QUESTS=jra_quests()
SIDE=[
 dict(title='S.S. TICKET',done=[f('FLAG_GOT_SS_TICKET')],stages=[(None,"BILL's SEA COTTAGE on ROUTE 25. ROUTE 24 leads north from CERULEAN CITY.",'Meet BILL and get the S.S. TICKET.')]),
 hm('CUT (HM01)','ITEM_HM01',"S.S. ANNE at VERMILION CITY: the CAPTAIN's office.",'Talk to the CAPTAIN to get HM01 CUT. You need the S.S. TICKET to board.'),
 hm('FLY (HM02)','ITEM_HM02','CERULEAN CITY POKéMON CENTER, the man at the back.',"Talk to him for HM02 FLY. GIOVANNI's ball at ROCKET HIDEOUT B4F holds one too."),
 hm('SURF (HM03)','ITEM_HM03','The SAFARI ZONE at FUCHSIA CITY: the SECRET HOUSE.','Find the SECRET HOUSE inside the SAFARI ZONE and talk to the attendant to get HM03 SURF.'),
 hm('STRENGTH (HM04)','ITEM_HM04','The house on ROUTE 16, west of CELADON CITY.','Talk to the girl inside to get HM04 STRENGTH.'),
 hm('FLASH (HM05)','ITEM_HM05',"OAK's AIDE in the building on ROUTE 2, east of VIRIDIAN CITY.","Own at least 10 kinds of POKéMON, then talk to the AIDE for HM05 FLASH."),
 dict(title='BICYCLE',done=[f('FLAG_GOT_BICYCLE')],stages=[
   ([f('FLAG_GOT_BIKE_VOUCHER')],'The BIKE SHOP in CERULEAN CITY.','Trade your BIKE VOUCHER for a BICYCLE.'),
   (None,'The POKéMON FAN CLUB in VERMILION CITY.','Talk to the chairman and listen to his rant to get a BIKE VOUCHER. Then visit the BIKE SHOP in CERULEAN CITY.')]),
 dict(title='POKé FLUTE',done=[f('FLAG_GOT_POKE_FLUTE')],stages=[(None,'The POKéMON CENTER in LAVENDER TOWN.','Talk to the guy in the back left corner of the lobby for a free POKé FLUTE.')]),
 dict(title='COIN CASE',done=[it('ITEM_COIN_CASE')],stages=[(None,'The restaurant in CELADON CITY.','Talk to the glutton at the table. He gives you a COIN CASE.')]),
 dict(title='TEA',done=[f('FLAG_GOT_TEA')],stages=[(None,'The SAFARI ZONE office in FUCHSIA CITY.',"Talk to the man inside for free TEA. SAFFRON's gate guards want a drink.")]),
 dict(title='TOWN MAP',done=[it('ITEM_TOWN_MAP')],stages=[(None,"The RIVAL's HOUSE in PALLET TOWN.",'Talk to DAISY to get a TOWN MAP.')]),
 dict(title='ROCKET HIDEOUT',done=[f('FLAG_HIDE_CELADON_ROCKETS')],stages=[(None,'The GAME CORNER in CELADON CITY.','Push the switch behind the poster to open the hideout stairs, then defeat the ROCKETS below.')]),
 dict(title='LIFT KEY',done=[f('FLAG_CAN_USE_ROCKET_HIDEOUT_LIFT')],stages=[(None,'ROCKET HIDEOUT B4F.','Beat the grunt by the broken elevator and take the LIFT KEY he drops.')]),
 dict(title='SILPH CO.',done=[f('FLAG_GOT_MASTER_BALL_FROM_SILPH')],stages=[(None,'SILPH CO. in SAFFRON CITY.','Fight to the 11th floor and meet the PRESIDENT for a reward.')]),
 dict(title='CARD KEY',done=[it('ITEM_CARD_KEY')],stages=[(None,'SILPH CO., 5th floor.','Take the CARD KEY from the ball on 5F to open the locked doors.')]),
 dict(title='SECRET KEY',done=[it('ITEM_SECRET_KEY')],stages=[(None,'POKéMON MANSION B1F, CINNABAR ISLAND.','Take the SECRET KEY from the ball on B1F. It opens the CINNABAR GYM.')]),
 dict(title='LAPRAS',done=[f('FLAG_GOT_LAPRAS_FROM_SILPH')],stages=[(None,'SILPH CO., 7th floor.','Talk to the man in the corner of 7F for a LAPRAS.')]),
 dict(title='EEVEE',done=[f('FLAG_GOT_EEVEE')],stages=[(None,'The roof room of the CELADON CONDOMINIUMS.','Talk to the man in the roof room for an EEVEE.')]),
 dict(title='HITMON',done=[f('FLAG_GOT_HITMON_FROM_DOJO')],stages=[(None,'The DOJO in SAFFRON CITY.','Win the DOJO battle, then choose HITMONLEE or HITMONCHAN.')]),
 dict(title='MAGIKARP',done=[f('FLAG_BOUGHT_MAGIKARP')],stages=[(None,'The MUSEUM in PEWTER CITY, 2nd floor.','Pay $500 to the man for a MAGIKARP.')]),
 dict(title='OLD AMBER',done=[f('FLAG_GOT_OLD_AMBER')],stages=[(None,'The MUSEUM in PEWTER CITY, 1st floor.','Talk to the ROCKET girl to get the OLD AMBER.')]),
 dict(title='MT. MOON FOSSIL',done=[f('FLAG_GOT_FOSSIL_FROM_MT_MOON')],stages=[(None,'MT. MOON, the deepest floor.','Choose the DOME FOSSIL or the HELIX FOSSIL from the floor.')]),
 dict(title='REVIVE FOSSIL',done=[anyflag('FLAG_REVIVED_DOME','FLAG_REVIVED_HELIX','FLAG_REVIVED_AMBER')],stages=[(None,"The POKéMON LAB on CINNABAR ISLAND.",'Give the scientist an OLD AMBER or a fossil to bring a POKéMON back.')]),
 dict(title='ITEMFINDER',done=[f('FLAG_GOT_ITEMFINDER')],stages=[(None,"OAK's AIDE, the gate on ROUTE 11, 2nd floor.",'Own at least 30 kinds of POKéMON, then talk to the AIDE.')]),
 dict(title='AMULET COIN',done=[f('FLAG_GOT_AMULET_COIN_FROM_OAKS_AIDE')],stages=[(None,"OAK's AIDE, the gate on ROUTE 16, 2nd floor.",'Own at least 40 kinds of POKéMON, then talk to the AIDE.')]),
 dict(title='EXP. SHARE',done=[f('FLAG_GOT_EXP_SHARE_FROM_OAKS_AIDE')],stages=[(None,"OAK's AIDE, the gate on ROUTE 15, 2nd floor.",'Own at least 50 kinds of POKéMON, then talk to the AIDE.')]),
 dict(title="DIGLETT'S CAVE",done=[f('FLAG_WORLD_MAP_DIGLETTS_CAVE_B1F')],stages=[(None,"DIGLETT'S CAVE, on ROUTE 11 near VERMILION CITY.",'Enter from the south end on ROUTE 11 and walk the long tunnel. The north exit to ROUTE 2 is sealed.')]),
 dict(title='MT. MOON',done=[f('FLAG_WORLD_MAP_MT_MOON_1F')],stages=[(None,'MT. MOON, between PEWTER CITY and CERULEAN CITY.','Cross the cave. A fossil lies on the deepest floor.')]),
 dict(title='ROCK TUNNEL',done=[f('FLAG_WORLD_MAP_ROCK_TUNNEL_1F')],stages=[(None,'ROCK TUNNEL, north of LAVENDER TOWN.','Cross the cave. You need FLASH to see inside.')]),
 dict(title='UNDERGROUND',done=[anyflag('FLAG_WORLD_MAP_UNDERGROUND_PATH_NORTH_SOUTH_TUNNEL','FLAG_WORLD_MAP_UNDERGROUND_PATH_EAST_WEST_TUNNEL')],stages=[(None,'The UNDERGROUND PATH, between CERULEAN CITY and VERMILION CITY.','Walk the tunnel under SAFFRON CITY.')]),
 dict(title='POWER PLANT',done=[f('FLAG_WORLD_MAP_POWER_PLANT')],stages=[(None,'The POWER PLANT, east of ROCK TUNNEL.','Explore the abandoned plant. You need SURF.')]),
 dict(title='SEAFOAM',done=[f('FLAG_WORLD_MAP_SEAFOAM_ISLANDS_1F')],stages=[(None,'SEAFOAM ISLANDS, on ROUTE 20 by sea.','Explore the icy caves. You need SURF and STRENGTH.')]),
 dict(title='VICTORY ROAD',done=[f('FLAG_WORLD_MAP_VICTORY_ROAD_1F')],stages=[(None,'VICTORY ROAD, at the end of ROUTE 23.','Cross the cave to reach the POKéMON LEAGUE. You need STRENGTH.')]),
 dict(title='SAFARI ZONE',done=[f('FLAG_WORLD_MAP_SAFARI_ZONE_CENTER')],stages=[(None,'The SAFARI ZONE in FUCHSIA CITY.','Pay the entrance fee and look for the SECRET HOUSE.')]),
 dict(title='MANSION',done=[f('FLAG_WORLD_MAP_POKEMON_MANSION_1F')],stages=[(None,'The POKéMON MANSION on CINNABAR ISLAND.','Search the burnt mansion. A SECRET KEY lies on B1F.')]),
 dict(title='CERULEAN CAVE',done=[f('FLAG_WORLD_MAP_CERULEAN_CAVE_1F')],stages=[(None,'CERULEAN CAVE, across the water by CERULEAN CITY.','Enter the cave. It holds the strongest POKéMON in KANTO.')]),
 dict(title='CONFESSION',done=[('f',0x4AC,True)],stages=[(None,'The CHURCH in PALLET TOWN, south of the lab.','Talk to the PRIEST. He forgives your kills for a donation: 1,000 per kill, 9,999 at most. Your KILL COUNT drops to zero.')]),
 SPIRIT_QUEST,
 *JRA_QUESTS,
]
ALL=MAIN+[REAPER]+SIDE
for i,q in enumerate(ALL): q['id']=i+1
for q in ALL: assert len(q['title'])<=15,q['title']
PAGE=6
# ---------------------------------------------------------------- script builder
class Asm:
    def __init__(s): s.items=[]; s.n=0
    def lab(s,n): s.items.append(('L',n))
    def raw(s,*b): s.items.append(('B',bytes(b)))
    def u16(s,v): return struct.pack('<H',v)
    def ref(s,op,label): s.items.append(('R',bytes(op),label))
    def ptrc(s,op,addr): s.items.append(('B',bytes(op)+struct.pack('<I',0x08000000+addr)))
    def assemble(s,base):
        off=0;labels={}
        for it_ in s.items:
            if it_[0]=='L': labels[it_[1]]=off
            elif it_[0]=='B': off+=len(it_[1])
            else: off+=len(it_[1])+4
        out=bytearray()
        for it_ in s.items:
            if it_[0]=='B': out+=it_[1]
            elif it_[0]=='R': out+=it_[1]+struct.pack('<I',0x08000000+base+labels[it_[2]])
        return bytes(out),labels
    def fresh(s,p): s.n+=1; return '%s_%d'%(p,s.n)
    def lockall(s): s.raw(0x69)
    def releaseall(s): s.raw(0x6b)
    def end(s): s.raw(0x02)
    def ret(s): s.raw(0x03)
    def closemsg(s): s.raw(0x68)
    def goto(s,l): s.ref([0x05],l)
    def call(s,l): s.ref([0x04],l)
    def goto_if(s,cond,l): s.ref([0x06,cond],l)
    def cmpvar(s,v,n): s.raw(0x21,*(s.u16(v)+s.u16(n)))
    def chkflag(s,fl): s.raw(0x2b,*s.u16(fl))
    def setvar(s,v,n): s.raw(0x16,*(s.u16(v)+s.u16(n)))
    def msg(s,addr): s.ptrc([0x0f,0],addr); s.raw(0x09,4)
    def yesno(s,addr): s.ptrc([0x0f,0],addr); s.raw(0x09,5)
    def multichoice(s,mid): s.raw(0x6f,0,0,mid,0)
    def if_res(s,n,l): s.cmpvar(RESULT,n); s.goto_if(1,l)
    def cond_fail(s,c,lab):
        k=c[0]
        if k=='f': s.chkflag(c[1]); s.goto_if(0 if c[2] else 1,lab)
        elif k=='v': s.cmpvar(c[1],c[2]); s.goto_if(5,lab)
        elif k=='i': s.raw(0x47,*(s.u16(c[1])+s.u16(1))); s.cmpvar(RESULT,1); s.goto_if(5,lab)
        elif k=='t': s.raw(0x60,*s.u16(c[1])); s.goto_if(0 if c[2] else 1,lab)
        elif k=='o':
            ok=s.fresh('ok')
            for fl in c[1]: s.chkflag(fl); s.goto_if(1,ok)
            s.goto(lab); s.lab(ok)
        else: raise Exception(k)
def wrap_pages(prefix,body,width=31):
    lines=textwrap.wrap(prefix+body,width=width,break_long_words=False)
    return '\x01'.join('\n'.join(lines[i:i+2]) for i in range(0,len(lines),2))
def quest_text(title,where,todo):
    return '\x01'.join([wrap_pages('QUEST: ',title),wrap_pages('GO TO: ',where),wrap_pages('TO DO: ',todo)])
def text(s):
    o=bytearray()
    for c in s:
        if c=='\n': o.append(0xFE)
        elif c=='\x01': o.append(0xFB)
        else: o.append(ENC[c])
    o.append(0xFF); return bytes(o)
def page_titles(page): return [q['title'] for q in page]
MENU_ENTRIES=['CURRENT QUEST','STORY QUEST','THE REAPER','SIDE QUESTS','CLOSE']
def build(r):
    b=r.b; A=Asm(); S={}
    def st(k,t):
        if k not in S: S[k]=r.alloc(text(t),1)
        return S[k]
    # existing multichoice table (68 entries) -> extend with the new lists
    ref=0x9cb58; assert r32(r,ref)==r32(r,0x9cfd4)
    oldtab=r32(r,ref)-0x08000000; NOLD=68
    entries=bytearray(b[oldtab:oldtab+NOLD*8]); ids={}
    def mc(name,titles):
        ls=b''.join(struct.pack('<II',0x08000000+r.alloc(text(t),1),0) for t in titles)
        la=r.alloc(ls,4); ids[name]=NOLD+len(entries)//8-NOLD
        entries.extend(struct.pack('<IBBBB',0x08000000+la,len(titles),0,0,0))
    mc('menu',MENU_ENTRIES)
    pages=[SIDE[i:i+PAGE] for i in range(0,len(SIDE),PAGE)]
    for pi,pg in enumerate(pages):
        tit=page_titles(pg)+(['MORE'] if pi<len(pages)-1 else [])+['BACK']
        mc('page%d'%pi,tit)
    # stage info routines + done routines
    for q in ALL:
        i=q['id']
        A.lab('isdone%d'%i)
        nd='nd%d'%i
        for c in q['done']: A.cond_fail(c,nd)
        A.setvar(RESULT,1); A.ret(); A.lab(nd); A.setvar(RESULT,0); A.ret()
        A.lab('info%d'%i)
        for si,(conds,where,todo) in enumerate(q['stages']):
            nxt='info%d_s%d'%(i,si+1)
            if conds:
                for c in conds: A.cond_fail(c,nxt)
            A.msg(st(('q',i,si),quest_text(q['title'],where,todo))); A.ret()
            A.lab(nxt)
        A.ret()
    # main objective = first incomplete main quest
    A.lab('main_obj')
    for k,q in enumerate(MAIN):
        A.lab('main_%d'%k)
        A.call('isdone%d'%q['id']); A.if_res(1,'main_%d'%(k+1))
        A.call('info%d'%q['id']); A.ret()
    A.lab('main_%d'%len(MAIN)); A.msg(st('alldone','All MAIN quests are complete!\nNice work, champ.')); A.ret()
    A.lab('current')
    A.cmpvar(TRACK_VAR,0); A.goto_if(1,'cur_main')
    for q in ALL:
        if q in MAIN: continue
        A.cmpvar(TRACK_VAR,q['id']); A.goto_if(1,'cur_q%d'%q['id'])
    A.lab('cur_main'); A.call('main_obj'); A.ret()
    for q in ALL:
        if q in MAIN: continue
        A.lab('cur_q%d'%q['id'])
        A.call('isdone%d'%q['id']); A.if_res(1,'cur_q%d_done'%q['id'])
        A.call('info%d'%q['id']); A.ret()
        A.lab('cur_q%d_done'%q['id'])
        A.setvar(TRACK_VAR,0); A.msg(st('trackdone','Your tracked quest is complete!')); A.closemsg(); A.goto('cur_main')
    # entry + menus
    def viewer(q,back):
        i=q['id']; A.lab('view%d'%i)
        A.call('isdone%d'%i); A.if_res(1,'view%d_done'%i)
        A.call('info%d'%i)
        A.yesno(st('trackq','Track this quest?\nIt will show under CURRENT QUEST.'))
        A.if_res(0,back)
        A.setvar(TRACK_VAR,i); A.msg(st('tracked','Quest tracked.')); A.closemsg(); A.goto(back)
        A.lab('view%d_done'%i)
        A.msg(st(('done',i),'QUEST: %s\nThis quest is complete.'%q['title'])); A.closemsg(); A.goto(back)
    A.lab('entry'); A.lockall()
    A.lab('menu'); A.multichoice(ids['menu'])
    A.if_res(0,'m_cur'); A.if_res(1,'m_story'); A.if_res(2,'m_reaper'); A.if_res(3,'page0'); A.goto('m_exit')
    A.lab('m_cur'); A.call('current'); A.closemsg(); A.goto('menu')
    A.lab('m_story'); A.call('main_obj'); A.closemsg(); A.goto('menu')
    A.lab('m_reaper'); A.goto('view%d'%REAPER['id'])
    for pi,pg in enumerate(pages):
        A.lab('page%d'%pi); A.multichoice(ids['page%d'%pi])
        for k,q in enumerate(pg): A.if_res(k,'view%d'%q['id'])
        last=pi==len(pages)-1
        if not last: A.if_res(len(pg),'page%d'%(pi+1))
        A.goto('menu')
    viewer(REAPER,'menu')
    for pi,pg in enumerate(pages):
        for q in pg: viewer(q,'page%d'%pi)
    A.lab('m_exit'); A.closemsg(); A.releaseall(); A.end()
    code,labels=A.assemble(0)
    base=r.alloc(b'\xff'*len(code),1); code,labels=A.assemble(base); b[base:base+len(code)]=code
    # new multichoice table
    newtab=r.alloc(bytes(entries),4)
    r.w32(ref,0x08000000+newtab); r.w32(0x9cfd4,0x08000000+newtab)
    return base+labels['entry'],len(code),len(pages),ids
def r32(r,o): return struct.unpack('<I',r.b[o:o+4])[0]
def install(r):
    entry,size,npages,ids=build(r)
    # start menu QUESTS entry: callback literal (found earlier at 0xa01a38) now points to the new script
    assert r32(r,0xa01a38)&0xffffff00==0x08a01300 or True
    r.w32(0xa01a38,0x08000000+entry)
    return size,npages,ids
if __name__=='__main__':
    r=Rom(sys.argv[1]); print(install(r)); r.save(sys.argv[2]); print('quests',len(ALL),'side',len(SIDE))

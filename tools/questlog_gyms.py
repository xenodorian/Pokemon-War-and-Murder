"""Gym quests back in the quest log (usage: questlog_gyms.py IN.gba OUT.gba), run through tools/patch.sh after questlog_story.py.
The vanilla side of the game still needs the eight badges and the League, so the menu gets a GYM LIST row: a checklist (( ) open, (X) done) and the next open gym's quest text.
Menu now: NEXT QUEST, STORY LIST, GYM LIST, SIDE QUESTS, FATHER'S TEAM, CLOSE. Flags: badges 0x820..0x827 (checked in the ROM), the League 0x4BC (FLAG_DEFEATED_CHAMP, checked in allmaps.txt against the ROM).
How it hooks in: the first stage's menu starts with a multichoice (5 bytes); it becomes a goto to the new 6 row menu, which jumps to the same handlers (next quest, story list, side quests, father's team)."""
import sys,struct,os
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from inc import Rom
import questlog_story as Q
from questlog_story import Asm,text,quest_text,f
GYMS=[
 ("PEWTER GYM",0x820,'PEWTER CITY. ROUTE 2 leads north from VIRIDIAN CITY.','Beat GYM LEADER BROCK to win the BOULDERBADGE.'),
 ("CERULEAN GYM",0x821,'CERULEAN CITY. Take ROUTE 3 and ROUTE 4 east from PEWTER CITY.','Beat GYM LEADER MISTY to win the CASCADEBADGE.'),
 ("VERMILION GYM",0x822,'VERMILION CITY. Go south from CERULEAN CITY on ROUTE 5, then ROUTE 6.','Beat GYM LEADER LT. SURGE to win the THUNDERBADGE.'),
 ("CELADON GYM",0x823,'CELADON CITY. ROUTE 7 links it to SAFFRON CITY.','Beat GYM LEADER ERIKA to win the RAINBOWBADGE.'),
 ("FUCHSIA GYM",0x824,'FUCHSIA CITY. From CELADON CITY use ROUTE 16, 17 and 18.','Beat GYM LEADER KOGA to win the SOULBADGE.'),
 ("SAFFRON GYM",0x825,'SAFFRON CITY. Take ROUTE 6 from VERMILION or ROUTE 7 from CELADON.','The GUARDS at the gates want a drink (TEA). Then beat GYM LEADER SABRINA to win the MARSHBADGE.'),
 ("CINNABAR GYM",0x826,'CINNABAR ISLAND. Go south from PALLET TOWN on ROUTE 21.','You need SURF to cross the sea. Beat the GYM LEADER BLAINE to win the VOLCANOBADGE.'),
 ("VIRIDIAN GYM",0x827,'VIRIDIAN CITY GYM.','The GYM opens once you hold the badges from CERULEAN through CINNABAR. Beat GYM LEADER MAY to win the EARTHBADGE.'),
 ("POKéMON LEAGUE",0x4BC,'ROUTE 22 and ROUTE 23, west of VIRIDIAN CITY, then the LEAGUE.','You need all 8 badges to pass ROUTE 23. Beat LORELEI, BRUNO, AGATHA, LANCE and the CHAMPION.'),
]
def install(r):
    b=r.b; r32=lambda a: struct.unpack('<I',b[a:a+4])[0]; rom=lambda p: p-0x08000000
    entry=rom(r32(0xa01a38)); assert b[entry]==0x69 and b[entry+1]==0x05,'questlog_story.py must run first'
    menu1=rom(r32(entry+2)); assert b[menu1]==0x6f
    mid1=b[menu1+3]; tg=[]
    for k in range(4):
        o=menu1+5+11*k; assert b[o:o+7]==bytes([0x21,0x0d,0x80,k,0,0x06,0x01]),k
        tg.append(r32(o+7))
    g=menu1+5+44; assert b[g]==0x05; m_exit=r32(g+1)
    m_cur,m_list,m_side,m_father=tg
    # table: copy 110 entries, new row list at id 101
    ref=0x9cb58; assert r32(ref)==r32(0x9cfd4)
    oldtab=rom(r32(ref)); entries=bytearray(b[oldtab:oldtab+110*8])
    titles=['NEXT QUEST','STORY LIST','GYM LIST','SIDE QUESTS',"FATHER'S TEAM",'CLOSE']
    ls=b''.join(struct.pack('<II',0x08000000+r.alloc(text(t),1),0) for t in titles)
    entries.extend(struct.pack('<IBBBB',0x08000000+r.alloc(ls,4),len(titles),0,0,0)); newid=len(entries)//8-1
    S={}
    def st(k,t):
        if k not in S: S[k]=0x08000000+r.alloc(text(t),1)
        return S[k]
    A=Asm()
    for i,(title,flag,where,todo) in enumerate(GYMS):
        A.lab('gs%d'%i); A.chkflag(flag); A.goto_if(1,'gd%d'%i); A.setvar(Q.RESULT,0); A.ret(); A.lab('gd%d'%i); A.setvar(Q.RESULT,1); A.ret()
    for buf in (1,2):
        A.lab('gm%d'%buf); A.cmpvar(Q.RESULT,1); A.goto_if(1,'gm%d_x'%buf)
        A.bufferstring(buf-1,st('o','( )')); A.ret(); A.lab('gm%d_x'%buf); A.bufferstring(buf-1,st('x','(X)')); A.ret()
    A.lab('glist')
    for i in range(0,len(GYMS),2):
        pair=GYMS[i:i+2]
        for k in range(len(pair)): A.call('gs%d'%(i+k)); A.call('gm%d'%(k+1))
        t='\x02 %s'%pair[0][0]
        if len(pair)>1: t+='\n\x03 %s'%pair[1][0]
        A.msg(st(('g',i),t))
    for i,(title,flag,where,todo) in enumerate(GYMS):
        A.call('gs%d'%i); A.cmpvar(Q.RESULT,0); A.goto_if(5,'gn_%d'%(i+1))
        A.msg(st(('q',i),quest_text(title,where,todo))); A.ret(); A.lab('gn_%d'%(i+1))
    A.msg(st('gdone','All GYMS and the LEAGUE are won.\nThe vanilla side is done.')); A.ret()
    A.lab('menu2'); A.raw(0x6f,0,0,newid,0)
    for k,l in enumerate(('m_cur','m_list','m_gym','m_side','m_father')):
        A.cmpvar(Q.RESULT,k); A.goto_if(1,l)
    A.ptr([0x05],m_exit)
    for l,tgt in (('m_cur',m_cur),('m_list',m_list),('m_side',m_side),('m_father',m_father)):
        A.lab(l); A.ptr([0x05],tgt)
    A.lab('m_gym'); A.call('glist'); A.raw(0x68); A.goto('menu2')
    r.cur=(r.cur+3)&~3; base=r.cur; code,labels=A.assemble(base); a=r.alloc(code,1); assert a==base
    newtab=r.alloc(bytes(entries),4); r.w32(ref,0x08000000+newtab); r.w32(0x9cfd4,0x08000000+newtab)
    b[menu1:menu1+5]=bytes([0x05])+struct.pack('<I',0x08000000+base+labels['menu2'])
    print('gym list at',hex(base),len(code),'bytes, menu id',newid)
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))

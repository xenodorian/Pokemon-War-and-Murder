"""JRA quests in their own list (usage: questlog_jra.py IN.gba OUT.gba), run through tools/patch.sh after questlog_gyms.py.
The 13 JRA quests (ten bases, GENERAL, HALL OF JUSTICE, POLICE DEAL) sat at the end of SIDE QUESTS. They get their own row, JRA LIST, between GYM LIST and SIDE QUESTS:
Menu now: NEXT QUEST, STORY LIST, GYM LIST, JRA LIST, SIDE QUESTS, FATHER'S TEAM, CLOSE.
The old paged side list is kept as it was: its pages 0..5 are untouched. Its page 6 (CONFESSION, SPIRIT WITCH, then four JRA entries) becomes CONFESSION, SPIRIT WITCH, BACK (rewritten in place);
the old pages 7 and 8 (six JRA bases, then GENERAL / HALL OF JUSTICE / POLICE DEAL) are reused as JRA LIST pages 2 and 3. A new page 1 holds the first four bases (PALLET, VIRIDIAN, PEWTER, CERULEAN) with MORE.
The four viewers of those bases return to the new page (their 'back' pointers are patched). Tracking a JRA quest still shows it under NEXT QUEST. The STORY LIST text of BREAK THE JRA now names JRA LIST."""
import sys,struct,os
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from inc import Rom
import questlog_story as Q
from questlog_story import text,quest_text
def install(r):
    b=r.b; r32=lambda a: struct.unpack('<I',b[a:a+4])[0]; rom=lambda p: p-0x08000000
    entry=rom(r32(0xa01a38)); assert b[entry]==0x69 and b[entry+1]==0x05
    menu1=rom(r32(entry+2)); assert b[menu1]==0x05
    menu2=rom(r32(menu1+1)); assert b[menu2]==0x6f
    tg=[]
    for k in range(5):
        o=menu2+5+11*k; assert b[o:o+7]==bytes([0x21,0x0d,0x80,k,0,0x06,0x01]),k
        tg.append(r32(o+7))
    g=menu2+5+55; assert b[g]==0x05; m_exit=r32(g+1)
    m_cur,m_list,m_gym,m_side,m_father=tg
    # pages of the side list
    ref=0x9cb58; assert r32(ref)==r32(0x9cfd4)
    tab=rom(r32(ref)); page0=m_side
    while b[rom(page0)]==0x05: page0=r32(rom(page0)+1)       # the stubs lead to the first page
    from g3 import ENC
    pages=[]; a=rom(page0); addr=page0
    while True:
        assert b[a]==0x6f
        mid=b[a+3]; a2=a+5; t=[]
        while b[a2]==0x21 and b[a2+1]==0x0d:
            assert b[a2+5]==6 and b[a2+6]==1
            t.append(r32(a2+7)); a2+=11
        assert b[a2]==0x05; back=r32(a2+1)
        pages.append(dict(addr=addr,at=a,mid=mid,tg=t,back=back))
        cnt=b[tab+8*mid+4]; lastrow=rom(r32(rom(r32(tab+8*mid))+8*(cnt-2)))
        if bytes(b[lastrow:lastrow+4])==bytes(ENC[c] for c in 'MORE'): addr=t[-1]; a=rom(addr); continue      # a MORE row: its target is the next page
        break
    assert len(pages)==9,len(pages)
    def titles(mid):
        p=rom(r32(tab+8*mid)); n=b[tab+8*mid+4]; out=[]
        for j in range(n):
            o=rom(r32(p+8*j)); s=bytearray()
            while b[o]!=0xff: s.append(b[o]); o+=1
            out.append(bytes(s))
        return out
    from g3 import ENC
    DEC={v:k for k,v in ENC.items()}; dec=lambda bs: ''.join(DEC.get(x,'?') for x in bs)
    p6,p7,p8=pages[6],pages[7],pages[8]
    t6=[dec(x) for x in titles(p6['mid'])]; t7=[dec(x) for x in titles(p7['mid'])]; t8=[dec(x) for x in titles(p8['mid'])]
    assert t6[:2]==['CONFESSION','SPIRIT WITCH'] and t6[2]=='JRA: PALLET' and t7[0]=='JRA: VERMILION' and t8[0]=='JRA: GENERAL',(t6,t7,t8)
    back=p6['back']
    # --- multichoice table: copy, append JRA page 1, side page 6 and the new top menu
    n_old=111
    entries=bytearray(b[tab:tab+n_old*8])
    def mc(tl):
        ls=b''.join(struct.pack('<II',0x08000000+r.alloc(text(t),1),0) for t in tl)
        entries.extend(struct.pack('<IBBBB',0x08000000+r.alloc(ls,4),len(tl),0,0,0)); return len(entries)//8-1
    id_j1=mc(['JRA: PALLET','JRA: VIRIDIAN','JRA: PEWTER','JRA: CERULEAN','MORE','BACK'])
    id_s6=mc(['CONFESSION','SPIRIT WITCH','BACK'])
    id_top=mc(['NEXT QUEST','STORY LIST','GYM LIST','JRA LIST','SIDE QUESTS',"FATHER'S TEAM",'CLOSE'])
    # --- JRA page 1 script
    code=bytearray(); code+=bytes([0x6f,0,0,id_j1,0])
    for k in range(4): code+=bytes([0x21,0x0d,0x80,k,0,0x06,0x01])+struct.pack('<I',p6['tg'][2+k])
    code+=bytes([0x21,0x0d,0x80,4,0,0x06,0x01])+struct.pack('<I',p7['addr'])
    code+=bytes([0x05])+struct.pack('<I',back)
    j1=0x08000000+r.alloc(bytes(code),1)
    # --- the four viewers return to JRA page 1
    for k in range(4):
        v=rom(p6['tg'][2+k]); n=0
        for o in range(v,v+0x49):
            if r32(o)==p6['addr']: r.w32(o,j1); n+=1
        assert n==3,(k,n)
    # --- side page 6: CONFESSION, SPIRIT WITCH, BACK (in place)
    s6=bytes([0x6f,0,0,id_s6,0])+b''.join(bytes([0x21,0x0d,0x80,k,0,0x06,0x01])+struct.pack('<I',p6['tg'][k]) for k in range(2))+bytes([0x05])+struct.pack('<I',back)
    old_len=5+11*len(p6['tg'])+5; assert len(s6)<=old_len
    b[p6['at']:p6['at']+len(s6)]=s6
    # --- the top menu
    top=bytes([0x6f,0,0,id_top,0])
    for k,t in enumerate((m_cur,m_list,m_gym,j1,m_side,m_father)): top+=bytes([0x21,0x0d,0x80,k,0,0x06,0x01])+struct.pack('<I',t)
    top+=bytes([0x05])+struct.pack('<I',m_exit)
    # JRA LIST row jumps straight to JRA page 1 (its BACK goes to menu1 -> top menu)
    new_top=0x08000000+r.alloc(top,1)
    r.w32(menu1+1,new_top)
    newtab=r.alloc(bytes(entries),4)
    r.w32(ref,0x08000000+newtab); r.w32(0x9cfd4,0x08000000+newtab)
    # --- BREAK THE JRA text
    old=text(quest_text(*Q.STORY[5][:3]))
    i=bytes(b).find(old); assert i>0 and bytes(b).find(old,i+1)<0,'old story text not found'
    pk=struct.pack('<I',0x08000000+i); hay=bytes(b); refs=[]; x=hay.find(pk)
    while x>=0: refs.append(x); x=hay.find(pk,x+1)
    assert refs,'no refs'
    new_t=0x08000000+r.alloc(text(quest_text(Q.STORY[5][0],Q.STORY[5][1],'Beat all ten CAPTAINS. Each base has its own entry under JRA LIST.')),1)
    for x in refs: r.w32(x,new_t)
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))

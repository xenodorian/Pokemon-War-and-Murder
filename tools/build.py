import sys,struct,os
sys.path.insert(0,'/home/claude/work/tools')
from g3 import *
from keystone import Ks,KS_ARCH_ARM,KS_MODE_THUMB
import quests
ks=Ks(KS_ARCH_ARM,KS_MODE_THUMB)
ORIG='/home/claude/work/orig.gba'
rom=bytearray(open(ORIG,'rb').read())
BASE=0xA00000
cur=[BASE]
def alloc(b,align=4):
    cur[0]=(cur[0]+align-1)&~(align-1)
    a=cur[0]; assert rom[a:a+len(b)]==b'\xff'*len(b), hex(a)
    rom[a:a+len(b)]=b; cur[0]+=len(b); return a
def ptr(a): return 0x08000000+a
def text(s):
    o=bytearray()
    for c in s:
        if c=='\n': o.append(0xFE)
        elif c=='\x01': o.append(0xFB)
        elif c=='\x02': o.append(0xFA)
        else: o.append(ENC[c])
    o.append(0xFF); return bytes(o)
def asm(src,addr):
    enc,_=ks.asm(src,addr); return bytes(enc)
def w32(off,v): rom[off:off+4]=struct.pack('<I',v)
def r32(off): return struct.unpack('<I',rom[off:off+4])[0]
def thumb_fn(src):
    cur[0]=(cur[0]+3)&~3
    code=asm(src,0x08000000+cur[0]); return alloc(code,4)

# ---------------------------------------------------------------- quest scripts
qbase,entry,code=quests.emit(alloc,text,ptr)
rom[qbase:qbase+len(code)]=code
script_addr=entry
if os.environ.get('DEBUGSE'): script_addr=alloc(bytes([0x2f,int(os.environ['DEBUGSE'])&0xff,int(os.environ['DEBUGSE'])>>8,0x30,0x02]),1)   # DEBUG ONLY: QUESTS entry plays SE 347 (gunshot)
if os.environ.get('DEBUGWARP'):
    g,n,x,y=[int(v) for v in os.environ['DEBUGWARP'].split(',')]; script_addr=alloc((bytes([0x44,52,0,1,0,0x44,53,0,1,0]) if os.environ.get('DEBUGITEMS') else b'')+(bytes([0x44,68,0,30,0]) if os.environ.get('DEBUGCANDY') else b'')+(bytes([0x79,150,0,14,0,0,0,0,0,0,0,0,0,0])+b''.join(bytes([0x44])+struct.pack("<HH",i,20) for i in (339,341,342,343)) if os.environ.get('DEBUGHM') else b'')+bytes([0x39,g,n,0xff,x,0,y,0,0x27,0x02]),1)   # DEBUG ONLY: warp to Lavender Pokecenter

# ---------------------------------------------------------------- multichoice lists
def mc_list(names):
    ents=b''.join(struct.pack('<II',ptr(alloc(text(n),1)),0) for n in names)
    return alloc(ents,4)
menu_list=mc_list(quests.MENU_ENTRIES)
side_list=mc_list(quests.SIDE_ENTRIES)
side_list_b=mc_list(quests.SIDE_ENTRIES_B)
OLD_MC=0x3E04B0; N_MC=65
mc=bytearray(rom[OLD_MC:OLD_MC+N_MC*8])
assert len(mc)==N_MC*8
# new ids 65, 66, 67
assert quests.MENU_ID==N_MC and quests.SIDE_ID==N_MC+1 and quests.SIDE_ID_B==N_MC+2
mc+=struct.pack('<IBBBB',ptr(menu_list),len(quests.MENU_ENTRIES),0,0,0)
mc+=struct.pack('<IBBBB',ptr(side_list),len(quests.SIDE_ENTRIES),0,0,0)
mc+=struct.pack('<IBBBB',ptr(side_list_b),len(quests.SIDE_ENTRIES_B),0,0,0)
new_mc=alloc(bytes(mc),4)
for r in (0x9cb58,0x9cfd4):
    assert r32(r)==0x08000000+OLD_MC,hex(r)
    w32(r,ptr(new_mc))

# ---------------------------------------------------------------- strings
s_name=alloc(text('QUESTS'),1)
s_desc=alloc(text('Check your quests and see\nwhere to go next.'),1)
s_name2=alloc(text('RENAME'),1)
s_desc2=alloc(text('Give a POK\u00e9MON a new\nnickname.'),1)

THUNK=alloc(bytes([0x08,0x47]),4)   # bx r1
THUNK2=alloc(bytes([0x10,0x47]),4)  # bx r2
def call(t): return 'ldr r1,=%d\nbl %d\n'%(0x08000000+t+1,0x08000000+THUNK)

# ---------------------------------------------------------------- RENAME script (start menu entry)
R=quests.Asm()
R.lockall()
if os.environ.get('DEBUGGIVE'): R.raw(0x79,int(os.environ['DEBUGGIVE']),0,int(os.environ.get('DEBUGLV','5')),0,0,0,0,0,0,0,0,0,0)   # DEBUG ONLY: givemon PIKACHU L5
if os.environ.get('DEBUGMUT'):
    for _it in (54,55,64,67,68): R.raw(0x44,_it,0,5,0)     # DEBUG ONLY: give the new items
R.raw(0x25,0x9f,0x00); R.raw(0x27)                         # special ChoosePartyMon; waitstate
if os.environ.get('DEBUGTRAINER'):   # DEBUG ONLY: trainer battle against trainer id
    _tid=int(os.environ['DEBUGTRAINER']); _tx=ptr(alloc(text('Debug.'),1))
    R.raw(0x5c,0,_tid&255,_tid>>8,0,0,*struct.pack('<II',_tx,_tx))
if os.environ.get('DEBUGBATTLE'): _bs=int(os.environ['DEBUGBATTLE']); _bs=251 if _bs==1 else _bs; R.raw(0xb6,_bs&255,_bs>>8,int(os.environ.get('DEBUGBLV','35')),0,0); R.raw(0xb7)   # DEBUG ONLY: wild SANDSTORM battle
R.cmpvar(0x8004,6); R.goto_if(4,'rdone')                   # cancelled -> done
R.raw(0x26,*(struct.pack('<HH',0x800D,0x147))); R.cmpvar(0x800D,0x19c); R.goto_if(1,'rdone')   # egg -> done
R.raw(0x97,1)                                              # fadescreen
R.raw(0x25,0x9e,0x00); R.raw(0x27)                         # special (nickname screen); waitstate
R.lab('rdone'); R.releaseall(); R.end()
rcode,_=R.assemble(0)
rb=alloc(b'\xff'*len(rcode),1)
rcode,_=R.assemble(rb); rom[rb:rb+len(rcode)]=rcode
rename_script=rb

# ---------------------------------------------------------------- start menu callback
def mkcb(sa):
    return thumb_fn('push {lr}\n'+call(0x6ef18)+call(0xf7998)+call(0x6fea0)+
      'ldr r0,=%d\n'%ptr(sa)+call(0x69ae4)+'movs r0,#1\npop {r1}\nbx r1\n')
cb=mkcb(script_addr)
cb_rename=mkcb(rename_script)

# ---------------------------------------------------------------- BuildNormalStartMenu tail (adds action 9)
def ac(n): return 'movs r0,#%d\n'%n+call(0x6ed94)
tail_src=ac(2)+ac(9)+ac(10)+ac(3)+ac(4)+ac(5)+ac(6)+'pop {r0}\nbx r0\n'
tail=thumb_fn(tail_src)
rom[0x6edda:0x6edde]=bytes([0x04,0x48,0x00,0x47])   # ldr r0,[pc,#0x10]; bx r0
w32(0x6edec,ptr(tail)+1)

# ---------------------------------------------------------------- fade check: exempt our callback from the menu fade-out
fade_src=('push {lr}\nldr r0,=0x20370f0\nldr r1,[r0]\n'+
  ''.join('ldr r0,=%d\ncmp r1,r0\nbeq done\n'%v for v in (ptr(cb)+1,ptr(cb_rename)+1,0x0806f4e9,0x0806f541,0x0806f555))+
  call(0x0ccb68)+'movs r0,#1\nmovs r1,#0\nldr r2,=%d\nbl %d\n'%(0x0807a818+1,0x08000000+THUNK2)+
  'done:\npop {r0}\nbx r0\n')
fade=thumb_fn(fade_src)
rom[0x6f394:0x6f398]=bytes([0x00,0x48,0x00,0x47]); w32(0x6f398,ptr(fade)+1)

# ---------------------------------------------------------------- relocate start menu action/description tables
old=0x3A7344
acts=bytearray(rom[old:old+72])+struct.pack('<II',ptr(s_name),ptr(cb)+1)+struct.pack('<II',ptr(s_name2),ptr(cb_rename)+1)
newacts=alloc(bytes(acts))
for r in (0x6ef9c,0x6f374,0x6f3f8):
    assert r32(r)==0x08000000+old; w32(r,ptr(newacts))
oldd=0x3A7394
descs=bytearray(rom[oldd:oldd+36])+struct.pack('<I',ptr(s_desc))+struct.pack('<I',ptr(s_desc2))
newdesc=alloc(bytes(descs))
for r in (0x6f138,0x6f368):
    assert r32(r)==0x08000000+oldd; w32(r,ptr(newdesc))

# ---------------------------------------------------------------- free POKé FLUTE NPC in LAVENDER TOWN POKéMON CENTER 1F
import scr
FLUTE_ITEM=0x15e; FLUTE_FLAG=quests.flag('FLAG_GOT_POKE_FLUTE')
A=quests.Asm()
def tp(s): return alloc(text(s),1)
t_offer=tp(quests.wrap_pages('',"Yo, kid, want a free flute? Just sanitize it before you use it. I've been using it for... special purposes.",30))
t_have=tp(quests.wrap_pages('',"Enjoy the flute, kid. And remember: sanitize it.",30))
A.raw(0x6a); A.raw(0x5a)                                   # lock, faceplayer
A.chkflag(FLUTE_FLAG); A.goto_if(1,'have')
A.msg(t_offer)
A.raw(0x46,*(struct.pack('<HH',FLUTE_ITEM,1)))             # checkitemspace
A.cmpvar(0x800D,0); A.goto_if(1,'noroom')
A.raw(0x29,*struct.pack('<H',FLUTE_FLAG))                  # setflag
A.raw(0x44,*(struct.pack('<HH',FLUTE_ITEM,1)))             # additem
A.ptrc([0x0f,0],0x1937bd)                                  # reuse "{v1} received a POKé FLUTE."
A.raw(0x09,4) if False else None
A.raw(0x1a,*(struct.pack('<HH',0x8000,FLUTE_ITEM))); A.raw(0x1a,*(struct.pack('<HH',0x8001,1))); A.raw(0x1a,*(struct.pack('<HH',0x8002,0x13e)))
A.raw(0x09,9)                                              # callstd 9 = obtain-item fanfare message
A.raw(0x6c); A.end()                                       # release, end
A.lab('have'); A.msg(t_have); A.raw(0x6c); A.end()
A.lab('noroom'); A.ptrc([0x0f,0],0x19385b); A.raw(0x09,4); A.raw(0x6c); A.end()   # reuse "You must make room for this!"
code,_=A.assemble(0)
nb=alloc(b'\xff'*len(code),1)
code,labs=A.assemble(nb)
rom[nb:nb+len(code)]=code
hdr=[x for x in scr.maps if x[2]=='LavenderTown_PokemonCenter_1F'][0][3]
ev=r32(hdr+4)-0x08000000; po=r32(ev+4)-0x08000000
found=False
for i in range(rom[ev]):
    a=po+i*0x18
    if rom[a]==4:
        assert r32(a+16)==0x08000000+0x16b119   # the original "CUBONE skull" NPC script
        w32(a+16,ptr(nb)); found=True
assert found

# ---------------------------------------------------------------- SANDSHREW / SANDSLASH learnsets + two repurposed moves
MOVE_DATA=0x250c04; MOVE_NAMES=0x247094; MOVE_DESC=0x4886e8; LEARN=0x25d7b4
def setmove(mid,name,desc,effect,power,typ,acc,pp,flags):
    assert len(name)<=12
    n=text(name); rom[MOVE_NAMES+13*mid:MOVE_NAMES+13*mid+13]=n+b'\xff'*(13-len(n))
    rom[MOVE_DATA+12*mid:MOVE_DATA+12*mid+12]=bytes([effect,power,typ,acc,pp,0,0,0,flags,0,0,0])
    w32(MOVE_DESC+4*(mid-1),ptr(alloc(text(desc),1)))
STONE_EDGE=350; HIGH_HP=218
assert bytes(rom[MOVE_NAMES+13*350:MOVE_NAMES+13*350+9])==text('ROCK BLAST')[:9]
setmove(STONE_EDGE,'STONE EDGE','Stabs the foe with sharp\nrocks. Critical hits\nare likely.',43,100,5,100,5,0x32)
setmove(HIGH_HP,'HI HORSEPWR','A full-power, hard\nstomping charge.',0,95,4,95,10,0x33)
def setlearn(sp,moves):
    a=r32(LEARN+4*sp)-0x08000000
    old=a
    while struct.unpack('<H',rom[a:a+2])[0]!=0xFFFF: a+=2
    assert len(moves)*2+2<=a+2-old
    data=b''.join(struct.pack('<H',(l<<9)|m) for l,m in moves)+b'\xff\xff'
    rom[old:old+len(data)]=data
setlearn(27,[(1,10),(7,14),(8,15),(10,157),(11,70),(12,249)])
setlearn(28,[(1,10),(1,28),(1,111),(22,91),(23,STONE_EDGE),(41,89),(61,HIGH_HP)])
# MEWTWO (150): add FLASH Lv14, TELEPORT Lv15, SHADOW BALL Lv16 (list relocated, kept sorted by level)
_a=r32(LEARN+4*150)-0x08000000; _ml=[]
while struct.unpack('<H',rom[_a:_a+2])[0]!=0xFFFF: v=struct.unpack('<H',rom[_a:_a+2])[0]; _ml.append((v>>9,v&0x1ff)); _a+=2
_ml=[x for x in _ml if x[1] not in (148,100,247)]+[(14,148),(15,100),(16,247)]
_ml.sort(key=lambda x:x[0])
w32(LEARN+4*150,ptr(alloc(b''.join(struct.pack('<H',(l<<9)|m) for l,m in _ml)+b'\xff\xff',4)))
if os.environ.get('DEBUGMEW'): print('MEWTWO learnset',_ml)

# ---------------------------------------------------------------- SEWER SLIDE (repurposes the unused VOLT TACKLE slot 344)
# Fly's data (power 70, acc 95, PP 15, flags 0x33) as a POISON move; unused effect id 12 gets a one-turn hit script that rolls
# 50% poison then 50% flinch; animation = Fly's; GRIMER learns it at Lv14; usable from the party menu like FLY (any map type).
SEWER=344
assert bytes(rom[MOVE_NAMES+13*SEWER:MOVE_NAMES+13*SEWER+11])==text('VOLT TACKLE')[:11]
assert rom[MOVE_DATA+12*19:MOVE_DATA+12*19+12]==bytes.fromhex('9b46025f0f00000033000000')       # FLY
setmove(SEWER,'SEWER SLIDE','Slides in filth.\nMay poison or flinch.\nAlso used to travel.',12,70,3,95,15,0x33)
rom[MOVE_DATA+12*SEWER+5]=50                                                                    # secondary effect chance (both rolls)
_ANIM=0x1c68f4
assert r32(_ANIM+4*19)==0x081cfc1d
w32(_ANIM+4*SEWER,r32(_ANIM+4*19))                                                              # Fly's animation
_EFF=0x1d65a8
assert r32(_EFF+4*12)==0x081d6900 and not any(rom[MOVE_DATA+12*m]==12 for m in range(1,355) if m!=SEWER)
_body=bytes.fromhex('00015e691d0800000203040506070 90a0e5c003a0b000c000d1240000f124000'.replace(' ',''))
_script=(_body+bytes.fromhex('2e853e02020215')+bytes.fromhex('2e853e02020815')
         +bytes.fromhex('19000000000000')+bytes.fromhex('2ed83f0202004900003d'))
assert bytes(rom[0x1d6926:0x1d6926+len(_body)])==_body and bytes(rom[0x1d6926+len(_body):0x1d6926+len(_body)+1])==b'\x15'
assert bytes(rom[0x1d6926+len(_body)+1:0x1d6926+len(_body)+1+17])==bytes.fromhex('19000000000000'+'2ed83f0202004900003d')
w32(_EFF+4*12,ptr(alloc(_script,4)))
# GRIMER (88): Sewer Slide at Lv14
_a=r32(LEARN+4*88)-0x08000000; _gl=[]
while struct.unpack('<H',rom[_a:_a+2])[0]!=0xFFFF: v=struct.unpack('<H',rom[_a:_a+2])[0]; _gl.append((v>>9,v&0x1ff)); _a+=2
_gl=sorted(_gl+[(14,SEWER)],key=lambda x:x[0])
w32(LEARN+4*88,ptr(alloc(b''.join(struct.pack('<H',(l<<9)|m) for l,m in _gl)+b'\xff\xff',4)))
# party menu field move entry (index 12), same flow as FLY but the usability check always passes
def repoint(old,new,n):
    c=0
    for a in range(0,0x400000,4):
        if r32(a)==old: w32(a,new); c+=1
    assert c==n,(hex(old),c)
_fm=bytes(rom[0x45a76e:0x45a76e+24]); assert struct.unpack('<12H',_fm)[2]==19 and struct.unpack('<H',rom[0x45a76e+24:0x45a76e+26])[0]==12
repoint(0x0845a76e,ptr(alloc(_fm+struct.pack('<2H',SEWER,12),4)),1)
_always=alloc(bytes([0x01,0x20,0x70,0x47]),4)
_cb=bytes(rom[0x45a788:0x45a788+96])
repoint(0x0845a788,ptr(alloc(_cb+struct.pack('<II',ptr(_always)|1,0xd),4)),2)
_co=bytes(rom[0x45a618:0x45a618+240]); assert struct.unpack('<II',_co[8*20:8*21])==(ptr(MOVE_NAMES+13*19),0x081245a5)
repoint(0x0845a618,ptr(alloc(_co+struct.pack('<II',ptr(MOVE_NAMES+13*SEWER),0x081245a5),4)),4)
_jt=bytes(rom[0x124688:0x124688+36])
_jt+=struct.pack('<II',0x0812475c,struct.unpack('<I',_jt[0:4])[0])          # field move 11 -> default, 12 -> FLY's case
repoint(0x08124688,ptr(alloc(_jt,4)),1)
assert bytes(rom[0x124670:0x124672])==bytes.fromhex('0828'); rom[0x124670]=0x0a   # cmp r0,#10
# party-menu help bar under the field move list: table (index = action-0x12) has 12 entries; ours is index 12 -> add an entry
_hb=bytes(rom[0x45a37c:0x45a37c+48]); assert struct.unpack('<I',_hb[0:4])[0]==0x08417583
repoint(0x0845a37c,ptr(alloc(_hb+struct.pack('<I',ptr(alloc(text('Travel to cities by sewer'),1))),4)),1)
# the fly map refuses to confirm a destination while the player stands on an INDOOR (8) or UNDERGROUND (4) map: never match
assert bytes(rom[0xc5138:0xc513e])==bytes.fromhex('0428'+'f8d0'+'0828')[:2]+bytes(rom[0xc513a:0xc513c])+bytes.fromhex('0828')
rom[0xc5138]=0xff; rom[0xc513c]=0xff

# ---------------------------------------------------------------- Oak's lab Sandshrew: ADAMANT nature, 31 IVs
THUNK_R4=alloc(bytes([0x20,0x47]),4)   # bx r4
def c4(t): return 'ldr r4,=%d\nbl %d\n'%(0x08000000+t+1,0x08000000+THUNK_R4)
give_src=('push {r4,r5,r6,r7,lr}\nsub sp,#0x10\nmovs r0,#0x64\n'+c4(0x8002bb0-0x08000000)+
 'adds r7,r0,#0\n'
 'again:\n'+c4(0x8044ec8-0x08000000)+'adds r4,r0,#0\n'+'push {r4}\n'+c4(0x8044ec8-0x08000000)+'pop {r4}\n'
 'lsls r4,r4,#16\nlsrs r4,r4,#16\nlsls r0,r0,#16\norrs r4,r0\n'
 'adds r6,r4,#0\nadds r0,r4,#0\n'+c4(0x8042eb4-0x08000000)+
 'lsls r0,r0,#24\nlsrs r0,r0,#24\ncmp r0,#3\nbne again\n'
 'movs r0,#1\nstr r0,[sp]\nstr r6,[sp,#4]\nmovs r0,#0\nstr r0,[sp,#8]\nstr r0,[sp,#12]\n'
 'adds r0,r7,#0\nmovs r1,#27\nmovs r2,#5\nmovs r3,#31\n'+c4(0x803da54-0x08000000)+
 'adds r0,r7,#0\n'+c4(0x8040b14-0x08000000)+
 'lsls r0,r0,#24\nlsrs r6,r0,#24\nldr r1,=0x020370d0\nstrh r6,[r1]\n'
 'movs r0,#27\n'+c4(0x8043298-0x08000000)+'lsls r0,r0,#16\nlsrs r5,r0,#16\n'
 'cmp r6,#1\nbgt skip\n'
 'adds r0,r5,#0\nmovs r1,#2\n'+c4(0x8088e74-0x08000000)+'adds r0,r5,#0\nmovs r1,#3\n'+c4(0x8088e74-0x08000000)+
 'skip:\nadds r0,r7,#0\n'+c4(0x8002bc4-0x08000000)+
 'add sp,#0x10\npop {r4,r5,r6,r7}\npop {r0}\nbx r0\n')
give_fn=thumb_fn(give_src)
G=quests.Asm()
G.cmpvar(0x4002,0x1b); G.goto_if(1,'sand')
G.raw(*rom[0x169c8b:0x169c8b+15])           # original givemon (other starters)
G.ret()
G.lab('sand'); G.raw(0x23,*struct.pack('<I',ptr(give_fn)+1)); G.ret()
gc,_=G.assemble(0); gb=alloc(b'\xff'*len(gc),1); gc,_=G.assemble(gb); rom[gb:gb+len(gc)]=gc
assert rom[0x169c8b]==0x79
rom[0x169c8b:0x169c8b+15]=bytes([0x04])+struct.pack('<I',ptr(gb))+bytes(10)   # call gb; 10x nop

if os.environ.get('DEBUGSAND'):   # DEBUG ONLY: RENAME entry grants the Adamant Sandshrew via native routine
    assert rom[rename_script+1]==0x79
    rom[rename_script+1:rename_script+16]=bytes([0x23])+struct.pack('<I',ptr(give_fn)+1)+bytes(10)

# ---------------------------------------------------------------- SANDSTORM: new species (reuses the unused CELEBI slot 251), evolves from SANDSLASH at Lv35
SS=251; SL=28
def cp(table,stride,dst,src,n=None):
    n=n or stride; rom[table+stride*dst:table+stride*dst+n]=rom[table+stride*src:table+stride*src+n]
# base stats (duplicate Sandslash, then new stats: HP 110 / ATK 150 / DEF 150 / SPE 120 / SPA 45 / SPD 105)
cp(0x254784,28,SS,SL); rom[0x254784+28*SS:0x254784+28*SS+6]=bytes([110,150,150,120,45,105])
# name
nm=text('SANDSTORM'); rom[0x245ee0+11*SS:0x245ee0+11*SS+11]=nm+b'\xff'*(11-len(nm))
# sprites: Sandslash front/back art, SHINY palette as the normal palette (and normal palette as the shiny one)
for tb in (0x2350ac,0x23654c):
    cp(tb,8,SS,SL); rom[tb+8*SS+6:tb+8*SS+8]=struct.pack('<H',SS)
PAL=0x23730c; SHINY=0x2380cc
assert struct.unpack('<H',rom[SHINY+8*SL+4:SHINY+8*SL+6])[0]==SL+500
rom[PAL+8*SS:PAL+8*SS+4]=rom[SHINY+8*SL:SHINY+8*SL+4]; rom[PAL+8*SS+4:PAL+8*SS+6]=struct.pack('<H',SS)
rom[SHINY+8*SS:SHINY+8*SS+4]=rom[PAL+8*SL:PAL+8*SL+4]; rom[SHINY+8*SS+4:SHINY+8*SS+6]=struct.pack('<H',SS+500)
# party icon + its palette slot, battle elevation (Celebi hovers; Sandslash does not)
cp(0x3d37a0,4,SS,SL); rom[0x3d3e80+SS]=rom[0x3d3e80+SL]; rom[0x23a004+SS]=rom[0x23a004+SL]
# cries (normal + reverse tables are indexed by species-1)
for tb in (0x48c914,0x48db44): cp(tb,12,SS-1,SL-1)
# pokedex: counts as SANDSLASH's entry
rom[0x251fee+2*(SS-1):0x251fee+2*(SS-1)+2]=struct.pack('<H',SL)
# learnset: Sandslash's list + HYPER BEAM at 35
la=alloc(b''.join(struct.pack('<H',(l<<9)|m) for l,m in [(1,10),(1,28),(1,111),(22,91),(23,STONE_EDGE),(35,63),(41,89),(61,HIGH_HP)])+b'\xff\xff',2)
w32(LEARN+4*SS,ptr(la))
# evolution: SANDSLASH -> SANDSTORM at level 35 (EVO_LEVEL = 4)
assert rom[0x259754+40*SL:0x259754+40*SL+8]==bytes(8)
rom[0x259754+40*SL:0x259754+40*SL+8]=struct.pack('<HHHH',4,35,SS,0)
rom[0x259754+40*SS:0x259754+40*SS+40]=bytes(40)

# ---------------------------------------------------------------- TAUNTER: Ghost/Poison evolution of TAUROS (Lv25), species slot 252 (old unused "?" slot)
import gfx
TT=252; HT=93; TA=128
def _tp(o): return r32(o)-0x08000000
# 64x64 pixel-art sprite (tools/taunter.png, the Haunros art with red outline): alpha<128 = transparent, up to 15 exact colors
import colorsys
from PIL import Image as _Im
_s=_Im.open('/home/claude/work/tools/taunter.png').convert('RGBA'); assert _s.size==(64,64)
_uc=[]
for _y in range(64):
    for _x in range(64):
        _c=_s.getpixel((_x,_y))
        if _c[3]>=128 and _c[:3] not in _uc: _uc.append(_c[:3])
assert len(_uc)<=15
_idx=[[ (_uc.index(_s.getpixel((x,y))[:3])+1) if _s.getpixel((x,y))[3]>=128 else 0 for x in range(64)] for y in range(64)]
_fr=_bk=gfx.pixels_to_tiles(_idx)
_cols=[(255,0,255)]+_uc+[(0,0,0)]*(15-len(_uc))
def _shiny(c):
    h,l,sat=colorsys.rgb_to_hls(*[v/255 for v in c])
    if not (h<0.06 or h>0.94): h=(h-0.14)%1.0       # keep reds, shift purples toward blue
    return tuple(int(v*255) for v in colorsys.hls_to_rgb(h,l,sat))
_pn=gfx.rgb_to_pal(_cols); _ps=gfx.rgb_to_pal(_cols[:1]+[_shiny(c) for c in _cols[1:]])
for tb,data in ((0x2350ac,_fr),(0x23654c,_bk)):
    cp(tb,8,TT,HT); w32(tb+8*TT,ptr(alloc(gfx.lz_comp(data),4))); rom[tb+8*TT+6:tb+8*TT+8]=struct.pack('<H',TT)
# normal palette = the supplied sprite's colors; shiny palette = hue-shifted version
w32(PAL+8*TT,ptr(alloc(gfx.lz_comp(_pn),4))); rom[PAL+8*TT+4:PAL+8*TT+6]=struct.pack('<H',TT)
w32(SHINY+8*TT,ptr(alloc(gfx.lz_comp(_ps),4))); rom[SHINY+8*TT+4:SHINY+8*TT+6]=struct.pack('<H',TT+500)
cp(0x2349cc,4,TT,HT); cp(0x235e6c,4,TT,HT)           # sprite coordinates
cp(0x3d37a0,4,TT,HT); rom[0x3d3e80+TT]=rom[0x3d3e80+HT]; rom[0x23a004+TT]=rom[0x23a004+HT]   # icon, icon palette, elevation
for tb in (0x48c914,0x48db44): cp(tb,12,TT-1,TA-1)    # Tauros cry
# base stats: HP 100 / ATK 150 / DEF 100 / SPE 100 / SPA 150 / SPD 75; Ghost/Poison; Levitate; male only; slow growth
cp(0x254784,28,TT,HT); _b=0x254784+28*TT
rom[_b:_b+6]=bytes([100,150,100,100,150,75]); rom[_b+6]=7; rom[_b+7]=3
rom[_b+8]=45; rom[_b+9]=200; rom[_b+10:_b+12]=struct.pack('<H',0x0204); rom[_b+12:_b+16]=bytes(4)
rom[_b+16]=0; rom[_b+17]=20; rom[_b+18]=35; rom[_b+19]=5; rom[_b+20]=15; rom[_b+21]=15; rom[_b+22]=26; rom[_b+23]=0
nm=text('TAUNTER'); rom[0x245ee0+11*TT:0x245ee0+11*TT+11]=nm+b'\xff'*(11-len(nm))
# TM/HM compatibility = TAUROS | HAUNTER
for i in range(8): rom[0x252bc8+8*TT+i]=rom[0x252bc8+8*TA+i]|rom[0x252bc8+8*HT+i]
# learnset
w32(LEARN+4*TT,ptr(alloc(b''.join(struct.pack('<H',(l<<9)|m) for l,m in [(25,325),(28,344),(30,94),(33,188),(35,95),(37,138),(40,247),(43,194)])+b'\xff\xff',2)))
# evolution: TAUROS -> TAUNTER at level 25
assert rom[0x259754+40*TA:0x259754+40*TA+8]==bytes(8)
rom[0x259754+40*TA:0x259754+40*TA+8]=struct.pack('<HHHH',4,25,TT,0)
# pokedex: uses the unused national slot 251 (Celebi's page), reached via species 252
rom[0x251fee+2*(TT-1):0x251fee+2*(TT-1)+2]=struct.pack('<H',251)
_d=0x44e850+36*251; _h=0x44e850+36*HT
_cat=text('MOCKING BULL')[:-1]; assert len(_cat)==12
rom[_d:_d+12]=_cat; rom[_d+12:_d+16]=struct.pack('<HH',15,450)
w32(_d+16,ptr(alloc(text('A hateful, undead POKéMON made\nfrom the raging spirit of a\nTAUROS that refused to die.'),1))); w32(_d+20,ptr(alloc(text(''),1)))
rom[_d+24:_d+36]=rom[_h+24:_h+36]

# pokedex category: copy until the 0xFF terminator instead of stopping at the first space (so 'MOCKING BULL' shows in full)
assert rom[0x10583c:0x10583e]==bytes([0x00,0x28]) and rom[0x105856:0x105858]==bytes([0x00,0x28])
rom[0x10583c]=0xff; rom[0x105856]=0xff
assert rom[0x105806:0x105808]==bytes([0x85,0xb0]) and rom[0x1058b4:0x1058b6]==bytes([0x05,0xb0]) and rom[0x10585a:0x10585c]==bytes([0x0a,0x2c])
rom[0x105806]=0x86; rom[0x1058b4]=0x06; rom[0x10585a]=0x0b     # frame 0x18 and a 12-character cap

# ---------------------------------------------------------------- GRIMER -> MUK (Lv25) -> SLIMOSAUR (Lv35), species slot 253
# MUK: SLUDGE BOMB moves from Lv47 to Lv25, SHADOW PUNCH at Lv30. SLIMOSAUR: Poison/Grass, base 110 in every stat, MUK's moves up to Lv35,
# GIGA DRAIN at Lv35, then VENUSAUR's list from Lv36 on. Sprite = tools/slimosaur.png (64x64, 15 colors).
SS=253; MK=89; VN=3
def _ls(sp):
    a=r32(LEARN+4*sp)-0x08000000; r=[]
    while struct.unpack('<H',rom[a:a+2])[0]!=0xFFFF: v=struct.unpack('<H',rom[a:a+2])[0]; r.append((v>>9,v&0x1ff)); a+=2
    return r
def _pk(lst): return b''.join(struct.pack('<H',(l<<9)|m) for l,m in lst)+b'\xff\xff'
_muk=_ls(MK); assert (47,188) in _muk and not any(m in (325,) for l,m in _muk)
_muk=sorted([x for x in _muk if x!=(47,188)]+[(25,188),(30,325)],key=lambda x:x[0])
w32(LEARN+4*MK,ptr(alloc(_pk(_muk),2)))
_ven=_ls(VN)
w32(LEARN+4*SS,ptr(alloc(_pk([x for x in _muk if x[0]<=35]+[(35,202)]+[x for x in _ven if x[0]>35]),2)))
# evolutions: GRIMER Lv25 -> MUK; MUK Lv35 -> SLIMOSAUR
assert rom[0x259754+40*88:0x259754+40*88+8]==struct.pack('<HHHH',4,38,89,0)
rom[0x259754+40*88:0x259754+40*88+8]=struct.pack('<HHHH',4,25,89,0)
assert rom[0x259754+40*MK:0x259754+40*MK+8]==bytes(8)
rom[0x259754+40*MK:0x259754+40*MK+8]=struct.pack('<HHHH',4,35,SS,0)
# sprite
_s=_Im.open('/home/claude/work/tools/slimosaur.png').convert('RGBA'); assert _s.size==(64,64)
_uc=[]
for _y in range(64):
    for _x in range(64):
        _c=_s.getpixel((_x,_y))
        if _c[3]>=128 and _c[:3] not in _uc: _uc.append(_c[:3])
assert len(_uc)<=15
_idx=[[ (_uc.index(_s.getpixel((x,y))[:3])+1) if _s.getpixel((x,y))[3]>=128 else 0 for x in range(64)] for y in range(64)]
_fr=_bk=gfx.pixels_to_tiles(_idx)
_cols=[(255,0,255)]+_uc+[(0,0,0)]*(15-len(_uc))
def _shiny2(c):
    h,l,sat=colorsys.rgb_to_hls(*[v/255 for v in c])
    if sat>0.15: h=(h+0.35)%1.0
    return tuple(int(v*255) for v in colorsys.hls_to_rgb(h,l,sat))
_pn=gfx.rgb_to_pal(_cols); _ps=gfx.rgb_to_pal(_cols[:1]+[_shiny2(c) for c in _cols[1:]])
for tb,data in ((0x2350ac,_fr),(0x23654c,_bk)):
    cp(tb,8,SS,MK); w32(tb+8*SS,ptr(alloc(gfx.lz_comp(data),4))); rom[tb+8*SS+6:tb+8*SS+8]=struct.pack('<H',SS)
w32(PAL+8*SS,ptr(alloc(gfx.lz_comp(_pn),4))); rom[PAL+8*SS+4:PAL+8*SS+6]=struct.pack('<H',SS)
w32(SHINY+8*SS,ptr(alloc(gfx.lz_comp(_ps),4))); rom[SHINY+8*SS+4:SHINY+8*SS+6]=struct.pack('<H',SS+500)
cp(0x2349cc,4,SS,MK); cp(0x235e6c,4,SS,MK)
cp(0x3d37a0,4,SS,MK); rom[0x3d3e80+SS]=rom[0x3d3e80+MK]; rom[0x23a004+SS]=rom[0x23a004+MK]     # icon, icon palette, elevation
for tb in (0x48c914,0x48db44): cp(tb,12,SS-1,MK-1)                                              # MUK's cry
# base stats: VENUSAUR's row with 110 in every stat, Poison/Grass, Stench/Overgrow, 50% male, Amorphous/Grass egg groups
cp(0x254784,28,SS,VN); _b=0x254784+28*SS
rom[_b:_b+6]=bytes([110]*6); rom[_b+6]=3; rom[_b+7]=12
rom[_b+16]=127; rom[_b+20]=0x0b; rom[_b+21]=7; rom[_b+22]=1; rom[_b+23]=65
nm=text('SLIMOSAUR'); rom[0x245ee0+11*SS:0x245ee0+11*SS+11]=nm+b'\xff'*(11-len(nm))
for i in range(8): rom[0x252bc8+8*SS+i]=rom[0x252bc8+8*MK+i]|rom[0x252bc8+8*VN+i]
# pokedex: national slot 385 (JIRACHI's unused page), reached via species 253
rom[0x251fee+2*(SS-1):0x251fee+2*(SS-1)+2]=struct.pack('<H',385)
_d=0x44e850+36*385; _h=0x44e850+36*VN
_cat=text('POISON PLANT')[:-1]; assert len(_cat)==12
rom[_d:_d+12]=_cat; rom[_d+12:_d+16]=rom[_h+12:_h+16]
w32(_d+16,ptr(alloc(text('This POKéMON grows in polluted\nareas of nature.'),1))); w32(_d+20,ptr(alloc(text(''),1)))
rom[_d+24:_d+36]=rom[_h+24:_h+36]

# ---------------------------------------------------------------- TEXT SPEED: SLOW/MID/FAST + new FASTER (2 chars/frame) and FASTEST (4 chars/frame, default)
assert rom[0x54960:0x54962]==bytes([0x01,0x21]); rom[0x54960]=3          # new-game default: FASTER (was MID)
assert rom[0xf78b4:0xf78b6]==bytes([0x02,0x28]); rom[0xf78b4]=3          # accept settings up to 3 (was reset to MID if >2)
assert rom[0xf78be:0xf78c0]==bytes([0x01,0x21]); rom[0xf78be]=3          # invalid value falls back to FASTER
assert r32(0xf78dc)==0x0841f428
w32(0xf78dc,ptr(alloc(bytes([8,4,1,1]),4)))                             # per-character delay: SLOW 8, MID 4, FAST 1, FASTER 1
assert struct.unpack('<H',rom[0x3cc304:0x3cc306])[0]==3; rom[0x3cc304]=4  # options menu: TEXT SPEED has 4 choices
s_f2=alloc(text('FASTER'),1)
assert r32(0x88a34)==0x083cc330
w32(0x88a34,ptr(alloc(rom[0x3cc330:0x3cc33c]+struct.pack('<I',ptr(s_f2)),4)))

# INSTANT: the engine's own speed-0 path leaves field message boxes blank, so INSTANT keeps delay 1 and instead
# RunTextPrinters calls RenderFont up to 2x per frame (delay counter cleared each time) when the setting is 3.
TRAMP=0x3af270
assert rom[TRAMP:TRAMP+8]==b'\xff'*8
assert rom[0x2e00:0x2e04]==bytes.fromhex(''.join('%02x'%b for b in rom[0x2e00:0x2e04]))   # (placeholder, keeps byte view)
hook_src=('push {r4,r5,lr}\nadds r4,r0,#0\nldr r1,=0x0300500c\nldr r1,[r1]\nldrb r1,[r1,#0x14]\nlsls r1,r1,#29\nlsrs r1,r1,#29\n'
 'cmp r1,#3\nbne single\nmovs r5,#2\n'
 'loop:\nmovs r0,#0\nstrb r0,[r4,#0x1e]\nadds r0,r4,#0\nldr r1,=%d\nbl %d\ncmp r0,#0\nbne done\nsubs r5,#1\nbne loop\nb done\n'
 'single:\nadds r0,r4,#0\nldr r1,=%d\nbl %d\n'
 'done:\npop {r4,r5}\npop {r1}\nbx r1\n')%(0x08002e7d,0x08000000+THUNK,0x08002e7d,0x08000000+THUNK)
hook=thumb_fn(hook_src)
rom[TRAMP:TRAMP+4]=bytes([0x00,0x49,0x08,0x47]); w32(TRAMP+4,ptr(hook)+1)       # ldr r1,[pc,#0]; bx r1; .word hook
off=TRAMP-(0x2e00+4)
rom[0x2e00:0x2e04]=struct.pack('<HH',0xF000|((off>>12)&0x7FF),0xF800|((off>>1)&0x7FF))

# paragraph-scroll speed tables are indexed by text speed too: give INSTANT (3) a real entry (index 3 was 0 = scroll never finishes)
assert r32(0x5d04)==0x081ea650 and rom[0x1ea650:0x1ea653]==bytes([1,2,4])
w32(0x5d04,ptr(alloc(bytes([1,2,4,16,16]),4)))
assert r32(0x14fc30)==0x0846fb08 and rom[0x46fb08:0x46fb0b]==bytes([1,2,4])
w32(0x14fc30,ptr(alloc(bytes([1,2,4,16,16]),4)))

assert rom[0x254784+28*150+8]==3; rom[0x254784+28*150+8]=255   # MEWTWO catch rate 255
assert struct.unpack('<8H',rom[0x25e014:0x25e024])==(15,19,57,70,148,249,127,291); rom[0x25e014:0x25e016]=b'\xff\xff'   # HM list emptied: HM moves can be forgotten
assert bytes(rom[0x125a90:0x125a92])==bytes.fromhex('00b5'); rom[0x125a90:0x125a94]=bytes.fromhex('00207047')   # Move Deleter HM check: always 'not an HM'
# ---------------------------------------------------------------- STAGE 1: GLOCK (item 52) and 9MM ROUND (item 53) in the unused item slots, sold in PokeMarts
ITEM_BASE=0x3db028
ITEM_GLOCK,ITEM_9MM=52,53
def mkitem(i,name,price,desc,importance):
    o=ITEM_BASE+44*i
    assert rom[o:o+9]==bytes([0xac])*8+b'\xff' and struct.unpack('<H',rom[o+14:o+16])[0]==0, 'item slot %d not free'%i
    rom[o:o+14]=text(name).ljust(14,b'\x00')
    rom[o+14:o+16]=struct.pack('<H',i); rom[o+16:o+18]=struct.pack('<H',price)
    w32(o+20,ptr(alloc(text(desc),1))); rom[o+24]=importance
mkitem(ITEM_GLOCK,'GLOCK',1000,'A handgun. Lets you rob\ndefeated TRAINERS.',1)
mkitem(ITEM_9MM,'9MM ROUND',50,'Ammo for a GLOCK.\nShooting uses one.',0)
# ---------------------------------------------------------------- MUTAGENS (items 54/55): +10 IVs (cap 31). Reuse the MEDICINE party-menu flow (bag -> party menu -> message -> item consumed)
ITEM_PHYS,ITEM_SPEC=54,55
mkitem(ITEM_PHYS,'PHYS MUTAGEN',5000,"Raises ATTACK and DEFENSE\nIVs by 10. (Max 31)",0)
mkitem(ITEM_SPEC,'SPEC MUTAGEN',5000,"Raises SP. ATK and SP. DEF\nIVs by 10. (Max 31)",0)
for _i in (ITEM_PHYS,ITEM_SPEC):
    _o=ITEM_BASE+44*_i
    rom[_o+26]=1; rom[_o+27]=1; w32(_o+28,0x080a16e1); w32(_o+32,0); w32(_o+36,0)     # Items pocket, party-menu use (same as vitamins), not usable in battle
    w32(0x2528bc+4*(_i-13),ptr(alloc(bytes(8),4)))                                       # empty item-effect record (slot was a null pointer)
# prices: PROTEIN / CALCIUM 7,500; RARE CANDY 9,900 (the mart price column only has room for 4 digits)
for _i,_pr in ((64,7500),(67,7500),(68,9900)):
    rom[ITEM_BASE+44*_i+16:ITEM_BASE+44*_i+18]=struct.pack('<H',_pr)
# icons: PROTEIN's bottle image with its own palette tinted green (PHYS) / purple (SPEC)
import colorsys as _cs
def _tint(pal_ptr,hue):
    c=gfx.pal_to_rgb(gfx.lz_decomp(rom,pal_ptr-0x08000000)); o=[c[0]]
    for r,g,b in c[1:]:
        h,l,sa=_cs.rgb_to_hls(r/255,g/255,b/255)
        if sa>0.15: h=hue
        o.append(tuple(int(v*255) for v in _cs.hls_to_rgb(h,l,sa)))
    return ptr(alloc(gfx.lz_comp(gfx.rgb_to_pal(o)),4))
ICONT=0x3d4294
for _i,_hue in ((ITEM_PHYS,0.33),(ITEM_SPEC,0.78)):
    w32(ICONT+8*_i,r32(ICONT+8*64)); w32(ICONT+8*_i+4,_tint(r32(ICONT+8*64+4),_hue))
IV_P=alloc(bytes([40,41]),2); IV_S=alloc(bytes([43,44]),2)        # MON_DATA_ATK_IV, DEF_IV / SPATK_IV, SPDEF_IV
MSG_P=alloc(b'\xfd\x02'+text("'s ATTACK and DEFENSE\nIVs rose!"),1); MSG_S=alloc(b'\xfd\x02'+text("'s SP. ATK and SP. DEF\nIVs rose!"),1)
# W1 replaces the 'would it have an effect' check, W2 applies the item, W3 builds the message
w1=thumb_fn('push {r4,r5,r6,lr}\nlsls r4,r1,#16\nlsrs r4,r4,#16\ncmp r4,#54\nbeq p\ncmp r4,#55\nbeq s\n'
 'ldr r4,=%d\nbl %d\npop {r4,r5,r6,pc}\n'%(0x08042415,0x08000000+THUNK_R4)+
 'p:\nldr r6,=%d\nb chk\ns:\nldr r6,=%d\n'%(ptr(IV_P),ptr(IV_S))+
 'chk:\nadds r5,r0,#0\nldrb r1,[r6]\nadds r0,r5,#0\nmovs r2,#0\n'+c4(0x803fbe8-0x08000000)+'cmp r0,#31\nblt eff\n'
 'ldrb r1,[r6,#1]\nadds r0,r5,#0\nmovs r2,#0\n'+c4(0x803fbe8-0x08000000)+'cmp r0,#31\nblt eff\nmovs r0,#1\npop {r4,r5,r6,pc}\neff:\nmovs r0,#0\npop {r4,r5,r6,pc}\n')
w2=thumb_fn('push {r4,r5,r6,r7,lr}\nsub sp,#8\nlsls r3,r1,#16\nlsrs r3,r3,#16\ncmp r3,#54\nbeq p\ncmp r3,#55\nbeq s\n'
 'ldr r4,=%d\nbl %d\nadd sp,#8\npop {r4,r5,r6,r7,pc}\n'%(0x08125269,0x08000000+THUNK_R4)+
 'p:\nldr r6,=%d\nb go\ns:\nldr r6,=%d\n'%(ptr(IV_P),ptr(IV_S))+
 'go:\nmovs r1,#100\nmuls r0,r1\nldr r1,=0x02024284\nadds r5,r0,r1\nmovs r7,#2\n'
 'loop:\nldrb r1,[r6]\nadds r0,r5,#0\nmovs r2,#0\n'+c4(0x803fbe8-0x08000000)+'adds r0,#10\ncmp r0,#31\nble ok\nmovs r0,#31\nok:\nstr r0,[sp]\n'
 'ldrb r1,[r6]\nadds r0,r5,#0\nmov r2,sp\n'+c4(0x804037c-0x08000000)+'adds r6,#1\nsubs r7,#1\nbne loop\n'
 'adds r0,r5,#0\n'+c4(0x803e47c-0x08000000)+'movs r0,#0\nadd sp,#8\npop {r4,r5,r6,r7,pc}\n')
w3=thumb_fn('push {r4,lr}\nlsls r1,r0,#16\nlsrs r1,r1,#16\ncmp r1,#54\nbeq p\ncmp r1,#55\nbeq s\n'
 'ldr r4,=%d\nbl %d\npop {r4,pc}\n'%(0x08125059,0x08000000+THUNK_R4)+
 'p:\nldr r1,=%d\nb out\ns:\nldr r1,=%d\n'%(ptr(MSG_P),ptr(MSG_S))+
 'out:\nldr r0,=0x02021d18\n'+c4(0x8008fcc-0x08000000)+'pop {r4,pc}\n')
def _tramp_ip(at,fn):
    assert rom[at:at+16]==b'\xff'*16
    rom[at:at+12]=bytes([0x01,0xb4,0x02,0x48,0x84,0x46,0x01,0xbc,0x60,0x47,0x00,0xbf]); w32(at+12,ptr(fn)+1)    # push r0; ldr r0,lit; mov ip,r0; pop r0; bx ip
def _bl(at,dst):
    off=dst-(at+4); rom[at:at+4]=struct.pack('<HH',0xF000|((off>>12)&0x7FF),0xF800|((off>>1)&0x7FF))
for _at,_t,_f in ((0x12533a,0x3af380,w1),(0x12541e,0x3af390,w2),(0x125516,0x3af3a0,w3)):
    _tramp_ip(_t,_f); _bl(_at,_t)
assert bytes(rom[0x12533a:0x12533e])!=b'\xff'*4
MART_SITES=[]
MARTS=[0x1649b8,0x16a298,0x16a708,0x16acd8,0x16b390,0x16b68c,0x16bb38,0x16d518,0x16ea48,0x16eaf4,0x16efdc,0x170b58,0x1718b4,0x171cd4,0x171e8c]
for a in MARTS:
    ids=[]; k=a
    while struct.unpack('<H',rom[k:k+2])[0]: ids.append(struct.unpack('<H',rom[k:k+2])[0]); k+=2
    assert ids[0] in (2,3,4) and len(ids)<12
    new=alloc(struct.pack('<%dH'%(len(ids)+8),*(ids+[ITEM_GLOCK,ITEM_9MM,ITEM_PHYS,ITEM_SPEC,64,67,68,0])),4)
    n=0
    for q in range(0,0x1c0000):                 # every pokemart command that points at this list
        if rom[q]==0x86 and r32(q+1)==ptr(a): w32(q+1,ptr(new)); n+=1; MART_SITES.append((q,new))
    assert n>=1,hex(a)

if os.environ.get('DEBUGMART'): rom[rename_script:rename_script+6]=bytes([0x86])+struct.pack('<I',ptr(new))+bytes([0x02])   # DEBUG ONLY: RENAME opens the last mart
# ---------------------------------------------------------------- STAGE 2a: gunshot sound effect (new song id 347 = SE_SHOT)
SONGT=0x4a32cc
assert r32(0x1dd11c)==0x084a32cc
nsong=1   # entry 0 is a dummy
while True:
    sp,ms,me=struct.unpack('<IHH',rom[SONGT+8*nsong:SONGT+8*nsong+8])
    t=sp-0x08000000
    if not(0x08000000<=sp<0x08800000 and rom[t]>=1 and rom[t]<=16 and rom[t+1]==0 and ms<8 and me<8): break
    nsong+=1
assert nsong==347, nsong
SE_SHOT=nsong
pcm=open('/home/claude/work/stage2/shot.raw','rb').read()
wave=alloc(struct.pack('<HHIII',0,0,13379*1024,0,len(pcm))+pcm,4)
vg=alloc(bytes([0x00,60,0,0])+struct.pack('<I',ptr(wave))+bytes([0xff,0x00,0xff,0x00]),4)
trk=alloc(bytes([0xbc,0x00,0xbb,0x3c,0xbd,0x00,0xbe,0x7f,0xff,60,0x7f,0xb1]),4)
song=alloc(bytes([1,0,5,0])+struct.pack('<II',ptr(vg),ptr(trk)),4)
newt=alloc(rom[SONGT:SONGT+8*nsong]+struct.pack('<IHH',ptr(song),1,1),4)
for a in (0x1dd11c,0x1dd150,0x1dd19c,0x1dd1f0,0x1dd224):
    assert r32(a)==0x084a32cc; w32(a,ptr(newt))

# ---------------------------------------------------------------- STAGE 2b: new overworld sprite (blood splatter) = object graphics id 0x98
from PIL import Image
GFX_SPLAT=0x98
def splat_assets():
    im=Image.open('/home/claude/work/stage2/splat.png').convert('RGBA')
    w,h=im.size; sc=min(16/w,16/h); nw,nh=max(1,round(w*sc)),max(1,round(h*sc))
    r=im.resize((nw,nh),Image.LANCZOS)
    c=Image.new('RGBA',(16,16),(0,0,0,0)); c.paste(r,((16-nw)//2,16-nh),r)
    px=c.load(); rgb=Image.new('RGB',(16,16))
    for y in range(16):
        for x in range(16): rgb.putpixel((x,y),px[x,y][:3])
    q=rgb.quantize(colors=15,method=Image.MEDIANCUT); pal=q.getpalette()[:45]
    idx=[[0]*16 for _ in range(16)]
    for y in range(16):
        for x in range(16):
            if px[x,y][3]>=128: idx[y][x]=q.getpixel((x,y))+1
    pw=bytearray(32)
    for i in range(15):
        r5,g5,b5=[pal[3*i+k]>>3 for k in range(3)]
        struct.pack_into('<H',pw,2+2*i,r5|(g5<<5)|(b5<<10))
    tiles=bytearray()
    for ty in range(2):
        for tx in range(2):
            for y in range(8):
                for x in range(0,8,2):
                    tiles.append(idx[ty*8+y][tx*8+x]|(idx[ty*8+y][tx*8+x+1]<<4))
    return bytes(tiles),bytes(pw)
tiles,palbytes=splat_assets()
tile_a=alloc(tiles,4); pal_a=alloc(palbytes,4)
img_a=alloc(struct.pack('<IHH',ptr(tile_a),0x80,0),4)
# palette table gets one more entry (tag 0x1120)
PT=0x3a5158; npal=18
newpt=alloc(rom[PT:PT+8*npal]+struct.pack('<IHH',ptr(pal_a),0x1120,0)+struct.pack('<IHH',0,0x11ff,0),4)   # table is terminated by tag 0x11FF
for a in (0x5f4d8,0x5f570,0x5f5c8):
    assert r32(a)==0x08000000+PT; w32(a,ptr(newpt))
# graphics info: copy the item ball's (16x16, inanimate), swap in our palette tag and frame image
GT=0x39fdb0
ib=r32(GT+4*92)-0x08000000
info=bytearray(rom[ib:ib+36]); info[2:4]=struct.pack('<H',0x1120); info[0x1c:0x20]=struct.pack('<I',ptr(img_a)); info[12]=(info[12]&0xF0)|10
info_a=alloc(bytes(info),4)
newgt=alloc(rom[GT:GT+4*GFX_SPLAT]+struct.pack('<I',ptr(info_a)),4)
assert r32(0x5f2f4)==0x08000000+GT; w32(0x5f2f4,ptr(newgt))
assert rom[0x5f2e0:0x5f2e2]==bytes([0x97,0x29]); rom[0x5f2e0]=GFX_SPLAT      # id clamp: allow 0x98

if os.environ.get('DEBUGGFX'):    # DEBUG ONLY: "group,num,localId,gfx" changes one NPC's graphics in its ROM template
    import scr
    g,n,lid,gx=[int(v) for v in os.environ['DEBUGGFX'].split(',')]
    h=[x for x in scr.maps if x[0]==g and x[1]==n][0][3]; ev=scr.rp(h+4); po=scr.rp(ev+4)
    for i in range(scr.d[ev]):
        if scr.d[po+i*0x18]==lid: rom[po+i*0x18+1]=gx

# ---------------------------------------------------------------- STAGE 2c: GLOCK robbery / shooting (C routines + scripts)
import subprocess
sys.path.insert(0,'/home/claude/work/stage2')
import prep
S2='/home/claude/work/stage2'
IDS,SHOOT=prep.load()
VARS_POOL=list(range(0x4090,0x40A0))+list(range(0x40A1,0x40AA))+list(range(0x40BD,0x40CF))+list(range(0x40D0,0x40E6))
VARS_POOL=VARS_POOL[:64]; assert len(VARS_POOL)==64 and len(IDS)<=512
def u16b(v): return struct.pack('<H',v)
# harmless script for the splatter object: say something grim
s_splat=alloc(text('A bloody mess.\nBest not to look.'),1)
SPL=quests.Asm(); SPL.ptrc([0x0f,0],s_splat); SPL.raw(0x09,6); SPL.end()
spc,_=SPL.assemble(0); splat_script=alloc(spc,1); spc,_=SPL.assemble(splat_script); rom[splat_script:splat_script+len(spc)]=spc
hdr=('#define NIDS %d\n#define SPLAT_SCRIPT 0x%08x\n#define GFX_SPLAT %d\nstatic const unsigned short g_ids[]={%s};\nstatic const unsigned char g_shoot[]={%s};\nstatic const unsigned short g_vars[]={%s};\n'
     %(len(IDS),ptr(splat_script),GFX_SPLAT,','.join(map(str,IDS)),','.join(map(str,SHOOT)),','.join(map(str,VARS_POOL))))
open(S2+'/data.h','w').write(hdr+('#define PROBE 1\n' if os.environ.get('DEBUGPROBE') else ''))
cur[0]=(cur[0]+3)&~3; CA=cur[0]
open(S2+'/rob.ld','w').write('ENTRY(wrap_load)\nSECTIONS { . = 0x%08x; .all : { *(.text*) *(.rodata*) *(.data*) } /DISCARD/ : { *(.ARM.exidx*) *(.comment) *(.note*) *(.ARM.attributes) } }\n'%ptr(CA))
subprocess.run(['clang','--target=thumbv4t-none-eabi','-mthumb','-Os','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-nostdlib','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-c',S2+'/rob.c','-o',S2+'/rob.o'],check=True)
subprocess.run(['ld.lld','-T',S2+'/rob.ld',S2+'/rob.o','-o',S2+'/rob.elf'],check=True)
subprocess.run(['llvm-objcopy','-O','binary',S2+'/rob.elf',S2+'/rob.bin'],check=True)
blob=open(S2+'/rob.bin','rb').read(); assert alloc(blob,4)==CA
SYM={}
for ln in subprocess.run(['nm',S2+'/rob.elf'],capture_output=True,text=True,check=True).stdout.split('\n'):
    f=ln.split()
    if len(f)==3: SYM[f[2]]=int(f[0],16)&~1
def sa(n): return SYM[n]-0x08000000          # file offset of a routine
# hook the two map-object-template loaders (3 + 2 call sites) through trampolines in free space
def tramp(at,target):
    assert rom[at:at+8]==b'\xff'*8
    rom[at:at+4]=bytes([0x00,0x49,0x08,0x47]); w32(at+4,0x08000000+target+1)
def patch_bl(at,dst):
    off=dst-(at+4)
    rom[at:at+4]=struct.pack('<HH',0xF000|((off>>12)&0x7FF),0xF800|((off>>1)&0x7FF))
tramp(0x3af280,sa('wrap_load')); tramp(0x3af290,sa('wrap_scripts'))
def bl_dst(at):
    h1,h2=struct.unpack('<HH',rom[at:at+4]); off=((h1&0x7FF)<<12)|((h2&0x7FF)<<1)
    if off&0x400000: off-=0x800000
    return at+4+off
for a in (0x5588c,0x55926,0x559ae): assert bl_dst(a)==0x54f68; patch_bl(a,0x3af280)
for a in (0x5694a,0x57448): assert bl_dst(a)==0x550a8; patch_bl(a,0x3af290)
# ROUTE 11 old man JASPER (trainer 259): the original ROM's script for him lost its first bytes (it starts mid-instruction, so being
# spotted by him reads garbage as a trainer id and crashes). Rebuild: trainerbattle + the intact tail, and repoint his object.
import scr as _scr
_jh=[x for x in _scr.maps if x[0]==3 and x[1]==29][0][3]; _jev=_scr.rp(_jh+4); _jpo=_scr.rp(_jev+4)
_jscr=alloc(bytes([0x5c,0,3,1,0,0])+struct.pack('<II',0x08184f5d,0x08184f7e)+bytes.fromhex('260d803900210d8001000601e69c1a080f008e4f18080906')+bytes([0x02]),1)
_n=0
for _k in range(_scr.d[_jev]):
    if r32(_jpo+_k*0x18+0x10)==0x081a9cbf: w32(_jpo+_k*0x18+0x10,ptr(_jscr)); _n+=1
assert _n==1
assert bytes(_scr.d[0x184f5d:0x184f61])==text('Comp')[:4] and bytes(_scr.d[0x1a9ce6:0x1a9ce8])==bytes([0x5c,0x05])
# the rob/shoot script, entered from the defeated-trainer talk script
def tx(t): return alloc(text(t),1)
def tx1(a,b): return alloc(text(a)[:-1]+b'\xfd\x02'+text(b),1)
s_askrob=tx('Point your GLOCK at this\nTRAINER and rob them?')
s_dont=tx("Don't shoot! Here, take\neverything I have!")
s_took=tx1('You took $','!')
s_nothing=tx("They've got nothing left\nto give.")
s_askshoot=tx('Shoot them anyway?\nThis uses one 9MM ROUND.')
s_gotmons=tx('You took their POK\u00e9MON!')
def cn(n): return sa(n)+1
H=quests.Asm(); pk=lambda v: u16b(v)
H.lab('start')
H.raw(0x47,*pk(ITEM_GLOCK),*pk(1)); H.cmpvar(0x800d,0); H.goto_if(1,'normal')
H.ptrc([0x23],cn('rob_info'))
H.cmpvar(0x8006,0); H.goto_if(1,'normal')
H.cmpvar(0x8004,1); H.goto_if(1,'already')
H.yesno(s_askrob); H.cmpvar(0x800d,0); H.goto_if(1,'normal')
H.ptrc([0x23],cn('rob_pay'))
H.msg(s_dont); H.msg(s_took); H.goto('shootask')
H.lab('already'); H.msg(s_nothing)
H.lab('shootask')
H.cmpvar(0x8005,0); H.goto_if(1,'done')
H.raw(0x47,*pk(ITEM_9MM),*pk(1)); H.cmpvar(0x800d,0); H.goto_if(1,'done')
H.yesno(s_askshoot); H.cmpvar(0x800d,0); H.goto_if(1,'done')
H.raw(0x45,*pk(ITEM_9MM),*pk(1))
H.raw(0x2f,*pk(SE_SHOT)); H.raw(0x30)
H.raw(0x53,*pk(0x800f))
H.ptrc([0x23],cn('shoot_do'))
H.raw(0x55,*pk(0x800f))
H.cmpvar(0x8007,0); H.goto_if(1,'noprt'); H.raw(0x53,*pk(0x8007)); H.raw(0x55,*pk(0x8007))
H.lab('noprt')
H.msg(s_gotmons)
H.lab('done'); H.raw(0x6c); H.end()
H.lab('normal'); H.raw(0x5e)
hc,_=H.assemble(0); hb=alloc(b'\xff'*len(hc),1); hc,_=H.assemble(hb); rom[hb:hb+len(hc)]=hc
assert rom[0x1a4ed7:0x1a4edd]==bytes([0x06,0x05,0xe8,0x4e,0x1a,0x08])
rom[0x1a4ed7:0x1a4edd]=bytes([0x06,0x05])+struct.pack('<I',ptr(hb))

# ---------------------------------------------------------------- STAGE 3: SELL POKEMON (third PokeMart menu entry, PC box browser)
S3='/home/claude/work/stage3'
NSP3=412
DECN={v:k for k,v in ENC.items()}
def spname(i):
    o=''
    for x in rom[0x245ee0+11*i:0x245ee0+11*i+11]:
        if x==0xff: break
        o+=DECN.get(x,'?')
    return o
EVO=0x259754
stage=[1]*NSP3
for _ in range(12):
    chg=False
    for sp in range(1,NSP3):
        for k in range(5):
            m,pm,tg,_pad=struct.unpack('<HHHH',rom[EVO+40*sp+8*k:EVO+40*sp+8*k+8])
            if m and 0<tg<NSP3 and stage[tg]<stage[sp]+1 and stage[sp]<6: stage[tg]=stage[sp]+1; chg=True
    if not chg: break
LEG=['ARTICUNO','ZAPDOS','MOLTRES','MEWTWO','MEW','RAIKOU','ENTEI','SUICUNE','LUGIA','HO-OH','REGIROCK','REGICE','REGISTEEL','LATIAS','LATIOS','KYOGRE','GROUDON','RAYQUAZA','JIRACHI','DEOXYS']
mult=[1]*NSP3
for sp in range(1,NSP3): mult[sp]=1 if stage[sp]<=1 else (2 if stage[sp]==2 else 3)
found=set()
for sp in range(1,NSP3):
    if spname(sp) in LEG: mult[sp]=4; found.add(spname(sp))
assert found==set(LEG), set(LEG)-found
if os.environ.get('DEBUGMULT'): print({spname(i):(stage[i],mult[i]) for i in (1,2,3,4,5,6,25,26,133,134,150,243,249,251,129,130)})
for c,v in (('A',0xbb),('a',0xd5),('0',0xa1),('$',0xb7),('.',0xad),('-',0xae),('/',0xba),('!',0xab),('?',0xac),(',',0xb8)): assert ENC[c]==v,c
open(S3+'/sdata.h','w').write('#define NSP %d\nstatic const unsigned char g_mult[]={%s};\n'%(NSP3,','.join(map(str,mult))))
cur[0]=(cur[0]+3)&~3; CA3=cur[0]
open(S3+'/sell.ld','w').write('ENTRY(ps_choose)\nSECTIONS { . = 0x%08x; .all : { *(.text*) *(.rodata*) *(.data*) } /DISCARD/ : { *(.ARM.exidx*) *(.comment) *(.note*) *(.ARM.attributes) } }\n'%ptr(CA3))
cc=['clang','--target=thumbv4t-none-eabi','-mthumb','-Os','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-nostdlib','-fno-unwind-tables','-fno-asynchronous-unwind-tables']
if os.environ.get('DEBUGFILL'): cc.append('-DDEBUGFILL')
subprocess.run(cc+['-c',S3+'/sell.c','-o',S3+'/sell.o'],check=True)
subprocess.run(['ld.lld','-T',S3+'/sell.ld',S3+'/sell.o','-o',S3+'/sell.elf'],check=True)
subprocess.run(['llvm-objcopy','-O','binary',S3+'/sell.elf',S3+'/sell.bin'],check=True)
assert alloc(open(S3+'/sell.bin','rb').read(),4)==CA3
SYM3={}
for ln in subprocess.run(['nm',S3+'/sell.elf'],capture_output=True,text=True,check=True).stdout.split('\n'):
    f=ln.split()
    if len(f)==3: SYM3[f[2]]=int(f[0],16)|1        # thumb function pointers
# the mart menu: BUY / SELL / SELL POKEMON / QUIT
assert r32(0x3df09c)==0x08416738 and r32(0x3df0a4)==0x0841673c and r32(0x3df0ac)==0x08416741
s_sellmon=alloc(text('SELL POK\u00e9MON'),1)
newtab=alloc(struct.pack('<8I',0x08416738,r32(0x3df0a0),0x0841673c,r32(0x3df0a8),ptr(s_sellmon),SYM3['ps_choose'],0x08416741,r32(0x3df0b0)),4)
nref=0
for q in range(0,0x3d0000,4):
    if r32(q)==0x083df09c: w32(q,ptr(newtab)); nref+=1
assert nref==2,nref
assert rom[0x9ab22:0x9ab24]==bytes([3,0x25]); rom[0x9ab22]=4          # movs r5,#3 -> #4 (list size and cursor range)
assert rom[0x3df0bc:0x3df0c4]==bytes([0,2,1,12,6,15,8,0]) and r32(0x9ab70)==0x083df0bc
w32(0x9ab70,ptr(alloc(bytes([0,2,1,12,8,15,8,0]),4)))                # window 4 rows tall instead of 3
# the shared sell script opens the game's own PC menu; while special var 0x8008 is set, RELEASE reads SELL and pays out
RES=0x800d
SH=quests.Asm()
SH.lab('sell')
if os.environ.get('DEBUGFILL'): SH.ptrc([0x23],SYM3['ps_debugfill']-0x08000000)
if not os.environ.get('DEBUGPC'): SH.setvar(0x8008,0x5E11)    # DEBUGPC (debug only): open the PC without sell mode
SH.raw(0x25,0x3c,0x00)        # special 0x3c: opens the POKeMON storage PC (same call the PC script makes)
SH.raw(0x27)                  # waitstate until the PC is closed
SH.setvar(0x8008,0)
SH.ret()
shc,_=SH.assemble(0); shb=alloc(b'\xff'*len(shc),1); shc,_=SH.assemble(shb); rom[shb:shb+len(shc)]=shc
# hooks into the PC storage code (trampolines near the original code keep the BL range; they only clobber r2)
def tramp2(at,target):
    assert rom[at:at+8]==b'\xff'*8
    rom[at:at+4]=bytes([0x00,0x4a,0x10,0x47]); w32(at+4,target)       # ldr r2,[pc,#0]; bx r2
def bl_to(at,dst):
    off=dst-(at+4)
    rom[at:at+4]=struct.pack('<HH',0xF000|((off>>12)&0x7FF),0xF800|((off>>1)&0x7FF))
s_sellword=alloc(text('SELL'),1)
h1=thumb_fn('lsls r0,r3,#2\nldr r2,=%d\nadds r0,r0,r2\nldr r0,[r0]\ncmp r3,#7\nbne done\npush {r3}\nldr r2,=%d\nldrh r2,[r2]\nldr r3,=%d\ncmp r2,r3\npop {r3}\nbne done\nldr r0,=%d\ndone:\nstr r0,[r1]\nbx lr\n'%(0x083d353c,0x020370c8,0x5E11,ptr(s_sellword)))
h2=thumb_fn('push {r0,r3,lr}\nldr r2,=%d\nadds r1,r1,r2\nldr r1,[r1]\nadds r0,r6,#0\nldr r2,=%d\nbl %d\nadds r1,r0,#0\npop {r0,r3,pc}\n'%(0x083cea88,SYM3['ps_text'],0x08000000+THUNK2))
tramp2(0x3af2a0,ptr(h1)+1); tramp2(0x3af2b0,ptr(h2)+1)
assert rom[0x94e0e:0x94e16]==bytes([0x98,0x00,0x80,0x18,0x00,0x68,0x08,0x60]),rom[0x94e0e:0x94e16].hex()
bl_to(0x94e0e,0x3af2a0); rom[0x94e12:0x94e16]=bytes([0xc0,0x46,0xc0,0x46])
assert rom[0x8fc8a:0x8fc8e]==bytes([0x89,0x18,0x09,0x68]),rom[0x8fc8a:0x8fc8e].hex()
bl_to(0x8fc8a,0x3af2b0)
stubs={}
for q,lst in MART_SITES:
    if lst not in stubs:
        T=quests.Asm()
        T.lab('stub'); T.setvar(RES,0); T.ptrc([0x86],lst); T.cmpvar(RES,0x5E11); T.goto_if(1,'dosell'); T.ret()
        T.lab('dosell')
        T.ptrc([0x04],shb); T.goto('stub')
        tc,_=T.assemble(0); tb=alloc(b'\xff'*len(tc),1); tc,_=T.assemble(tb); rom[tb:tb+len(tc)]=tc; stubs[lst]=tb
    assert rom[q]==0x86
    rom[q]=0x04; w32(q+1,ptr(stubs[lst]))

out=sys.argv[1] if len(sys.argv)>1 else '/home/claude/work/outlaw_quest.gba'
open(out,'wb').write(rom)
print('built; used %x..%x (%d bytes)'%(BASE,cur[0],cur[0]-BASE))

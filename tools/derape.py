# usage: derape.py in.gba out.gba
# Removes the rape references from the dialogue and rewords the sentence around another violent crime where it needs one.
import sys,struct
sys.path.insert(0,'/home/claude/work/tools')
from inc import *
from g3 import ENC
def enc(s):
    o=bytearray(); i=0
    while i<len(s):
        if s[i]=='\\':
            o.append({'n':0xfe,'l':0xfa,'p':0xfb}[s[i+1]]); i+=2
        else: o.append(ENC[s[i]]); i+=1
    return bytes(o)
PAIRS=[
 ("statuatory rape laws.","restraining order."),
 ("We are NOT rapists.","We are NOT murderers."),
 ("I don't want to get raped!","I don't want to get mugged!"),
 ("robbed\\nand gangraped.","robbed\\nand beaten up."),
 ("I'm never getting raped again!","I'm never getting mugged again!"),
 ("Rapists, Murderers,","Muggers, Murderers,"),
 ("He's a rapist\\npig!","He's a crooked\\npig!"),
 ("house and raped me.","house and stabbed me."),
 ("steal and rape and","steal and set fires and"),
 ("even for raping hot girls!","even for robbing banks!"),
 ("They raped my daughter","They beat up my daughter"),
 ("won't\\lrape or kill.","won't\\lburn or kill."),
 ("She then got raped.","She then got shot."),
 ("The raping and murdering","The torturing and murdering"),
 ("assault and \\lRAPE POKEMON!","assault and \\lMURDER POKEMON!"),
 ("THUGS gangrape\\nweak people","THUGS mug\\nweak people"),
 ("try to sexually\\nassault me.","try to rob\\nme."),
 ("murderous, rapist THUGS","murderous, thieving THUGS"),
 ("Someone's getting raped!","Someone's getting stabbed!"),
 ("killers and rapists.","killers and kidnappers."),
 ("been a rapist or","been a kidnapper or"),
 ("dirty rapist!","dirty thief!"),
 ("SAY NO to RAPE!","SAY NO to MURDER!"),
 ("You are supporting the RAPE of","You support the MURDER of"),
]
def span(b,i):
    s=i
    while s>0 and b[s-1]!=0xff: s-=1
    e=b.index(0xff,i)+1
    return s,e
if __name__=='__main__':
    r=Rom(sys.argv[1]); b=r.b
    for old,new in PAIRS:
        po,pn=enc(old),enc(new)
        hits=[]; i=-1
        while True:
            i=bytes(b).find(po,i+1)
            if i<0 or i>=0xa00000: break
            hits.append(i)
        assert len(hits)==1,(old,hits)
        p=hits[0]; s,e=span(b,p)
        ns=bytes(b[s:p])+pn+bytes(b[p+len(po):e])
        if len(ns)<=e-s:
            b[s:e]=ns+b'\xff'*(e-s-len(ns)); print('in place',hex(s),old)
        else:
            pat=struct.pack('<I',0x08000000+s)
            refs=[j for j in range(len(b)-3) if b[j:j+4]==pat]
            assert refs,(old,hex(s))
            na=r.alloc(ns,1)
            for j in refs: b[j:j+4]=struct.pack('<I',0x08000000+na)
            b[s:e]=b'\xff'*(e-s)                                   # the old text is deleted, not left behind
            print('moved',hex(s),'->',hex(na),len(refs),'refs',old)
    r.save(sys.argv[2])

import sys
ROM='/root/.claude/uploads/6e40a750-3062-5a1e-998e-15cd4f95db16/f4046af2-outlaw-2015-09-05.gba'
def load(): return open(ROM,'rb').read()
CH={}
for i,c in enumerate(' ÀÁÂÇÈÉÊËÌ ÎÏÒÓÔŒÙÚÛÑßàá çèéêëì îïòóôœùúûñºª'): CH[i]=c
for i,c in enumerate('0123456789!?.-・…“”‘’♂♀$,×/ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'): CH[0xA1+i]=c
CH[0x1B]='é'; CH[0xAD]='.';CH[0xB4]="'"
CH[0xFE]='\n';CH[0xFA]='\n';CH[0xFB]='\n'
ENC={}
for k,v in CH.items():
    if v not in ENC: ENC[v]=k
ENC['é']=0x1B; ENC["'"]=0xB4; ENC['.']=0xAD
ENC[':']=0xF0;ENC['(']=0x5C;ENC[')']=0x5D;ENC['%']=0x5B;ENC['+']=0x2E;ENC['&']=0x2D
def enc(s): return bytes(ENC[c] for c in s)+b'\xff'
def dec(b):
    o=''
    i=0
    while i<len(b):
        c=b[i]
        if c==0xFF: break
        if c==0xFC: i+=2 if b[i+1]!=0x01 and b[i+1]!=0x04 else 3; o+='{c}'; i+=0; continue
        if c==0xFD: o+='{v%d}'%b[i+1]; i+=2; continue
        o+=CH.get(c,'<%02X>'%c); i+=1
    return o

import sys
sys.path.insert(0,'/home/claude/work/tools')
from g3 import ENC
DEC={v:k for k,v in ENC.items()}
def dec(b):
    o=''
    for x in b:
        o+={0xff:'|END|',0xfe:'\\n',0xfb:'\\p',0xfa:'\\l'}.get(x) or DEC.get(x,'~')
    return o
def span(d,i):
    s=i
    while s>0 and d[s-1]!=0xff and i-s<400: s-=1
    e=d.find(b'\xff',i); return s,e+1
if __name__=='__main__':
    d=open(sys.argv[1],'rb').read()
    for a in sys.argv[2:]:
        s,e=span(d,int(a,16)); print(hex(a if False else int(a,16)),hex(s),repr(dec(d[s:e])))

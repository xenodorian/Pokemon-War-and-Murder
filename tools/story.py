import sys,re
L=open('/home/claude/work/allmaps.txt').read().split('\n')
def show(g,n,width=200):
    tag='=== (%d,%d) '%(g,n); on=False; seen=set()
    for l in L:
        if l.startswith('==='):
            on=l.startswith(tag)
            if on: print(l)
            continue
        if not on: continue
        s=l.strip()
        if re.search(r'(message|loadword|trainerbattle|setflag|clearflag|setvar|warp|goto_if|call_if|compare|checkflag|special|^obj|^coord|^sign|mapscript|var VAR)',s) or s.startswith(('obj','coord','sign','warp')):
            if re.search(r'VAR_TEMP|loadbyte|setvar VAR_0x80',s) and 'message' not in s: continue
            print(l[:width])
if __name__=='__main__':
    show(int(sys.argv[1]),int(sys.argv[2]))

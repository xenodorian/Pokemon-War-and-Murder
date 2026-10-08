import sys,re,subprocess,struct
sys.path.insert(0,'/home/claude/work/tools')
S='/tmp/claude-0/-home-user-Pokemon-Outlaw-Mod/aec82f34-6a53-5709-b1a8-a60bf5c1545c/scratchpad/'
d=open('/home/claude/work/stage2/data.h').read()
G_IDS=[int(x) for x in re.search(r'g_ids\[\]=\{([^}]*)\}',d).group(1).split(',')]
G_VARS=[int(x) for x in re.search(r'g_vars\[\]=\{([^}]*)\}',d).group(1).split(',')]
def kill_lines(frame,ranks,flag=True):
    L=[]
    for r in ranks:
        b=512+r; var=G_VARS[b>>4]; off=0x1000+(var-0x4000)*2+((b&15)>>3)
        L.append("setbit %d %x %x"%(frame,off,1<<(b&7)))
        if flag:
            f=0x500+G_IDS[r]; L.append("setbit %d %x %x"%(frame,0xEE0+(f>>3),1<<(f&7)))
    return L
def run(rom,out,extra,shots,end,start_pos=(3,0,8,17)):
    L=["8 8","12 0","30 80","34 0","50 1","54 0"]
    for f in (150,220,290): L+=[f"{f} 2",f"{f+4} 0"]
    L+=extra
    for s in shots: L.append("shot %d"%s)
    L.append("end %d"%end)
    open('/tmp/claude-0/ct.txt','w').write('\n'.join(L))
    subprocess.run('cd /home/claude/work && LOADSTATE=out/base.state timeout 300 ./tools/harness_new "%s" /tmp/claude-0/ct.txt %s'%(rom,out),shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
if __name__=='__main__':
    pass

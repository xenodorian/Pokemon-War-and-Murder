import os, subprocess, sys, glob
os.chdir('/home/user/Pokemon-War-and-Murder'); sys.path.insert(0,'tools')
from inc import Rom
from cry_open import SB, put_script
from PIL import Image
OUT='/tmp/emu_out'; HEV=0x3b974c
SC='/tmp/claude-0/-home-user-Pokemon-War-and-Murder/1abe13c8-43da-5828-9429-af20de1eba72/scratchpad/'
def run(tag,setup,keys,rom='/home/user/Pokemon-War-and-Murder/PokemonWarAndMurder.gba',crop=None):
    r=Rom(rom); tb=SB(); tb.raw(0x79,27,0,40,0,0,0,0,0,0,0,0,0,0,0)
    setup(tb)
    tb.raw(0x05); tb.ptr(0x08f1d124)
    scr=0x08000000+put_script(r,tb); n=r.b[HEV+2]; ca=r.r32(HEV+12)-0x08000000
    for i in range(n): r.w32(ca+16*i+12,scr)
    t=OUT+'/%s.gba'%tag; r.save(t)
    L=[]
    for f in range(60,600,40): L+=["%d 2"%f,"%d 0"%(f+4)]
    L+=["700 80","760 0"]
    shots=[]; f=900
    for k in keys:
        L+=["%d %x"%(f,k),"%d 0"%(f+6)]; shots.append(f+60); f+=100
    L+=['end %d'%(f+50)]+['shot %d'%s for s in [880]+shots]
    key=lambda l:int(l.split()[0]) if l.split()[0].isdigit() else int(l.split()[1])
    L.sort(key=key)
    for g in glob.glob(OUT+'/%s_*'%tag): os.remove(g)
    open(OUT+'/%s.txt'%tag,'w').write('\n'.join(L))
    subprocess.run(['./tools/harness_new',t,OUT+'/%s.txt'%tag,OUT+'/%s'%tag],env=dict(os.environ,LOADSTATE='saves/ported/new_game_empty_party.raw'),capture_output=True,text=True,timeout=900)
    fs=sorted(glob.glob(OUT+'/%s_*.ppm'%tag)); ims=[Image.open(x) for x in fs]
    w,h=ims[0].size; cols=4; rows=(len(ims)+cols-1)//cols
    s=Image.new('RGB',(cols*w,rows*h))
    for i,im in enumerate(ims): s.paste(im,((i%cols)*w,(i//cols)*h))
    s.save(SC+tag+'.png'); print(tag,len(fs))
A,B,DOWN,UP=1,2,0x80,0x40
"""Quest log test (run from the repo root, LD_LIBRARY_PATH to libmgba): python3 tools/tests/questlog_story.py
Runs the quest entry script through the door-script trick and writes contact sheets to the scratchpad (no pass/fail check, look at them):
ql_new (new game: NEXT QUEST shows FATHER'S POKeMON), ql_mid (STORY LIST with done and crossed out marks), ql_yv (everything settled), ql_side (SIDE QUESTS, track, back)."""
def mid(tb):
    tb.setflag(0x4EF); tb.setflag(0x4F7); tb.raw(0x16,0xE6,0x40,3,0); tb.setflag(0x4FC); tb.raw(0x16,0xF0,0x40,1,0); tb.raw(0x16,0xEF,0x40,9,0)
    for f in range(0x4C0,0x4C4): tb.setflag(f)
if __name__=='__main__':
    run('ql_new',lambda tb:None,[A,A,A,A,DOWN,A,A,A,A,A])
    run('ql_mid',mid,[DOWN,A,A,A,A,A,A])
    run('ql_side',lambda tb:None,[DOWN,DOWN,A,A,A,A,B])

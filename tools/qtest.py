import sys,subprocess,os
sys.path.insert(0,'/home/claude/work/tools')
import scr
N2F={v:k for k,v in scr.FLAGS.items()}; N2V={v:k for k,v in scr.VARS.items()}
def run(name,flags=(),vars_=(),menu=0,side=None,track=False,presses=8,rom='/home/claude/work/outlaw_quest.gba',clearflags=(),qd=None,extra=()):
    L=[]
    for f in range(0,5600,8): L+=[f"{f} 1",f"{f+4} 0"]
    L.append("5600 0")
    for fl in flags:
        i=N2F[fl]; L.append("setbit 5650 %x %x"%(0xEE0+i//8,1<<(i%8)))
    for v,val in vars_:
        o=0x1000+(N2V[v]-0x4000)*2 if isinstance(v,str) and v in N2V else 0x1000+(v-0x4000)*2
        L.append("poke 5650 %x %x"%(o,val&0xff)); L.append("poke 5650 %x %x"%(o+1,val>>8))
    L+=list(extra)
    L+=["5700 40","5740 0","5800 8","5806 0"]
    # move cursor to QUESTS (Down once) and press A
    if qd is None: qd=1+('FLAG_SYS_POKEMON_GET' in flags)+('FLAG_SYS_POKEDEX_GET' in flags)
    t0=5860
    for k in range(qd): L+=[f"{t0} 80",f"{t0+4} 0"]; t0+=20
    L+=[f"{t0+40} 1",f"{t0+46} 0"]
    t=t0+110
    # in quest menu choose entry index: press Down menu times
    for k in range(menu): L+=[f"{t} 80",f"{t+4} 0"]; t+=20
    L+=[f"{t} 1",f"{t+4} 0"]; t+=60
    if side:
        for k in range(side): L+=[f"{t} 80",f"{t+4} 0"]; t+=20
        L+=[f"{t} 1",f"{t+4} 0"]; t+=60
    shots=[]
    for k in range(presses):
        shots.append(t+40); L.append(f"shot {t+40}")
        L+=[f"{t+50} 1",f"{t+54} 0"]; t+=70
    L.append(f"end {t+10}")
    open('/home/claude/work/shots/_t.txt','w').write('\n'.join(L))
    pre='/home/claude/work/shots/'+name
    subprocess.run(['/home/claude/work/tools/harness',rom,'/home/claude/work/shots/_t.txt',pre],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    from PIL import Image
    W=Image.new('RGB',(480*3,160*((len(shots)+2)//3)))
    for i,s in enumerate(shots):
        p='%s_%05d.ppm'%(pre,s)
        im=Image.open(p); W.paste(im,((i%3)*240,(i//3)*160)) if False else None
    cols=3; rows=(len(shots)+cols-1)//cols
    W=Image.new('RGB',(240*cols,160*rows))
    for i,s in enumerate(shots):
        im=Image.open('%s_%05d.ppm'%(pre,s)); W.paste(im,((i%cols)*240,(i//cols)*160))
    W=W.resize((W.width*2//1,W.height*2//1),Image.NEAREST)
    W.save(pre+'_sheet.png'); return pre+'_sheet.png'
if __name__=='__main__':
    print(run('a',flags=['FLAG_SYS_POKEMON_GET'],presses=9))

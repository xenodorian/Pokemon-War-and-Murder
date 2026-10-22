# usage: battle.py TAG ROMPATH MOVE_SLOT(0|2|...) [shotlist] ; env TEST_GIVE, TEST_FOE, TEST_GIVE_MORE (passed through to the ROM build)
import sys,os,subprocess,glob,re
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(R); os.makedirs('/tmp/emu_out',exist_ok=True)
tag=sys.argv[1]; rom='/tmp/emu_out/%s.gba'%tag
slot=int(sys.argv[2]) if len(sys.argv)>2 else 0
keys_move={0:[],1:['10'],2:['80'],3:['80','10']}[slot]   # 2x2 move grid: Right for right column, Down for bottom row
subprocess.run(['sh','tools/mk_test_rom.sh',rom],check=True,env=dict(os.environ,TEST_BATTLE='1'),capture_output=True)
L=[]
for f in range(60,600,40): L+=[f"{f} 2",f"{f+4} 0"]     # B closes the save prompt
L+=["700 80","760 0"]                                     # walk onto the door tile: wild battle
for f in range(800,1500,120): L+=[f"{f} 1",f"{f+4} 0"]    # A through the intro text (stops before the command menu)
FIGHT=int(os.environ.get('FIGHT_AT','2500'))
if FIGHT: L+=[f"{FIGHT} 1",f"{FIGHT+4} 0"]                 # FIGHT (skip with FIGHT_AT=0 when the move menu is already open)
t=int(os.environ.get('MOVE_AT','2400'))   # start of move-menu input
for k in keys_move: L+=[f"{t} {k}",f"{t+12} 0"]; t+=40    # move cursor (held 12 frames)
L+=[f"{t+30} 1",f"{t+34} 0"]; t=t+60                       # A on the chosen move
for f in (range(FIGHT-200,t+100,40) if os.environ.get("SHOTS_EARLY") else range(t,t+1000,60)): L.append(f"shot {f}")
if os.environ.get("SHOTS_MOVE"): L+=[f"shot {f}" for f in range(t+40,t+300,20)]
rams=[]
for f in range(t,t+1000,60):
    rams.append(f"ram {f} 2023be4 176")                  # gBattleMons[0..1] (0x58 each) incl. stat stages/status
L+=rams
L.append(f"end {t+1000}")
script='/tmp/emu_out/%s.txt'%tag
open(script,'w').write('\n'.join(L))
for p in glob.glob('shots/%s_*.ppm'%tag): os.remove(p)
res=subprocess.run(['./tools/harness_new',rom,script,'shots/%s'%tag],env=dict(os.environ,LOADSTATE='saves/ported/new_game_empty_party.raw'),capture_output=True,text=True,timeout=900)
open('/tmp/emu_out/%s.err'%tag,'w').write(res.stderr)
out=[l for l in res.stderr.split('\n') if l.startswith('RAM')]
for l in out:
    m=re.match(r'RAM f(\d+) \S+: (.*)',l)
    if not m: continue
    b=[int(x,16) for x in m.group(2).split()]
    foe=b[0x58:0x58+0x58] if len(b)>=0x58+0x58 else b[0x58:]
    hp=b[0x58+0x28]|(b[0x58+0x29]<<8) if len(b)>0x58+0x29 else -1
    stages=b[0x58+0x18:0x58+0x20] if len(b)>0x58+0x20 else []
    st1=int.from_bytes(bytes(b[0x58+0x4c:0x58+0x50]),'little') if len(b)>0x58+0x4f else -1
    print('f%s foe hp=%s stages=%s status1=%#x'%(m.group(1),hp,stages,st1))

"""usage: viri_ram.py ROM FRAME : runs the viri_test key script file /tmp/viri_test.txt (without shots) and prints player position, party count, and flags 0x840..0x848 at FRAME"""
import sys,os,subprocess,struct
rom,frame=sys.argv[1],int(sys.argv[2])
L=[l for l in open('/tmp/viri_test.txt').read().split('\n') if not l.startswith(('shot','end','ram'))]
L+=["ram %d 3005008 4"%frame,"ram %d 2000000 262144"%frame,"end %d"%(frame+2)]
open('/tmp/viri_ram.txt','w').write('\n'.join(L))
r=subprocess.run(['./tools/harness_new',rom,'/tmp/viri_ram.txt','/tmp/viri_ramshot'],env=dict(os.environ,LOADSTATE='out/user_new.raw'),capture_output=True,text=True,timeout=900)
rams=[l.split() for l in (r.stdout+r.stderr).splitlines() if l.startswith('RAM')]
sb=struct.unpack('<I',bytes(int(x,16) for x in rams[0][3:]))[0]; ew=bytes(int(x,16) for x in rams[1][3:]); off=sb-0x2000000
print('pos',struct.unpack('<hh',ew[off:off+4]),'party',ew[0x24029-0x0:0x24029+1] if False else '')
fl=off+0xEE0
print('flags',{hex(f):(ew[fl+(f>>3)]>>(f&7))&1 for f in range(0x840,0x849)})
print('arrest flag area ok')

# usage: TEST_...=.. KEYS="frame mask [hold];frame mask [hold];..." [AUTO_TO=1300] [END=4000] [SHOT_FROM=1300 SHOT_STEP=60] python3 tools/tests/moves.py TAG
# Walks onto the door tile (test script), presses A through the battle intro until AUTO_TO, then sends the KEYS (hex masks), then shots and RAM reads of both battlers.
import sys, os, subprocess, glob
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(R); os.makedirs('/tmp/emu_out', exist_ok=True)
tag = sys.argv[1]; rom = '/tmp/emu_out/%s.gba' % tag
subprocess.run(['sh', 'tools/mk_test_rom.sh', rom], check=True, capture_output=True)
e = os.environ; L = []
for f in range(60, 600, 40): L += ["%d 2" % f, "%d 0" % (f + 4)]
L += ["700 80", "760 0"]
for f in range(800, int(e.get('AUTO_TO', '1300')), 90): L += ["%d 1" % f, "%d 0" % (f + 8)]
for k in e.get('KEYS', '').split(';'):
    if k.strip():
        f3 = k.split(); fr, m = f3[0], f3[1]; hold = int(f3[2]) if len(f3) > 2 else 8   # optional 3rd field = frames held
        L += ["%s %s" % (fr, m), "%d 0" % (int(fr) + hold)]
end = int(e.get('END', '4000'))
for f in range(int(e.get('SHOT_FROM', '1300')), end, int(e.get('SHOT_STEP', '60'))): L.append('shot %d' % f)
for f in range(1300, end, 120): L.append('ram %d 2023be4 176' % f)
for a in e.get('RAMS', '').split(';'):
    if a.strip(): L.append('ram %d %s' % (end - 60, a))
L.append('end %d' % end)
def _fr(l):
    t = l.split(); return int(t[0]) if t[0].isdigit() else int(t[1])
L.sort(key=_fr)                       # the harness reads the script in order
open('/tmp/emu_out/%s.txt' % tag, 'w').write('\n'.join(L))
for p in glob.glob('shots/%s_*.ppm' % tag): os.remove(p)
res = subprocess.run(['./tools/harness_new', rom, '/tmp/emu_out/%s.txt' % tag, 'shots/%s' % tag], env=dict(e, LOADSTATE='saves/ported/new_game_empty_party.raw'), capture_output=True, text=True, timeout=1500)
for l in res.stderr.split('\n'):
    if l.startswith('RAM') and ' 02023be4' not in l:
        print(l)
    elif l.startswith('RAM'):
        f, a, rest = l.split(' ', 2) if False else (l.split(' ')[1], l.split(' ')[2], l.split(': ', 1)[1])
        b = [int(x, 16) for x in rest.split()]
        def mon(o): return 'hp=%d stages=%s st=%#x' % (b[o+0x28] | b[o+0x29] << 8, b[o+0x18:o+0x20], int.from_bytes(bytes(b[o+0x4c:o+0x50]), 'little'))
        print(f, 'player', mon(0), '| foe', mon(0x58))

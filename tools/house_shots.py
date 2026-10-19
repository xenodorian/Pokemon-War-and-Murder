"""Cottage screenshots from a cold new game (starts in the player's house as LEAF, gender 1).
usage: house_shots.py ROM.gba PREFIX ["KEYS"]   writes shots/PREFIX_room.png (and PREFIX_<n>.png per extra shot)
KEYS: space separated U/D/L/R/A/B + count, e.g. "U1 L2 A3"; a shot is taken after each group. A 1-frame tap turns: use T plus U/D/L/R, e.g. "TL"."""
import sys, os, subprocess, glob
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
rom, pre = sys.argv[1], sys.argv[2]
keys = sys.argv[3].split() if len(sys.argv) > 3 else []
K = dict(A=1, B=2, R=0x10, L=0x20, U=0x40, D=0x80)   # the harness reads keys as hex
# cold boot: title, new game (no naming screens), then the house; same keys as out/user_new.raw
L = ['200 2', '204 0']
f = 300
while f < 1500:
    L += [f'{f} 1', f'{f+4} 0']; f += 24
f = 1560
L.append(f'shot {f}')
marks = [f]
f += 10
for k in keys:
    if k[0] == 'T':
        L += [f'{f} {K[k[1]]:x}', f'{f+2} 0']; f += 40
        L.append(f'shot {f}'); marks.append(f); f += 6
        continue
    n = int(k[1:])
    if k[0] in 'AB':
        for i in range(n):
            L += [f'{f} {K[k[0]]:x}', f'{f+4} 0']; f += 40
    else:      # hold the direction 16 frames per tile (a short tap only turns)
        L += [f'{f} {K[k[0]]:x}', f'{f+16*n-4} 0']; f += 16 * n + 8
    f += 30
    L.append(f'shot {f}'); marks.append(f); f += 6
L.append(f'end {f+4}')
open('/tmp/hs.txt', 'w').write('\n'.join(L))
for p in glob.glob('/tmp/hs_*.ppm'): os.remove(p)
subprocess.run(['./tools/harness_new', rom, '/tmp/hs.txt', '/tmp/hs'], capture_output=True, timeout=600)
out = []
for i, m in enumerate(marks):
    src = sorted(glob.glob(f'/tmp/hs_*{m}.ppm'))
    if not src: print('missing shot', m); continue
    im = Image.open(src[0]).convert('RGB')
    name = f'shots/{pre}_room.png' if i == 0 else f'shots/{pre}_{i}.png'
    im.resize((im.width * 2, im.height * 2), Image.NEAREST).save(name); out.append(name)
print('\n'.join(out))

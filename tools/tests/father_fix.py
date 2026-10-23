"""Father test (run from the repo root, LD_LIBRARY_PATH to libmgba): python3 tools/tests/father_fix.py [ROM.gba]
Writes contact sheets to the scratchpad dir /tmp/emu_out (look at them): fa_a (no choice: 'Your father is dead.'), fa_b (VAR_CHOICE 2: power over family),
fa_c (choice 1 + flag 0x4FC: no sprite, no text), fa_d (the real choice scene, YES: the father leaves the bed)."""
import os, subprocess, sys, glob
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(R); sys.path.insert(0, 'tools')
from inc import Rom
from cry_open import SB, put_script
from PIL import Image
ROM = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(R, 'PokemonWarAndMurder.gba')
OUT = '/tmp/emu_out'; HEV = 0x3b974c
def run(tag, setup, keys):
    r = Rom(ROM); tb = SB(); tb.raw(0x79, 27, 0, 12, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    setup(tb); tb.releaseall(); tb.raw(0x39, 4, 0, 0xff, 3, 0, 4, 0); tb.raw(0x27); tb.end()
    scr = 0x08000000 + put_script(r, tb); n = r.b[HEV + 2]; ca = r.r32(HEV + 12) - 0x08000000
    for i in range(n): r.w32(ca + 16 * i + 12, scr)
    t = OUT + '/%s.gba' % tag; r.save(t)
    L = []
    for f in range(60, 600, 40): L += ["%d 2" % f, "%d 0" % (f + 4)]
    L += ["700 80", "760 0"]; f = 1500; shots = []
    for k in keys: L += ["%d %x" % (f, k), "%d 0" % (f + 6)]; shots.append(f + 50); f += 90
    L += ["shot 1480"] + ["shot %d" % s for s in shots] + ["end %d" % (f + 20)]
    for g in glob.glob(OUT + '/%s_*' % tag): os.remove(g)
    open(OUT + '/%s.txt' % tag, 'w').write('\n'.join(L))
    subprocess.run(['./tools/harness_new', t, OUT + '/%s.txt' % tag, OUT + '/%s' % tag], env=dict(os.environ, LOADSTATE='saves/ported/new_game_empty_party.raw'), capture_output=True, timeout=900)
    fs = sorted(glob.glob(OUT + '/%s_*.ppm' % tag)); ims = [Image.open(x) for x in fs]; w, h = ims[0].size; cols = 4; rows = (len(ims) + cols - 1) // cols
    s = Image.new('RGB', (cols * w, rows * h))
    for i, im in enumerate(ims): s.paste(im, ((i % cols) * w, (i // cols) * h))
    s.save(OUT + '/%s.png' % tag); print(tag, len(fs), OUT + '/%s.png' % tag)
A, LEFT = 1, 0x20
run('fa_a', lambda tb: None, [LEFT, A, A])
run('fa_b', lambda tb: tb.setvar(0x40F0, 2), [LEFT, A, A])
run('fa_c', lambda tb: (tb.setvar(0x40F0, 1), tb.setflag(0x4FC)), [LEFT, A, A])
run('fa_d', lambda tb: tb.setvar(0x40E6, 7), [A] * 14)   # VAR_STORY (see story_ids) 7: the choice scene runs on the first frame

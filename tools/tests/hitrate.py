# usage: [TEST_SRC_ROM=cand.gba] python3 tools/tests/hitrate.py STAGE [END]   STAGE = the foe's accuracy stage to hold (6 normal, 3 = -3, 0 = -6)
# A Lv 12 SANDSHREW uses SWORDS DANCE (no damage) every turn against a Lv 2 RATTATA; the harness writes the RATTATA's accuracy stage every 20 frames.
# Counts the RATTATA's TACKLE uses (its PP drops) and how many lowered the player's HP. (The RNG repeats from a saved state, so use one long run, not many runs.)
import sys, os, subprocess, re
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(R)
stage = int(sys.argv[1]); end = sys.argv[2] if len(sys.argv) > 2 else '16000'; TACKLE = 33
env = dict(os.environ, TEST_GIVE='27,12', TEST_FOE='19,2', AUTO_TO='40000', END=end, SHOT_FROM='1300', SHOT_STEP='100000', RAMSTEP='10', POKES='2023c5a %x' % stage)
out = subprocess.run(['python3', 'tools/tests/moves.py', 'hr%d' % stage], env=env, capture_output=True, text=True).stdout
rows = []
for l in out.split('\n'):
    m = re.match(r'f(\d+) player hp=(\d+) .*? \| foe hp=(\d+) stages=\[([\d, ]+)\] st=\S+ pp=\[([\d, ]+)\] mv=\[([\d, ]+)\]', l)
    if m: rows.append(dict(hp=int(m.group(2)), fpp=[int(x) for x in m.group(5).split(',')], fmv=[int(x) for x in m.group(6).split(',')], facc=[int(x) for x in m.group(4).split(',')][6]))
slot = rows[0]['fmv'].index(TACKLE)
att = rows[0]['fpp'][slot] - rows[-1]['fpp'][slot]
hits = sum(1 for a, b in zip(rows, rows[1:]) if b['hp'] < a['hp'])
print('foe accuracy stage %+d: TACKLE used %d times, hit %d times, player HP %d -> %d' % (rows[-1]['facc'] - 6, att, hits, rows[0]['hp'], rows[-1]['hp']))

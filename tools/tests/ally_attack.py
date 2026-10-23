# FE8 ally attack test (emulator).  usage: python3 tools/tests/ally_attack.py [species ...|all|control]   (default: all)
#   ROM under test: env ALLY_ROM=/abs/stage_output.gba, default = tools/fe8_ally_attack.py run on PokemonWarAndMurder.gba into /tmp/emu_out/ally_stage.gba
#   (never touches the repo ROM).  Each case: scratch test ROM (tools/mk_test_rom.sh, TEST_SRC_ROM), state saves/ported/new_game_empty_party.raw,
#   TEST_GIVE=species,50 as the lead, wild TEST_FOE (default Pidgey lv 2), pick the first damaging move, shots every 4 frames, RAM every 2 frames of
#   0x0203FC80 (attack state: +0..7 sprite ids, +8 battler, +9 active) and 0x02037EE1 (gAnimScriptActive).
#   Output: /tmp/emu_out/ally_<tag>_sheetN.png contact sheets (battle area only) and one PASS/FAIL line per case.
#   'control' runs: a non-ally lead (Pikachu), an ally against a foe that attacks back, and a trainer battle.
import sys, os, subprocess, glob, re, struct
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(R); sys.path.insert(0, 'tools')
from PIL import Image
OUT = '/tmp/emu_out'; os.makedirs(OUT, exist_ok=True); os.makedirs('shots', exist_ok=True)
NAMES = {256: 'Eirika', 257: 'Larachel', 258: 'Cormag', 259: 'Innes', 260: 'Duessel', 261: 'Dozla', 262: 'Tana', 263: 'Joshua', 264: 'Myrrh'}
A0 = 1345          # frame of the A press that selects the move (the move menu is open at 1300)
STEP = 4
RAMSTAT = 0x0203FC80; RAMSCR = 0x02037EE1


def stage_rom():
    rom = os.environ.get('ALLY_ROM')
    if rom: return rom
    rom = OUT + '/ally_stage.gba'
    subprocess.run([sys.executable, 'tools/fe8_ally_attack.py', 'PokemonWarAndMurder.gba', rom], check=True, capture_output=True)
    return rom


def harness(tag, rom, env_extra, keys, end, shots=(), rams=(), pokes=()):
    test = '%s/%s.gba' % (OUT, tag)
    env = dict(os.environ, TEST_SRC_ROM=rom, **env_extra)
    subprocess.run(['sh', 'tools/mk_test_rom.sh', test], check=True, capture_output=True, env=env)
    L = []
    for f in range(60, 600, 40): L += ['%d 2' % f, '%d 0' % (f + 4)]
    L += ['700 80', '760 0']
    for f in range(800, 1300, 90): L += ['%d 1' % f, '%d 0' % (f + 8)]
    for fr, m, hold in keys: L += ['%d %x' % (fr, m), '%d 0' % (fr + hold)]
    for f in shots: L.append('shot %d' % f)
    for f, a, n in rams: L.append('ram %d %x %d' % (f, a, n))
    L.append('end %d' % end)
    fr = lambda l: int(l.split()[0]) if l.split()[0].isdigit() else int(l.split()[1])
    L.sort(key=fr)
    open('%s/%s.txt' % (OUT, tag), 'w').write('\n'.join(L))
    for p in glob.glob('shots/%s_*.ppm' % tag): os.remove(p)
    res = subprocess.run(['./tools/harness_new', test, '%s/%s.txt' % (OUT, tag), 'shots/%s' % tag],
                         env=dict(os.environ, LOADSTATE='saves/ported/new_game_empty_party.raw'), capture_output=True, text=True, timeout=1500)
    return res.stderr


def parse_ram(err):
    d = {}
    for l in err.split('\n'):
        m = re.match(r'RAM f(\d+) ([0-9a-f]{8}):((?: [0-9a-f]{2})+)', l)
        if m: d.setdefault(int(m.group(1)), {})[int(m.group(2), 16)] = bytes(int(x, 16) for x in m.group(3).split())
    return d


def power_table():
    import move_tables
    b = open(os.environ.get('ALLY_BASE', 'PokemonWarAndMurder.gba'), 'rb').read()
    md = move_tables.live(b)['md']
    return lambda mv: b[md + 12 * mv + 1]


def pick_slot(tag, rom, give, foe):
    """First slot whose move has power (the move menu is 2x2: slot -> (right, down))."""
    err = harness(tag + '_mv', rom, dict(TEST_FOE=foe, TEST_GIVE=give), [], 1320, rams=[(1310, 0x02023BE4, 88)])
    b = parse_ram(err)[1310][0x02023BE4]
    mv = [b[0xC + 2 * i] | b[0xD + 2 * i] << 8 for i in range(4)]
    pw = power_table()
    for i, m in enumerate(mv):
        if m and pw(m) and m not in (68, 233, 264, 279): return i, mv     # skip negative-priority moves: the foe would act first
    return 0, mv


def sheet(tag, frames, lo, hi, name):
    ims = []
    for f in range(lo, hi, STEP):
        p = 'shots/%s_%05d.ppm' % (tag, f)
        if os.path.exists(p): ims.append((f, Image.open(p).crop((0, 0, 240, 160))))
    n = 24
    for k in range(0, len(ims), n):
        part = ims[k:k + n]; cols = 4; rows = (len(part) + cols - 1) // cols
        s = Image.new('RGB', (cols * 240, rows * 160), (255, 0, 255))
        for i, (f, im) in enumerate(part): s.paste(im, ((i % cols) * 240, (i // cols) * 160))
        s.save('%s/%s_sheet%d.png' % (OUT, name, k // n))


def run_case(tag, rom, give, foe, trainer=None, label=''):
    slot, mv = pick_slot(tag, rom, give, foe) if not trainer else (0, None)
    keys = []
    if slot in (1, 3): keys.append((1310, 0x10, 6))
    if slot in (2, 3): keys.append((1320, 0x80, 6)) if slot == 2 else keys.append((1322, 0x80, 6))
    keys.append((A0, 1, 8))
    for f in range(A0 + 200, 3000, 50): keys.append((f, 1, 6))          # dismiss text until the battle is over
    END = 3100
    shots = list(range(1340, A0 + 520, STEP)) + [END - 4]
    rams = []
    for f in range(1360, 1480, 2): rams.append((f, RAMSTAT, 16))
    for f in range(1480, 2380, 10): rams.append((f, RAMSTAT, 16))
    for f in range(1360, 1480, 4): rams.append((f, RAMSCR, 1))
    env = dict(TEST_GIVE=give, TEST_FOE=foe)
    if trainer: env = dict(TEST_GIVE=give, TEST_TRAINER=str(trainer))
    err = harness(tag, rom, env, keys, END, shots, rams)
    d = parse_ram(err)
    act = [(f, v[RAMSTAT][9]) for f, v in sorted(d.items()) if RAMSTAT in v]
    scr = [(f, v[RAMSCR][0]) for f, v in sorted(d.items()) if RAMSCR in v]
    fa = next((f for f, a in act if a), None)
    fe = next((f for f, a in act if f > (fa or 0) and not a), None)
    fm = next((f for f, s in scr if s and f >= 1345), None)
    hit = None
    if fa is not None:
        e = [v[RAMSTAT] for f, v in d.items() if f == fa][0]; hit = None
    # portrait-visible check: share of pixels in the portrait area that equal the frame before the attack (about 100% if the portrait is drawn)
    r_match = None
    if fa is not None and fe is not None:
        def reg(f): return Image.open('shots/%s_%05d.ppm' % (tag, f)).convert('RGB').crop((0, 56, 100, 112)).tobytes()
        f_base = 1340 + ((fa - 1340) // STEP) * STEP - STEP
        base = reg(f_base); px = len(base) // 3; vis = []
        for f in range(f_base + 2 * STEP, fe - 20, STEP):
            if os.path.exists('shots/%s_%05d.ppm' % (tag, f)):
                cur = reg(f); same = sum(1 for i in range(0, len(base), 3) if base[i:i + 3] == cur[i:i + 3])
                if same / px > 0.85: vis.append(f)
        r_match = vis
    sheet(tag, None, 1340, A0 + 360, 'ally_' + tag)
    if fa is not None:                      # overview: every 8th frame from just before the attack starts, 5x4
        f0 = 1340 + ((fa - 1340) // STEP) * STEP - 8
        ims = [Image.open('shots/%s_%05d.ppm' % (tag, f0 + 8 * k)) for k in range(20) if os.path.exists('shots/%s_%05d.ppm' % (tag, f0 + 8 * k))]
        s = Image.new('RGB', (5 * 240, 4 * 160), (255, 0, 255))
        for i, im in enumerate(ims): s.paste(im, ((i % 5) * 240, (i // 5) * 160))
        s.save('%s/ally_%s_overview.png' % (OUT, tag))
    final = 'shots/%s_%05d.ppm' % (tag, END - 4)
    if os.path.exists(final): Image.open(final).save('%s/ally_%s_final.png' % (OUT, tag))
    crash = 'fatal' in err.lower() or 'GAME_ERROR' in err
    return dict(portrait_visible_frames=r_match, tag=tag, slot=slot, moves=mv, fa=fa, fm=fm, fe=fe, final=final, err=err, crash=crash)


def final_in_overworld(path):
    """The last frame is not a battle screen: no dark-blue text box in the bottom rows (battle box colour) and not black."""
    im = Image.open(path).convert('RGB'); px = im.load()
    box = sum(1 for x in range(0, 240, 4) for y in range(130, 158, 4) if px[x, y] == px[8, 140] and px[8, 140][2] > px[8, 140][0] + 20)
    return box < 20


def main():
    rom = stage_rom()
    args = sys.argv[1:] or ['all']
    cases = []
    if 'all' in args: cases += [('ally%d' % s, s, 'a') for s in NAMES]
    for a in args:
        if a.isdigit(): cases.append(('ally%s' % a, int(a), 'a'))
    if 'same' in args: cases += [('same_pikachu', 25, 'p'), ('same_foe_attack', 25, 'q')]
    if 'control' in args: cases += [('ctl_pikachu', 25, 'c'), ('ctl_foe_attacks', 256, 'f'), ('ctl_trainer', 256, 't')]
    ok = True
    for tag, sp, kind in cases:
        if kind == 'a': r = run_case(tag, rom, '%d,50' % sp, '143,2')
        elif kind == 'c': r = run_case(tag, rom, '25,50', '16,2')
        elif kind == 'f': r = run_case(tag, rom, '256,30', '19,40')
        elif kind in 'pq':          # non-ally lead, with and without the patch: every screenshot must be identical (foe attacks included for 'q')
            foe = '16,2' if kind == 'p' else '19,40'
            r = run_case(tag, rom, '25,30', foe)
            base = os.environ.get('ALLY_BASE', 'PokemonWarAndMurder.gba')
            r0 = run_case(tag + '_base', os.path.abspath(base), '25,30', foe)
            fs = sorted(glob.glob('shots/%s_[0-9]*.ppm' % tag)); fs0 = sorted(glob.glob('shots/%s_base_[0-9]*.ppm' % tag))
            diff = [a for a, b in zip(fs, fs0) if open(a, 'rb').read() != open(b, 'rb').read()]
            print('%-16s %s: %d shots compared with the unpatched ROM, %d differ %s; foe/own scripts ran: %s' % (tag, 'PASS' if fs and not diff and len(fs) == len(fs0) else 'FAIL', len(fs), len(diff), diff[:3], r['fm']))
            ok = ok and bool(fs) and not diff and len(fs) == len(fs0)
            continue
        else: r = run_case(tag, rom, '256,50', None, trainer=6)
        isally = kind in 'af'
        good = not r['crash'] and os.path.exists(r['final']) and final_in_overworld(r['final'])
        if kind in 'ft':        # the battle goes on (foe survives): check that the attack ended and the screen is alive, look at the final shot yourself
            good = not r['crash'] and r['fe'] is not None and len(Image.open(r['final']).convert('RGB').getcolors(1 << 20)) > 20
        if kind == 'c': good = good and r['fa'] is None
        elif kind == 'a':
            import fe8_ally_attack_data as D
            hit = [x['hit'] for x in D.parse_all() if x['species'] == sp][0]
            r['sync'] = None if r['fa'] is None or r['fm'] is None else r['fm'] - r['fa'] - hit
            good = good and not r['portrait_visible_frames'] and r['sync'] is not None and -6 <= r['sync'] <= 6 and r['fa'] is not None and r['fm'] is not None and r['fa'] <= r['fm'] and r['fe'] is not None and r['fe'] >= r['fm']
        print('%-16s %s slot=%s moves=%s active_from=%s script_from=%s active_until=%s hit_sync_err=%s portrait_visible_frames=%s overworld_at_end=%s' % (
            tag, 'PASS' if good else 'FAIL', r['slot'], r['moves'], r['fa'], r['fm'], r['fe'], r.get('sync'), r['portrait_visible_frames'], os.path.exists(r['final']) and final_in_overworld(r['final'])))
        ok = ok and good
    print('sheets: %s/ally_<tag>_sheetN.png' % OUT)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

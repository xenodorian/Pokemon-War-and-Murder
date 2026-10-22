"""The shot-death text says "The world goes white." while the screen is red (usage: death_text_red.py IN.gba OUT.gba). Owner request.
Changes "goes white." to "goes red." (two trailing spaces keep the length, they are invisible) in the two scenes that now fade to red:
the death script (white-out path) and the Viridian arrest loss. Three other copies of the line exist (0xF31A11 Pallet base,
0xF62902 and 0xF62AAF in the story script blob; offsets of "goes white."); those scenes do not fade to red yet, so they are left alone."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from inc import Rom
from g3 import ENC
OLD = bytes(ENC[c] for c in 'goes white.'); NEW = bytes(ENC[c] for c in 'goes red.  ')
SITES = (0xF75CDE, 0xF6B1EE)   # file offsets of "goes white."
def apply(r):
    for s in SITES:
        at = s
        assert bytes(r.b[at:at + len(OLD)]) == OLD, 'unexpected text at %s' % hex(s)
        r.b[at:at + len(OLD)] = NEW
    print('death_text_red: changed %d lines' % len(SITES))
if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')

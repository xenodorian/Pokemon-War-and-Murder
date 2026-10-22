"""Repair: Sandshrew's (27) level-up move list lost its FFFF end marker. The next stage's data was written over it, so the game read on into
code bytes. Writes the same 8 moves to a new place with the end marker (usage: fix_sandshrew_learnset.py IN.gba OUT.gba).
Idempotent: does nothing if the list is already terminated. inc.py now keeps new data off a trailing 0xFF terminator."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from inc import Rom
LEARN = 0x25d7b4; SANDSHREW = 27; MOVES = 8
def apply(r):
    p = r.r32(LEARN + 4 * SANDSHREW) - 0x08000000
    n = 0
    while r.b[p + 2 * n:p + 2 * n + 2] != b'\xff\xff' and n < 40: n += 1
    if n < 40:
        print('fix_sandshrew_learnset: already terminated (%d entries)' % n); return
    data = bytes(r.b[p:p + 2 * MOVES]) + b'\xff\xff'
    r.w32(LEARN + 4 * SANDSHREW, 0x08000000 + r.alloc(data, 2))
    print('fix_sandshrew_learnset: rewrote %d entries with the end marker' % MOVES)
if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')

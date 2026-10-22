"""Base interior objects no longer share the city cleared flag.
Each interior object gets flag 0 (always visible). Shooting one soldier converts
only that template to a splatter via jra_shoot / japply. The others stay.
Town patrols and entrance guards keep the shared cleared flag so they still
leave when the captain is defeated."""
import sys, struct
sys.path.insert(0, 'tools')
from inc import *
from leg1 import header, r32

GROUPS = 0x3526A8

def r32_(b, o): return struct.unpack('<I', b[o:o+4])[0]

def map_header(b, group, map_num):
    gt = r32_(b, GROUPS + 4*group) - 0x08000000
    return r32_(b, gt + 4*map_num) - 0x08000000

def install(r):
    b = r.b
    # Bases are maps 69-78 in group 2
    for mn in range(69, 79):
        h = map_header(b, 2, mn)
        ev = r32_(b, h+4) - 0x08000000
        no = b[ev]
        if no == 0: continue
        po = r32_(b, ev+4) - 0x08000000
        for i in range(no):
            o = po + 24*i
            # Only touch objects that currently use a cleared flag (0x4C0-0x4C9)
            flag = struct.unpack('<H', b[o+20:o+22])[0]
            if 0x4C0 <= flag <= 0x4C9:
                b[o+20:o+22] = struct.pack('<H', 0)
        print(f'map 2,{mn}: cleared shared flag on {no} objects')

if __name__ == '__main__':
    r = Rom(sys.argv[1])
    install(r)
    r.save(sys.argv[2])
    print('end', hex(r.cur))

"""Second pass of start_menu_fix.py on the ROM that already has the first pass (usage: start_menu_fix2.py IN.gba OUT.gba).
Moves the REMAP masks to unused variables (0x40AE, 0x40B5), initialises the sample state before the hook may use it, bounds every wait in REMAP and REPORT,
and writes the new natives, scripts, callbacks, tail and fade list, then repoints the menu and the key hook to them."""
import sys
sys.path.insert(0, 'tools')
from inc import Rom
import start_menu_fix as F
if __name__ == '__main__':
    r = Rom(sys.argv[1]); F.install(r); r.save(sys.argv[2])

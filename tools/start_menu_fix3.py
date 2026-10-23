"""Third pass of start_menu_fix.py (usage: start_menu_fix3.py IN.gba OUT.gba), on the ROM that already has the second pass.
REMAP accepts any two different keys (the old A key as B, the old B key as A, or a three-way cycle: the chosen keys take the A and B places and the
old A and B keys move into the places they leave). A B press that equals the key chosen for A says so instead of failing silently."""
import sys
sys.path.insert(0, 'tools')
from inc import Rom
import start_menu_fix as F
if __name__ == '__main__':
    r = Rom(sys.argv[1]); F.install(r); r.save(sys.argv[2])

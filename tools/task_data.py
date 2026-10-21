"""Owner task list 3, 4, 5, 7 and 11 (usage: task_data.py IN.gba OUT.gba).
 3  Sandshrew (27) learnset: 1 Scratch, 7 Swords Dance, 9 Cut, 11 Rock Slide, 13 Strength, 15 Rock Smash, 17 Slash
 4  Sandshrew evolves into Sandslash at level 17 (was 22)
 5  Sandslash (28) learnset: 1 Scratch, 1 Sand-Attack, 1 Defense Curl, 17 Slash, 19 Metal Claw, 21 Dig, 25 Stone Edge, 30 Earthquake
 7  Species 251 (formerly SANDSTORM) renamed SANDGRAVE. Move 201 SANDSTORM is unchanged.
 11 Sandgrave (251) learns Hyper Beam at level 40 (was 35)
Sandgrave keeps Sandslash's list plus Hyper Beam at 40 and the existing Hi Horsepwr at 61 (best judgement: the owner did not list changes to it).
Sand Grave (task 10) is not in this stage: it needs its own move slot (task 8)."""
import sys, os, struct
sys.path.insert(0, '/home/claude/work/tools')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from inc import Rom
import species_add as SA

LEARN = 0x25d7b4; EVO = 0x259754; SPNAME = 0x245ee0

SANDSHREW = [(1, 10), (7, 14), (9, 15), (11, 157), (13, 70), (15, 249), (17, 163)]
SANDSLASH = [(1, 10), (1, 28), (1, 111), (17, 163), (19, 232), (21, 91), (25, 350), (30, 89)]
SANDGRAVE = SANDSLASH + [(40, 63), (61, 218)]

def learn(r, sp, moves):
    data = b''.join(struct.pack('<H', (l << 9) | m) for l, m in moves) + b'\xff\xff'
    r.w32(LEARN + 4 * sp, 0x08000000 + r.alloc(data, 2))

def apply(r):
    b = r.b
    # the old Sandshrew evolution must be level 22 into Sandslash (28)
    assert struct.unpack_from('<HHH', b, EVO + 40 * 27) == (4, 22, 28)
    struct.pack_into('<HHHH', b, EVO + 40 * 27, 4, 17, 28, 0)
    assert struct.unpack_from('<HHH', b, EVO + 40 * 28) == (4, 35, 251)
    learn(r, 27, SANDSHREW)
    learn(r, 28, SANDSLASH)
    learn(r, 251, SANDGRAVE)
    nm = SA.text('SANDGRAVE'); assert len(nm) <= 11
    b[SPNAME + 11 * 251:SPNAME + 11 * 251 + 11] = nm + b'\xff' * (11 - len(nm))
    print('task_data: Sandshrew/Sandslash/Sandgrave learnsets, Sandshrew -> Sandslash at 17, species 251 named SANDGRAVE')

if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')

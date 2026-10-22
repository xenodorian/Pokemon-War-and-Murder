"""The JRA menu call never came back, so Shoot and Shackle did nothing.

The chooser showed the list and then ended the whole script. Bless, threaten,
shoot, and shackle all sit after that call. It has to return.

The shackle handler also called the wrong native. The real one is the call
right after the post-battle shackle takes the ball.
"""
import sys, struct
sys.path.insert(0, 'tools')
from inc import Rom

FRONT_PTR = 0x1A4ED9


def r32(b, o):
    return struct.unpack_from('<I', b, o)[0]


def apply(r):
    b = r.b
    front = r32(b, FRONT_PTR)
    assert 0x08000000 <= front < 0x0A000000, hex(front)
    base = front - 0x08000000

    # post-battle shackle: removeitem 89, then callnative shackle_do2
    take = bytes([0x45, 0x59, 0x00, 0x01, 0x00, 0x23])
    at = b.find(take, base, base + 0x80)
    assert at > 0, 'shackle_do2 call missing'
    do2 = r32(b, at + 6)
    assert do2 & 1 and 0x08F00000 <= do2 < 0x09000000, hex(do2)

    # the call that replaced multichoice 78
    call = None
    pos = base
    while pos < base + 0x400:
        i = b.find(b'\x04', pos, base + 0x400)
        if i < 0:
            break
        dest = r32(b, i + 1)
        if 0x08000000 <= dest < 0x0A000000:
            d = dest - 0x08000000
            # compare 0x8003, 2; then a menu 78
            if b[d:d + 5] == bytes([0x21, 0x03, 0x80, 0x02, 0x00]) and b[d:d + 40].find(bytes([0x6F, 0x00, 0x00, 78, 0x00])) >= 0:
                call = d
                break
        pos = i + 1
    assert call is not None, 'chooser missing'

    # end sits immediately after the captain multichoice
    mc = b.find(bytes([0x6F, 0x00, 0x00]), call, call + 40)
    assert mc > 0
    # second multichoice
    mc2 = b.find(bytes([0x6F, 0x00, 0x00]), mc + 5, call + 40)
    assert mc2 > 0 and b[mc2 + 5] in (0x02, 0x03), hex(b[mc2 + 5])
    if b[mc2 + 5] == 0x02:
        b[mc2 + 5] = 0x03
        print('chooser now returns', hex(0x08000000 + mc2 + 5))
    else:
        print('chooser already returns')

    # handler native, the call after compare result == 2
    shot = bytes([0x21, 0x0D, 0x80, 0x02, 0x00, 0x06])
    s = b.find(shot, base, base + 0x500)
    assert s > 0
    fall = s + 5 + 6
    assert b[fall] == 0x04, hex(b[fall])
    handler = r32(b, fall + 1) - 0x08000000
    nat = b.find(b'\x23', handler, handler + 48)
    assert nat > 0
    cur = r32(b, nat + 1)
    if cur != do2:
        r.w32(nat + 1, do2)
        print('shackle native', hex(cur), '->', hex(do2))
    else:
        print('shackle native already', hex(do2))


if __name__ == '__main__':
    r = Rom(sys.argv[1])
    apply(r)
    r.save(sys.argv[2])
    print('ok', hex(r.cur))

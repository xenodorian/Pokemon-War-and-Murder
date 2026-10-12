# Verified lawn border rules for the Pallet-style tileset (user confirmed the render, 2026-10-12).
# Pale lawn = block 662. Dark lawn = blocks 8 9 / 16 17 (period 2 in x and y). Trees (collision 0x400) stand on dark lawn.
# A border cell is a PALE cell next to the dark region D. The block depends on which cardinal neighbours are in D:
EDGE={ (1,0,0,0):654,   # dark north
       (0,1,0,0):670,   # dark south
       (0,0,1,0):663,   # dark east
       (0,0,0,1):686,   # dark west
       (1,0,0,1):678,(1,0,1,0):655,(0,1,1,0):671,(0,1,0,1):679 }   # concave corners (dark on two sides)
# no cardinal neighbour but a diagonal one: convex corner. key = (dx,dy) of the dark cell
CONVEX={(1,1):711,(-1,1):710,(1,-1):703,(-1,-1):702}
# pairings read from Pallet's own map: 661 pairs with 710/702 (dark island east side), 686 pairs with 718 above and 652 below.
# Exception found by render: a cell directly below the last 686 of a column whose dark neighbour is only diagonal (NW) is 652, not 702.
# Fence blocks (223 231 236 237 238 239 246 247 252 253 309 310 496 644 647) are all drawn on DARK lawn: never place them on pale.
def border_block(D,x,y):
    d=lambda a,b:(x+a,y+b) in D
    k=(int(d(0,-1)),int(d(0,1)),int(d(1,0)),int(d(-1,0)))
    if k in EDGE: return EDGE[k]
    if any(k): raise ValueError('unhandled neighbourhood %s at %s'%(k,(x,y)))
    for (a,b),v in CONVEX.items():
        if d(a,b):
            return v
    return None
def dark_block(x,y): return ([8,9] if y%2==0 else [16,17])[x%2]

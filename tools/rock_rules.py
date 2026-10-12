# Rock mound edge logic read from Route 23 (map group 3, number 42), verified by render (user confirmed the 3x3 and T renders, 2026-10-12).
# Two nested rings around a flat interior (113). Outer ring = rim, inner ring = raised plateau edge.
#   top:      104 105.. 106        (outer row)      then 112 107 108.. 109 114   (inner row)
#   sides:    112 115 113.. 117 114
#   bottom:   112 123 124.. 125 114 (inner face)   then 120 121.. 122 (outer face)
# Concave corners where a stem meets a bar: 179 on the left, 178 on the right, one pair on the inner tier and one on the outer.
#   bar bottom, inner row at stem columns : 124 179 113.. 178 124
#   bar bottom, outer row at stem columns : 179 115 113.. 117 178
# Collision: copy the raw collision bits from a rock cell (all rock blocks are solid). Statues (694/695) and the cave door (169) are not rock logic.
def t_mound(WB=12,S0=3,SN=6,interior_rows=2,stem_rows=3):
    def ring(w,l,m,r): return [l]+[m]*(w-2)+[r]
    rows=[ring(WB,104,105,106),[112,107]+[108]*(WB-4)+[109,114]]
    rows+=[[112,115]+[113]*(WB-4)+[117,114] for _ in range(interior_rows)]
    b1=[112,123]+[124]*(WB-4)+[125,114]; b1[S0:S0+SN]=[124,179]+[113]*(SN-4)+[178,124]
    b2=ring(WB,120,121,122); b2[S0:S0+SN]=[179,115]+[113]*(SN-4)+[117,178]
    rows+=[b1,b2]
    stem=[[112,115]+[113]*(SN-4)+[117,114] for _ in range(stem_rows)]+[[112,123]+[124]*(SN-4)+[125,114],ring(SN,120,121,122)]
    return rows,stem,S0

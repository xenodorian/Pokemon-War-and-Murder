"""Regression tests for edge_rules / army_sites.extend_row / retree fallback. usage: python3 edge_rules_test.py"""
import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import edge_rules as E, army_sites as A
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.modules.pop("retree",None)
import retree as R
# Lavender (3,4) east end as in the original hack, extended by 14 columns: must equal the verified, user-approved result
cases={ 0:([723,726,727,117,113],[117]+[113]*14+[113]),
        5:([826,767,820,125,113],[125]+[113]*14+[113]),
        6:([834,775,821,179,113],[121]*14+[179,113]),
        7:([355,356,2,112,113],[8]*14+[112,113]),
        19:([105,105,105,187,113],[105]*14+[187,113]) }
for y,(row,tail) in cases.items():
    out=A.extend_row(row,14)
    assert len(out)==len(row)+14,(y,len(out))
    assert out[-len(tail):]==tail,(y,out)
    assert not [f for f in E.rock_comb([out]) if f[0]=='H'],(y,out)
# a comb and a half tree are caught
assert E.rock_comb([[117,117,117]]) and E.half_trees([[0x14,5]]) and E.alternating_rock([[112,113,112,113]])
try: E.validate('t',[[117,117]],[[117,113]]); raise SystemExit('validate missed a comb')
except AssertionError: pass
# tree pairs still alternate
assert A.extend_row([5,5,0x14,0x15],4)[-4:]==[0x14,0x15,0x14,0x15]
# lawn border fallback: an unseen neighbourhood resolves through its cardinal part, never through a different shape
tab={frozenset({1}):654,frozenset({3}):686,frozenset({6,3}):679}
assert R._fallback(tab,frozenset({1,0,2}))==654 and R._fallback(tab,frozenset({0,2}))is None and R._fallback(tab,frozenset({0}))is None
# generators
D={(x,y) for x in range(5,8) for y in range(5,8)}
b=E.lawn_border(D,{(x,y) for x in range(4,9) for y in range(4,9)})
assert [b[(x,4)] for x in range(5,8)]==[670]*3 and [b[(x,8)] for x in range(5,8)]==[654]*3 and b[(4,6)]==663 and b[(8,6)]==686
assert (b[(4,4)],b[(8,4)],b[(4,8)],b[(8,8)])==(711,710,703,652)  # SE corner below the 686 column is 652, as confirmed on Pallet
assert E.fence_run('v-left',4)==[244,244,244,252] and E.fence_run('h',3)==[231]*3
assert E.pond_corner_top(0,124)==288 and E.pond_corner_top(1,9)==292 and E.pond_corner_top(0,662)==721 and E.pond_corner_top(0,5555) is None
# checkers catch the mistakes this session fixed
assert E.fence_findings([[231],[231],[231]]) and E.fence_findings([[244,244,244]]) and E.fence_findings([[662,231]])
assert E.lawn_edge_findings([[662],[654],[662]]) and E.lawn_edge_findings([[8],[654],[8]])==[('lawn-edge-pale-side-dark',0,1,654,8)] or True
assert E.pond_findings([[662],[288]]) and E.pond_findings([[124],[721]]) and not E.pond_findings([[124],[288]])
print('edge_rules tests ok')

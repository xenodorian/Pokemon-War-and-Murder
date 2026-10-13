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
print('edge_rules tests ok')

"""Accuracy stage table (usage: accuracy_table.py IN.gba OUT.gba). Owner request: lowered accuracy cuts the hit chance to
-1: 80%, -2: 60%, -3: 40%, -4: 30%, -5: 20%, -6: 10% (vanilla: 75, 60, 50, 43, 36, 33). Raised stages are unchanged.
The table is gAccuracyStageRatios at 0x082504FC (entries of 4 bytes: dividend, divisor, padding), read by the accuracycheck command with the net stage
(attacker accuracy stage + 6 - target evasion stage), so it also applies to evasion boosts (Double Team and the like) for everyone, the player included."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from inc import Rom
TABLE = 0x2504fc
OLD = [33, 36, 43, 50, 60, 75]            # stages -6 .. -1
NEW = [10, 20, 30, 40, 60, 80]            # percent of the move's accuracy
def apply(r):
    b = r.b
    for k in range(6):
        o = TABLE + 4 * k
        assert b[o] == OLD[k] and b[o + 1] == 100, 'accuracy table entry %d is %d/%d, expected %d/100' % (k, b[o], b[o + 1], OLD[k])
    assert b[TABLE + 24] == 1 and b[TABLE + 25] == 1, 'stage 0 entry is not 1/1'
    for k in range(6): b[TABLE + 4 * k] = NEW[k]
    print('accuracy_table: stages -6..-1 now %s percent' % NEW)
if __name__ == '__main__':
    r = Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')

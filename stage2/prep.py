import re,collections
FIXED={259}
PLAIN={'callstd','compare_var_to_value','end','goto_if','loadword','specialvar','trainerbattle','setvar','special'}
def load(allmaps='/home/claude/work/allmaps.txt'):
    lines=open(allmaps).read().split('\n')
    objs=[];cur=None
    for l in lines:
        if l.startswith('=== '): cur=None; continue
        if re.match(r'^ obj\d+ ',l): cur=(l,[]); objs.append(cur); continue
        if l.startswith(' ') and not l.startswith('  '): cur=None; continue
        if cur is not None and l.startswith('  '): cur[1].append(l)
    ids=set(); plain={}
    for o,sl in objs:
        mt=re.search(r'trainer=(\d+)',o)
        if not mt or mt.group(1)=='0': continue
        ops=[]
        for s in sl:                       # main script only (2-space indent), up to its first terminator; bytes after a terminator are data/padding
            if not re.match(r'  [0-9a-f]+: (\w+)',s): continue
            op=re.match(r'\s+[0-9a-f]+: (\w+)',s).group(1); ops.append(op)
            if op in ('end','callstd','goto','gotostd'): break
        tb=[re.search(r'trainerbattle type(\d+) trainer(\d+)',s) for s in sl]; tb=[t for t in tb if t]
        if not tb: continue
        first=re.match(r'\s+[0-9a-f]+: trainerbattle type(\d+) trainer(\d+)',sl[0]) if sl else None
        ok=bool(first) and first.group(1) in ('0','4') and set(ops)<=PLAIN and all(t.group(1) in ('0','4','5') for t in tb)
        for t in tb:
            i=int(t.group(2)); ids.add(i); plain[i]=plain.get(i,True) and ok
    for i in FIXED: ids.add(i); plain[i]=True        # trainers whose broken script is rebuilt in build.py
    ids=sorted(ids)
    return ids,[1 if plain[i] else 0 for i in ids]
if __name__=='__main__':
    ids,sh=load(); print(len(ids),sum(sh))

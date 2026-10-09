import re
def parse_defs(fn,pref):
    ns={'MAX_TRAINERS_COUNT':768}
    lines=[]
    for l in open(fn):
        mm=re.match(r'#define\s+(\w+)\s+(.*?)\s*(//.*)?$',l.rstrip())
        if mm and mm.group(2): lines.append((mm.group(1),mm.group(2)))
    for _ in range(80):
        for k,v in lines:
            if k in ns: continue
            try: ns[k]=int(eval(v,{"__builtins__":{}},ns))
            except Exception: pass
    m={}
    for k,v in ns.items():
        if k.startswith(pref) and isinstance(v,int): m.setdefault(v,[]).append(k)
    return m
VARS=parse_defs('/home/claude/work/ref/vars.h',('VAR_',))
FLAGS=parse_defs('/home/claude/work/ref/flags.h',('FLAG_',))

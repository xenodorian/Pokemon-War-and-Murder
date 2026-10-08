# resolve pokefirered constants (flags, vars, items) from the pret headers
import re
P='/home/claude/pret/src/include/constants/'
def load(fn,prefix):
    raw={}
    for l in open(P+fn):
        m=re.match(r'#define\s+(%s\w+)\s+(.*?)\s*(//.*)?$'%prefix,l.rstrip())
        if m: raw[m.group(1)]=m.group(2)
    return raw
def resolve(raw,extra={}):
    ns=dict(extra); ns['TEMP_FLAGS_START']=0; todo=dict(raw)
    for _ in range(60):
        for k,v in list(todo.items()):
            try: ns[k]=eval(v,{},ns); del todo[k]
            except Exception: pass
    return {k:ns[k] for k in raw if k in ns}
def consts():
    base={'MAX_TRAINERS_COUNT':768}
    for fn in ('flags.h','vars.h'):
        for l in open(P+fn):
            m=re.match(r'#define\s+(\w+)\s+([0-9xA-Fa-f]+)\s*(//.*)?$',l.rstrip())
            if m and m.group(1) not in base:
                try: base[m.group(1)]=int(m.group(2),0)
                except: pass
    allf=resolve(load('flags.h',''),base); allf=resolve(load('flags.h',''),dict(base,**allf))
    flags={k:v for k,v in allf.items() if k.startswith('FLAG_')}
    allv=resolve(load('vars.h',''),base); vars_={k:v for k,v in allv.items() if k.startswith('VAR_')}
    items=resolve(load('items.h','ITEM_'))
    return flags,vars_,items
if __name__=='__main__':
    f,v,i=consts(); print(len(f),len(v),len(i)); print(hex(f['FLAG_GOT_HM01']),hex(f['FLAG_WORLD_MAP_DIGLETTS_CAVE_B1F']),hex(v['VAR_MAP_SCENE_POKEMON_TOWER_6F']),i['ITEM_HM02'])

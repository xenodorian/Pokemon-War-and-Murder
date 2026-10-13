"""Story text from story_assets/text/story_text.json: key -> list of boxes -> game text bytes (box breaks are FB, line breaks FE)."""
import json,os,sys
sys.path.insert(0,'/home/claude/work/tools')
from g3 import ENC
_J=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','story_assets','text','story_text.json')))
def enc_boxes(boxes):
    out=bytearray()
    for bi,b in enumerate(boxes):
        lines=b.split('\n')
        assert len(lines)<=2,b
        for li,l in enumerate(lines):
            for c in l: out.append(ENC[c])
            if li!=len(lines)-1: out.append(0xFE)
        if bi!=len(boxes)-1: out.append(0xFB)
    out.append(0xFF); return bytes(out)
def boxes(key): return list(_J[key])
def ptr(r,key): return 0x08000000+r.alloc(enc_boxes(_J[key]),1)
def ptr_s(r,s): return 0x08000000+r.alloc(enc_boxes([s] if isinstance(s,str) else s),1)
def battle_ptr(r,s):
    """battle text: the last letter needs a trailing space"""
    return 0x08000000+r.alloc(enc_boxes([s])[:-1]+b' \xff',1)

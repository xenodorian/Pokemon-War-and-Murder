"""HYPERPUNCH (357) gets its own battle animation (usage: anim_hyperpunch.py IN.gba OUT.gba). Runs after anim_throw.py.
Built only from FireRed's own animation scripts (data/battle_anim_scripts.s): MEGA PUNCH (move 5: charged fist, white flash on the target, impact background, heavy shake)
followed by DYNAMIC PUNCH (move 223: second fist, target shake, five explosions on the target). Both bodies are copied command by command, so every sprite template,
task and sound pointer is the original one; the first body's closing 'end' is dropped so the two play back to back (each one clears its own mon background and blend).
Not Leaf-wrapped: it is a heavy punch for any user (the Leaf throw frames belong to the throw moves)."""
import sys,os,struct
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(1,'/home/claude/work/tools')
from inc import Rom
import anim_throw as AT
HYPERPUNCH,MEGA_PUNCH,DYNAMIC_PUNCH=357,5,223
def apply(r):
    b=r.b
    tk=struct.unpack_from('<I',b,0x1c68f4+4*33)[0]
    ANIM=None
    for o in range(0,0x400000,4):
        v=struct.unpack_from('<I',b,o)[0]-0x08000000
        if 0xA00000<=v<len(b)-4*358 and struct.unpack_from('<I',b,v+4*33)[0]==tk and struct.unpack_from('<I',b,v+4*356)[0]!=tk: ANIM=v; break
    assert ANIM,'anim table'
    assert struct.unpack_from('<I',b,ANIM+4*HYPERPUNCH)[0]==tk,'hyperpunch not on the tackle animation'
    def cmd_len(o):
        op=b[o]
        if op in (2,3): return 7+2*b[o+6]
        if op==0x1f: return 6+2*b[o+5]
        return AT.LEN[op]
    def body(move,drop_end):
        ptr=struct.unpack_from('<I',b,ANIM+4*move)[0]; o=ptr-0x08000000; out=b''
        # the opening 'call' of MEGA PUNCH (SetImpactBackground) keeps its absolute pointer
        while True:
            n=cmd_len(o)
            if b[o]==0x08: return out if drop_end else out+bytes(b[o:o+n])
            out+=bytes(b[o:o+n]); o+=n
    s=body(MEGA_PUNCH,True)+body(DYNAMIC_PUNCH,False)
    a=r.alloc(s,1)
    r.w32(ANIM+4*HYPERPUNCH,0x08000000+a)
    print('anim_hyperpunch: script',hex(a),len(s),'bytes; table',hex(ANIM))
if __name__=='__main__':
    r=Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')

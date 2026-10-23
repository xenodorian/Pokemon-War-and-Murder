"""Scene cast fixes (usage: scenes_fix.py IN.gba OUT.gba), run through tools/patch.sh after mason_pass2.py.
Review rule: whoever speaks in a scene must be on screen.
 1. Rival's house, Daisy (map 4,2): the TOWN MAP chain said 'MASON: DAISY has a TOWN MAP for you' but Mason is not in that room; Daisy is. It is Daisy's line now.
 2. YVELTAL has no overworld sprite and speaks before and after its battle: those lines become narration (a voice shakes the tower, it stays with you).
 3. The epilogue cards (FATHER at the step, Nero's fate) ran in the General's throne room with speakers who are not there; the epilogue now plays over a black screen.
Every text pointer is found by searching the ROM for the text bytes from story_text.json."""
import sys,struct,os,re
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from inc import Rom
from shinigami import SB,put_script
import story_text as ST
def refs_of(b,addr): return [m.start() for m in re.finditer(re.escape(struct.pack('<I',0x08000000+addr)),bytes(b[:0x1200000]))]
def repoint_text(r,key,boxes):
    old=ST.enc_boxes(ST.boxes(key)); a=bytes(r.b).find(old); assert a>0,key
    rf=refs_of(r.b,a); assert rf,key
    p=ST.ptr_s(r,boxes)
    for x in rf: r.w32(x,p)
    return len(rf)
def install(r):
    b=r.b
    # 1. Daisy hands over the map herself
    ref=0x168ef8; old=struct.unpack('<I',b[ref:ref+4])[0]; assert old>=0x09000000,hex(old)
    r.w32(ref,ST.ptr_s(r,["DAISY: Grandpa means well, but he\ncannot see the war coming.","DAISY: Here, a TOWN MAP. Use it to\nfind your way home, LEAF."]))
    # 2. YVELTAL as a voice
    n=repoint_text(r,'yveltal_rise',["The earth splits. YVELTAL rises.\nIts wings blot out the sky.","A voice shakes the tower:\nWho dares wake me? A child?","It attacks. No time to rest."])
    n+=repoint_text(r,'yveltal_tamed',["YVELTAL folds its black wings.\nIt bows its head to Leaf.","It will stay with her.\nA bond is made."])
    # 3. epilogue over black
    d=bytes(b[:0x1200000]); pat=re.compile(rb'\x04(.{4})\x16\xe6\x40\x06\x00',re.S); k=0
    for m in pat.finditer(d):
        epi=struct.unpack('<I',m.group(1))[0]
        if not 0x08f00000<=epi<0x0a000000: continue
        S=SB(); S.fadescreen(1); S.raw(0x04); S.ptr(epi); S.raw(0x03)
        w=0x08000000+put_script(r,S); b[m.start()+1:m.start()+5]=struct.pack('<I',w); k+=1
    assert k==1,k
    print('daisy fixed; yveltal texts',n,'refs; epilogue wrapped')
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))

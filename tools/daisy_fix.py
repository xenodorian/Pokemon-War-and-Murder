"""Daisy's old Outlaw lines (usage: daisy_fix.py IN.gba OUT.gba), run through tools/patch.sh after scenes_fix.py.
Daisy (Oak's granddaughter, Mason's sister, rival's house in Pallet Town, script 0x168d56) greeted LEAF as a slum kid ('hoodrat', 'go back to the gutter'), flirted, and said she
'needs to stop doing acid' after giving the map. None of that fits the story (LEAF is not a slum kid; Daisy is kind and worried about the war). Her grooming and map lines stay."""
import sys,struct,os
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from inc import Rom
import story_text as ST
# (location of the msgbox pointer, address of the old string, new boxes)
CH=[
 (0x168d9c,0x18d58c,["DAISY: Oh, LEAF! Grandpa told me\nyou are going to the war.","DAISY: Be careful out there.\nCome back safe."]),
 (0x168db1,0x18d5c4,["DAISY: LEAF, you look tired.\nRest here a moment."]),
 (0x168dd7,0x18d7d3,["DAISY: Hey, LEAF! You have been\nbrave. Let me help.","How about I groom one of your\nPOKeMON for you?"]),
 (0x168f5b,0x18d6af,["DAISY: Keep it safe. A map can\nsave your life out there."]),
 (0x168f65,0x18d763,["A map of KANTO lies on the table.\nIt looks well used."]),
]
def install(r):
    b=r.b
    for ref,old,boxes in CH:
        assert struct.unpack('<I',b[ref:ref+4])[0]==0x08000000+old,hex(ref)
        r.w32(ref,ST.ptr_s(r,boxes))
    print('daisy lines',len(CH))
if __name__=='__main__':
    r=Rom(sys.argv[1]); install(r); r.save(sys.argv[2]); print('end',hex(r.cur))

// Who dies on a white-out. VAR 0x8007 = 1 from leaf_down_standin means death in the white-out script.
// Owner rule: in a playable run, if the player is in the party as a playable POKeMON when everything faints, she dies (HEAVEN or HELL by reputation).
// If she is not in the party, the normal POKeMON CENTER respawn. "In the party" is species 255 (LEAF): a real LEAF that fainted (as before), or the
// stand-in (owner id 'STND') in a run with F_PLAYABLE (0x84A) set.
// The battle's end callback deletes the stand-in before the white-out script runs, so she is noted when the battle STARTS: prepare_note runs the old
// max_prepare (which adds her when the party is empty) and records "stand-in present in a playable run" in the script scratch word 0x800A.
// (Script variables in the save block cannot be used: the game moves the save block between the battle start and the white-out and the value was lost.)
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
#include "standin_gen.h"
#define GETMON ((u32(*)(void*,int,void*))(0x0803FBE8|1))
#define PARTY ((u8*)0x02024284)
#define PARTY_COUNT (*(volatile u8*)0x02024029)
#define SB1 (*(u8* volatile*)0x03005008)
#define GSV(n) (*(volatile u16*)(0x020370b8+2*((n)-0x8000)))
#define NOTE 0x5A5A
void prepare_note(void){
    u16 standin=(PARTY_COUNT==0);                       // the stand-in only joins when the party is completely empty (the old max_prepare adds her)
    ((void(*)(void))OLD_MAX_PREPARE)();
    if(!((SB1[0xEE0+(0x84A>>3)]>>(0x84A&7))&1)) standin=0;
    GSV(0x800A)=standin?NOTE:0;
}
void leaf_down_standin(void){
    u16 down=0;
    for(u32 i=0;i<PARTY_COUNT;i++){
        u8* m=PARTY+100*i;
        if(GETMON(m,11,0)!=255 || GETMON(m,1,0)==0x53544E44) continue;
        if(GETMON(m,0x39,0)==0) down=1;
    }
    if(GSV(0x800A)==NOTE){ down=1; GSV(0x800A)=0; }
    *(volatile u16*)0x020370C6=down;
}

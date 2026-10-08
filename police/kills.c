// Kill count check for the story police: kills = trainers the player shot (bits 512.. of the shoot record) and has not had forgiven at the church
// (a forgiven kill has its trainer flag cleared). Result in script var 0x8007.
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
#include "../stage2/data.h"
#define SB1 (*(u8* volatile*)0x03005008)
#define GSV(n) (*(volatile u16*)(0x020370b8+2*(n)))
#define KILL_LIMIT 10
static u16* varp(u32 bit){ return (u16*)(SB1+0x1000+((g_vars[bit>>4]-0x4000)<<1)); }
static int bit_get(u32 b){ return (*varp(b)>>(b&15))&1; }
static int flag_get(u32 f){ return (SB1[0xEE0+(f>>3)]>>(f&7))&1; }
void kill_check(void){
    u32 n=0;
    for(u32 r=0;r<NIDS;r++) if(bit_get(512+r)&&flag_get(0x500+g_ids[r])) n++;
    GSV(7)=(n>=KILL_LIMIT)?1:0;
}

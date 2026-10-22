// death_fx with the trainer class read live. The class saved by max_prepare_wrap came out 0 for trainer battles (gBattleTypeFlags is not set yet
// when the battle-start hook runs), so a JRA soldier's kill showed "mauled by a pokemon" and played the cry instead of the gunshot.
// At death time gBattleTypeFlags (bit 3 = trainer battle) and gTrainerBattleOpponent_A still hold the fight that just ended.
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
#define GSV(n) (*(volatile u16*)(0x020370b8+2*(n)))
#define DF_BTYPE (*(volatile u32*)0x02022B4C)
#define DF_OPP (*(volatile u16*)0x020386ae)
#define DF_ENEMY_SPECIES (*(volatile u16*)(0x02023BE4+0x58))
#define DF_TRAINERS 0x08798790
#define DF_PlaySE ((void(*)(u16))(0x080722cc|1))
#define DF_PlayCry ((void(*)(u16,signed char))(0x08071df0|1))
#define DF_FadeCol ((u32(*)(u32,signed char,u8,u8,u16))(0x08070588|1))
void death_fx_live(void){
    u8 cls=(DF_BTYPE&8)?*(const u8*)(DF_TRAINERS+40*(u32)DF_OPP+1):0;
    u8 mauled=(cls==44 || cls==45 || cls==48)?0:1;
    GSV(12)=mauled;
    if(mauled) DF_PlayCry(DF_ENEMY_SPECIES,0);
    else DF_PlaySE(347);                                  // SE_SHOT
    DF_FadeCol(0xFFFFFFFFu,0,0,16,0x001F);
}

// Native routines added on top of the owner's personal ROM (CRC32 0x2f906b52). One module, one table (REBASE01), installed by tools/rebase_natives.py.
//  - max_prepare_wrap: runs before every battle. Saves the class of the trainer fighting (0 for a wild POKeMON) in VAR 0x40F8, then calls the old max_prepare.
//  - death_fx: what plays when a permanent LEAF dies. A JRA soldier (class 48), captain (44) or general (45) gives a gunshot, anything else the attacker's cry. The screen fades to red.
//  - shackle_check / shackle_do / shoot_captain: SHACKLE on a defeated captain, and +10 liberty when a captain is shot.
//  - partner_choose_move_fix: the AI partner always aims at a foe unless the move targets the user.
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
#include "rebase_gen.h"
#define SB1 (*(u8* volatile*)0x03005008)
#define GSV(n) (*(volatile u16*)(0x020370b8+2*(n)))
static u16* var(u32 v){ return (u16*)(SB1+0x1000+((v-0x4000)<<1)); }
#define DF_BTYPE (*(volatile u32*)0x02022B4C)             // gBattleTypeFlags
#define DF_OPP (*(volatile u16*)0x020386ae)               // gTrainerBattleOpponent_A
#define DF_ENEMY_SPECIES (*(volatile u16*)(0x02023BE4+0x58))
#define DF_TRAINERS 0x08798790                            // trainer table, 40 bytes each, class at +1
#define DF_PlaySE ((void(*)(u16))(0x080722cc|1))
#define DF_PlayCry ((void(*)(u16,signed char))(0x08071df0|1))
#define DF_FadeCol ((u32(*)(u32,signed char,u8,u8,u16))(0x08070588|1))
#define VAR_DEATHCLS 0x40F8

void max_prepare_wrap(void){
    *var(VAR_DEATHCLS)=(DF_BTYPE&8)?*(const u8*)(DF_TRAINERS+40*(u32)DF_OPP+1):0;
    ((void(*)(void))OLD_MAX_PREPARE)();
}
void death_fx(void){
    u8 cls=(u8)*var(VAR_DEATHCLS);
    u8 mauled=(cls==44 || cls==45 || cls==48)?0:1;
    GSV(12)=mauled;                                       // read by the death script: 1 = print the mauled line
    if(mauled) DF_PlayCry(DF_ENEMY_SPECIES,0);
    else DF_PlaySE(347);                                  // SE_SHOT
    DF_FadeCol(0xFFFFFFFFu,0,0,16,0x001F);                // screen to red
}

// ---- SHACKLE. Captain trainers (class 44, by trainer id). The captain's last party member is the one captured.
static const u16 captain_ids[]={15,6,442,86,460,176,284,399,24,433};
#define SH_GiveMon ((u8(*)(u16,u8,u16,u32,u32,u8))(0x080a011c|1))     // ScriptGiveMon
#define SH_ShootDo ((void(*)(void))(0x08a09b61|1))                     // the base shoot native the shoot script calls
#define SH_RESULT (*(volatile u16*)0x020370d0)                         // VAR_RESULT (0x800D)
#define SH_FLAG_BASE 0x871                                             // one flag per captain, 0x871 to 0x87A
static int shackle_index(void){
    u16 id=DF_OPP;
    for(u32 i=0;i<sizeof captain_ids/sizeof captain_ids[0];i++) if(captain_ids[i]==id) return (int)i;
    return -1;
}
static int shackle_flag_get(u32 f){ return (*(volatile u8*)(*(u8* volatile*)0x03005008+0xEE0+(f>>3))>>(f&7))&1; }
static void shackle_flag_set(u32 f){ volatile u8* p=(volatile u8*)(*(u8* volatile*)0x03005008+0xEE0+(f>>3)); *p|=(u8)(1<<(f&7)); }
static void shackle_liberty(int d){
    volatile u16* lib=(volatile u16*)(*(u8* volatile*)0x03005008+0x1000+((0x40ac-0x4000)<<1));
    *lib=(u16)(*lib+d);
}
void shackle_check(void){
    int i=shackle_index();
    GSV(12)=(i>=0 && !shackle_flag_get(SH_FLAG_BASE+(u32)i))?1:0;
}
void shackle_do(void){
    const u8* t=(const u8*)(DF_TRAINERS+40*(u32)DF_OPP);
    u32 n=t[32];
    const u8* last=(const u8*)(*(const u32*)(t+36))+8*(n-1);
    SH_RESULT=SH_GiveMon(*(const u16*)(last+4),last[2],0,0,0,0);
    shackle_flag_set(SH_FLAG_BASE+(u32)shackle_index());
    shackle_liberty(5);
}
void shoot_captain(void){
    SH_ShootDo();
    if(shackle_index()>=0) shackle_liberty(10);
}

// ---- AI partner (MAX's PIKACHU / RAICHU): replaces partner_choose_move in sPlayerBufferCommands entry 20.
#define VAR_PARTNER 0x4092
#define gActiveBattler (*(volatile u8*)0x02023bc4)
#define gBattlerTarget (*(volatile u8*)0x02023d6c)
#define gAbsentBattlerFlags (*(volatile u8*)0x02023d70)
#define gBattleControllerExecFlags (*(volatile u32*)0x02023bc8)
#define gBattlerControllerFuncs ((u32*)0x03004fe0)
#define gBitTable ((u32*)0x0825e45c)
#define gBattleBufferA ((u8*)0x02022bc4)
#define gBattleMoves ((u8*)0x08250c04)                     // the original move table; the partner only uses original moves
#define BattleAI_SetupAIData ((void(*)(void))(0x080c6da0|1))
#define BattleAI_ChooseMoveOrAction ((u8(*)(void))(0x080c6f44|1))
#define GetBattlerAtPosition ((u8(*)(u8))(0x080751e8|1))
#define EmitTwoReturnValues ((void(*)(u8,u8,u16))(0x0800e848|1))
#define PlayerBufferRunCommand (0x0802e3b4|1)
#define ORIG_CHOOSEMOVE ((void(*)(void))(0x08032c90|1))
static void exec_done(void){
    gBattlerControllerFuncs[gActiveBattler]=PlayerBufferRunCommand;
    gBattleControllerExecFlags&=~gBitTable[gActiveBattler];
}
void partner_choose_move_fix(void){
    if(!(gActiveBattler==2 && *var(VAR_PARTNER)==1)){ ORIG_CHOOSEMOVE(); return; }
    u16* moves=(u16*)(gBattleBufferA+0x200*gActiveBattler+4);
    BattleAI_SetupAIData();
    u8 chosen=BattleAI_ChooseMoveOrAction();
    if(chosen>3) chosen=0;
    u8 tgt=gBattleMoves[12*moves[chosen]+6];
    // the target is set every time, so a stale battler (the player or the partner itself) is never kept
    gBattlerTarget=GetBattlerAtPosition(1);                              // B_POSITION_OPPONENT_LEFT
    if(gAbsentBattlerFlags&gBitTable[gBattlerTarget]) gBattlerTarget=GetBattlerAtPosition(3);
    if(tgt&(2|16)) gBattlerTarget=gActiveBattler;                        // user, or user or selected
    EmitTwoReturnValues(1,10,chosen|(gBattlerTarget<<8));               // 10 = B_ACTION_EXEC_SCRIPT
    exec_done();
}

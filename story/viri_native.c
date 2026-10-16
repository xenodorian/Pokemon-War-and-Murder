// Native routines of the Viridian arrest scene: MAX's PIKACHU joins the party for the double battle and acts on its own, then leaves.
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
#define PARTY ((u8*)0x02024284)
#define COUNT (*(volatile u8*)0x02024029)
#define OUTCOME (*(volatile u8*)0x02023e8a)
#define RESULT (*(volatile u16*)0x020370d0)
#define SB1 (*(u8* volatile*)0x03005008)
#define GetMonData ((u32(*)(void*,int,void*))(0x0803FBE8|1))
#define ZeroMonData ((void(*)(void*))(0x0803D994|1))
#define CreateMon ((void(*)(void*,u16,u8,u8,u8,u32,u8,u32))(0x0803DA54|1))
#define MAXOT 0x4D415821u
#define VAR_PSPECIES 0x4093
#define VAR_PLEVEL 0x4094
#define VAR_PARTNER 0x4092          // 1 while MAX's PIKACHU fights as the AI partner (battler 2)
static u16* var(u32 v){ return (u16*)(SB1+0x1000+((v-0x4000)<<1)); }
static void drop(int i){
    int n=COUNT;
    for(int k=i;k<n-1;k++){ u32* d=(u32*)(PARTY+100*k); u32* s=(u32*)(PARTY+100*(k+1)); for(int w=0;w<25;w++) d[w]=s[w]; }
    ZeroMonData(PARTY+100*(n-1)); COUNT=(u8)(n-1);
}
// MAX's PIKACHU (Lv 10, marked by the preset trainer id MAX!) goes into party slot 1 (so it is the second player-side battler) and
// the partner AI drives it. Needs a lead POKeMON and a free slot, otherwise the fight is LEAF's alone.
void viri_prepare(void){
    int n=COUNT;
    for(int i=0;i<n;i++) if(GetMonData(PARTY+100*i,1,0)==MAXOT) return;
    *var(VAR_PARTNER)=0;
    if(n<1||n>=6) return;
    for(int k=n;k>1;k--){ u32* d=(u32*)(PARTY+100*k); u32* s=(u32*)(PARTY+100*(k-1)); for(int w=0;w<25;w++) d[w]=s[w]; }
    u16 sp=*var(VAR_PSPECIES), lv=*var(VAR_PLEVEL);      // later fights (story_ambush.py) set these: MAX's RAICHU instead of PIKACHU
    if(!sp){ sp=25; lv=10; }
    CreateMon(PARTY+100,sp,(u8)lv,32,0,0,1,MAXOT); COUNT=(u8)(n+1);
    *var(VAR_PARTNER)=1;
}
// after the fight: PIKACHU leaves, RESULT = 1 when the player's side lost (outcome is not "won")
void viri_cleanup(void){
    for(int i=0;i<COUNT;i++) if(GetMonData(PARTY+100*i,1,0)==MAXOT){ drop(i); break; }
    *var(VAR_PARTNER)=0; *var(VAR_PSPECIES)=0; *var(VAR_PLEVEL)=0;
    RESULT=(OUTCOME==1)?0:1;
}
// ---- partner AI: ported from pokeemerald src/battle_controller_player_partner.c (PlayerPartnerHandleChooseAction / ChooseMove)
// onto FireRed's player controller (battler 2 keeps the player controller; only these two command handlers are replaced).
#define gActiveBattler (*(volatile u8*)0x02023bc4)
#define gBattlerTarget (*(volatile u8*)0x02023d6c)
#define gAbsentBattlerFlags (*(volatile u8*)0x02023d70)
#define gBattleControllerExecFlags (*(volatile u32*)0x02023bc8)
#define gBattlerControllerFuncs ((u32*)0x03004fe0)
#define gBitTable ((u32*)0x0825e45c)
#define gBattleBufferA ((u8*)0x02022bc4)
#define gBattleMoves ((u8*)0x08250c04)
#define BattleAI_SetupAIData ((void(*)(void))(0x080c6da0|1))
#define BattleAI_ChooseMoveOrAction ((u8(*)(void))(0x080c6f44|1))
#define GetBattlerAtPosition ((u8(*)(u8))(0x080751e8|1))
#define EmitTwoReturnValues ((void(*)(u8,u8,u16))(0x0800e848|1))
#define PlayerBufferRunCommand (0x0802e3b4|1)
#define ORIG_CHOOSEACTION ((void(*)(void))(0x08032bd4|1))
#define ORIG_CHOOSEMOVE ((void(*)(void))(0x08032c90|1))
static int partner(void){ return gActiveBattler==2 && *var(VAR_PARTNER)==1; }
static void exec_done(void){
    gBattlerControllerFuncs[gActiveBattler]=PlayerBufferRunCommand;
    gBattleControllerExecFlags&=~gBitTable[gActiveBattler];
}
// Emerald runs AI_TrySwitchOrUseItem here, which also emits "use a move". It is skipped on purpose: it may switch PIKACHU for a mon of the player's own
// party, because FireRed has no separate partner party. Plain "use a move" is what that function emits when it does not switch.
void partner_choose_action(void){
    if(!partner()){ ORIG_CHOOSEACTION(); return; }
    EmitTwoReturnValues(1,0,0);
    exec_done();
}
void partner_choose_move(void){
    if(!partner()){ ORIG_CHOOSEMOVE(); return; }
    u16* moves=(u16*)(gBattleBufferA+0x200*gActiveBattler+4);
    BattleAI_SetupAIData();
    u8 chosen=BattleAI_ChooseMoveOrAction();
    if(chosen>3) chosen=0;
    u8 tgt=gBattleMoves[12*moves[chosen]+6];
    if(tgt&(2|16)) gBattlerTarget=gActiveBattler;                      // user, or user or selected
    if(tgt&8){                                                          // both foes
        gBattlerTarget=GetBattlerAtPosition(1);                          // B_POSITION_OPPONENT_LEFT
        if(gAbsentBattlerFlags&gBitTable[gBattlerTarget]) gBattlerTarget=GetBattlerAtPosition(3);
    }
    EmitTwoReturnValues(1,10,chosen|(gBattlerTarget<<8));               // 10 = B_ACTION_EXEC_SCRIPT
    exec_done();
}

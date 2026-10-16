// Native routines of the Shinigami storyline: reputation, shop price scaling and refusal, LEAF fights as herself.
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
#include "../stage2/data.h"
#include "../leg2/killcount.h"
#include "story_gen.h"
#define SB1 (*(u8* volatile*)0x03005008)
#define PARTY ((u8*)0x02024284)
#define COUNT (*(volatile u8*)0x02024029)
#define VAR_REP 0x40E7
#define VAR_REPADJ 0x40E9
#define BLESS_VAR 0x40F4
#define SP_MAX 255
#define STNDOT 0x53544E44u      // OT id marking the stand-in LEAF (empty party only); a real LEAF has the player's OT id
#define VAR_BSTART 0x4091       // 1 = the battle started with a full party containing the real LEAF
#define OUTCOME (*(volatile u8*)0x02023e8a)
#define ENEMY ((u8*)0x0202402c)
#define STORAGE (*(u8* volatile*)0x03005010)
#define SetupScript ((void(*)(const u8*))(0x08069ae4|1))
#define CopyMon ((void(*)(void*,void*,u32))(0x08040b08|1))
#define CB2_CONTINUE (0x080568c4|1)
#define GetMonData ((u32(*)(void*,int,void*))(0x0803FBE8|1))
#define ZeroMonData ((void(*)(void*))(0x0803D994|1))
#define SetMonData ((void(*)(void*,u32,const void*))(0x0804037c|1))
#define GSV(n) (*(volatile u16*)(0x020370b8+2*(n)))
#define CreateMon ((void(*)(void*,u16,u8,u8,u8,u32,u8,u32))(0x0803DA54|1))
static u16* var(u32 v){ return (u16*)(SB1+0x1000+((v-0x4000)<<1)); }
// reputation 0..200, 100 = neutral: 100 + blessings - kills + story adjustments (VAR_REPADJ is stored as 1000 + adjustment). Result is also written to VAR_REP.
u32 rep_calc(void){
    int r=100+(int)*var(BLESS_VAR)-(int)kc_total();
    int adj=(int)*var(VAR_REPADJ); if(adj>=500) r+=adj-1000;
    if(r<0) r=0; if(r>200) r=200;
    *var(VAR_REP)=(u16)r; return (u32)r;
}
// shop price: +1% per point below 100, -1% per point above 100 (at least 1)
u32 scale_price(u32 price){
    u32 r=rep_calc(); u32 pct=(r<100)?(100+(100-r)):(100-(r-100));
    if(pct==0) pct=1;
    u32 p=(price*pct*655)>>16; if(price&&p==0) p=1; return p;
}
typedef struct { u8 pad[8]; u8* scriptPtr; } Ctx;
u8 shop_cmd(Ctx* ctx){
    if(rep_calc()==0){ ctx->scriptPtr=(u8*)REFUSE_SCRIPT; return 0; }
    return ((u8(*)(Ctx*))ORIG_POKEMART)(ctx);
}
static void drop(int i){
    int n=COUNT;
    for(int k=i;k<n-1;k++){ u32* d=(u32*)(PARTY+100*k); u32* s=(u32*)(PARTY+100*(k+1)); for(int w=0;w<25;w++) d[w]=s[w]; }
    ZeroMonData(PARTY+100*(n-1)); COUNT=(u8)(n-1);
}
static int is_leaf_perm(int i){ return GetMonData(PARTY+100*i,11,0)==SP_MAX && GetMonData(PARTY+100*i,1,0)!=STNDOT; }
// removes the stand-in LEAF (the stand-in for a trainer with no POKeMON at all) from the party; the real LEAF stays
void max_remove(void){
    for(int i=0;i<COUNT;i++) if(GetMonData(PARTY+100*i,11,0)==SP_MAX && GetMonData(PARTY+100*i,1,0)==STNDOT){ drop(i); return; }
}
// LEAF becomes a real party member (Lv 5, her own OT id) the moment she gets her first POKeMON
void leaf_join(void){
    int n=COUNT; if(n>=6) return;
    for(int i=0;i<n;i++) if(is_leaf_perm(i)) return;
    CreateMon(PARTY+100*n,SP_MAX,5,32,0,0,0,0); COUNT=(u8)(n+1);
}
static int box_empty(u32* b){ for(int w=0;w<20;w++) if(b[w]) return 0; return 1; }
// after a catch with a full party the game already sent the new POKeMON to the PC: swap it with LEAF (LEAF takes its PC slot)
void leaf_swap(void){
    int li=-1; for(int i=0;i<COUNT;i++) if(is_leaf_perm(i)) li=i;
    if(li<0) return;
    u32* e=(u32*)ENEMY; u8* base=STORAGE+4;
    for(int k=0;k<14*30;k++){
        u32* s=(u32*)(base+80*k);
        if(s[0]==e[0] && s[1]==e[1] && (e[0]|e[1])){
            u32* l=(u32*)(PARTY+100*li); for(int w=0;w<20;w++) s[w]=l[w];
            CopyMon(PARTY+100*li,ENEMY,100); return;
        }
    }
}
// GSV4 = species of the caught POKeMON (for the prompt text)
void leaf_prompt_prep(void){ GSV(4)=(u16)GetMonData(ENEMY,11,0); }
#define GMAIN 0x030030F0
#define SAVEDCB (*(volatile u32*)(GMAIN+8))
#define SetMainCallback2 ((void(*)(u32))(0x08000544|1))
#define VAR_CBLO 0x40EB
#define VAR_CBHI 0x40F1
// the battle's end callback is wrapped: the first frame back in the overworld removes LEAF again, then the real callback runs
void max_after(void){
    u32 cb=(u32)*var(VAR_CBLO)|((u32)*var(VAR_CBHI)<<16);
    max_remove();
    SAVEDCB=cb;
    if(*var(VAR_BSTART)==1 && OUTCOME==7){      // caught with a full party that holds LEAF: ask PC or withdraw
        *var(VAR_BSTART)=0; leaf_prompt_prep();
        SetupScript((const u8*)PROMPT_SCRIPT); SetMainCallback2(CB2_CONTINUE); return;
    }
    SetMainCallback2(cb);
}
// before every battle: only when the party is completely empty LEAF (Lv 1, 1 HP, TACKLE) joins as a stand-in, for the length of that battle
void max_prepare(void){
    max_remove();
    int n=COUNT, perm=0; for(int i=0;i<n;i++) if(is_leaf_perm(i)) perm=1;
    *var(VAR_BSTART)=(n>=6&&perm)?1:0;
    if(n==0){
        CreateMon(PARTY,SP_MAX,1,32,0,0,1,STNDOT); COUNT=1;
        u16 one=1; SetMonData(PARTY,0x3a,&one); SetMonData(PARTY,0x39,&one);      // max HP 1, HP 1: one hit and she is down
    }
    u32 cb=SAVEDCB; u32 mine=((u32)max_after)|1;
    if(cb!=mine && cb!=0){ *var(VAR_CBLO)=(u16)cb; *var(VAR_CBHI)=(u16)(cb>>16); SAVEDCB=mine; }
}
// GSV7 = 1 when the party is empty (used by the white-out script: LEAF was the one who fell)
void party_empty(void){ GSV(7)=(COUNT==0)?1:0; }

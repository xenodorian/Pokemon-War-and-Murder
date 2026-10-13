// Native routines of the Shinigami storyline: reputation, shop price scaling and refusal, MAX fights as herself.
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
#include "../stage2/data.h"
#include "../leg2/killcount.h"
#include "story_gen.h"
#define SB1 (*(u8* volatile*)0x03005008)
#define PARTY ((u8*)0x02024284)
#define COUNT (*(volatile u8*)0x02024029)
#define VAR_REP 0x40ED
#define VAR_REPADJ 0x40E9
#define BLESS_VAR 0x40F4
#define SP_MAX 255
#define GetMonData ((u32(*)(void*,int,void*))(0x0803FBE8|1))
#define ZeroMonData ((void(*)(void*))(0x0803D994|1))
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
static int usable(u8* m){ u32 sp=GetMonData(m,11,0); if(!sp||sp==412) return 0; return *(u16*)(m+0x56)>0; }
static void drop(int i){
    int n=COUNT;
    for(int k=i;k<n-1;k++){ u32* d=(u32*)(PARTY+100*k); u32* s=(u32*)(PARTY+100*(k+1)); for(int w=0;w<25;w++) d[w]=s[w]; }
    ZeroMonData(PARTY+100*(n-1)); COUNT=(u8)(n-1);
}
// removes MAX (the stand-in for a trainer with nothing to fight with) from the party
void max_remove(void){
    for(int i=0;i<COUNT;i++) if(GetMonData(PARTY+100*i,11,0)==SP_MAX){ drop(i); return; }
}
// before every battle: with no usable POKeMON in the party MAX (Lv 1, Caterpie stats, TACKLE) joins; once a usable one exists again she leaves
void max_prepare(void){
    int n=COUNT, ok=0, mx=-1;
    for(int i=0;i<n;i++){ u8* m=PARTY+100*i; if(GetMonData(m,11,0)==SP_MAX) mx=i; else if(usable(m)) ok++; }
    if(ok){ if(mx>=0) drop(mx); return; }
    if(mx>=0) return;
    if(n<6){ CreateMon(PARTY+100*n,SP_MAX,1,32,0,0,1,0); COUNT=(u8)(n+1); }
}

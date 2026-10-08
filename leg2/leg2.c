// Leg 2 native routines: kill count / bless count / karma, blessing a trainer.
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
#include "../stage2/data.h"
#include "leg2_data.h"
#include "killcount.h"
#define SB1 (*(u8* volatile*)0x03005008)
#define GSV(n) (*(volatile u16*)(0x020370b8+2*(n)))
#define OPP (*(volatile u16*)0x020386ae)
#define STRBUF ((u8*)0x02021cd0)
#define BLESS_VAR 0x40F4
static u16* varp(u32 bit){ return (u16*)(SB1+0x1000+((g_vars[bit>>4]-0x4000)<<1)); }
static int bit_get(u32 b){ return (*varp(b)>>(b&15))&1; }
static void bit_set(u32 b){ *varp(b) |= (u16)(1<<(b&15)); }
static int flag_get(u32 f){ return (SB1[0xEE0+(f>>3)]>>(f&7))&1; }
static u16* bless_p(void){ return (u16*)(SB1+0x1000+((BLESS_VAR-0x4000)<<1)); }
static int rank_of(u32 id){ for(int i=0;i<NIDS;i++) if(g_ids[i]==id) return i; return -1; }
static u32 kills(void){ return kc_total(); }
static u8* put_str(u8* o,const u8* s){ while(*s!=0xFF) *o++=*s++; return o; }
static u8* put_num(u8* o,u32 v){
    static const u32 pw[5]={10000,1000,100,10,1};
    int started=0;
    for(int i=0;i<5;i++){ u32 d=0; while(v>=pw[i]){v-=pw[i];d++;} if(d||started||i==4){ *o++=(u8)(0xA1+d); started=1; } }
    return o;
}
// GSV7: 0 = karma zero, 1 = negative, 2 = positive
void karma_check(void){
    int k=(int)*bless_p()-(int)kills();
    GSV(7)=(k<0)?1:(k>0?2:0);
}
// builds the three-line status text at gStringVar1 (read by a RAM message pointer)
void kc_show(void){
    u32 n=kills(); u32 b=*bless_p(); int k=(int)b-(int)n;
    u8* o=STRBUF;
    o=put_str(o,T_KILLS); o=put_num(o,n); *o++=0xFE;
    o=put_str(o,T_BLESS); o=put_num(o,b); *o++=0xFB;
    o=put_str(o,T_KARMA);
    if(k<0){ *o++=SIGN0; if(SIGN1) *o++=SIGN1; k=-k; }
    o=put_num(o,(u32)k); *o++=0x00; *o=0xFF;
}
// blessing the trainer just fought: Bless Count +1, trainer marked as done (robbed bit), random consumable into 0x8000/0x8001
void bless_do(void){
    u32 id=OPP; int r=rank_of(id);
    if(r>=0) bit_set(r);
    u16* p=bless_p(); if(*p<999) (*p)++;
    u32 rnd=((u32(*)(void))(0x08044ec8|1))();
    GSV(0)=ITEM_POOL[(rnd*NPOOL)>>16]; GSV(1)=1;
}

// ---- police (generated officers): defeated officer talk script helpers
#define POL0 55
#define NPOL 24
#define LASTTALKED (*(volatile u16*)0x020370d2)
static u8* tmpl_for(u8 lid){
    u8 n=((u8*)*(u32*)(0x02036dfc+4))[0]; u8* t=KC_SB1+0x8E0;
    for(int i=0;i<n&&i<64;i++,t+=0x18) if(t[0]==lid) return t;
    return 0;
}
static void kill_tmpl(u8* t){ t[1]=GFX_SPLAT; *(u16*)(t+0xc)=0; *(u32*)(t+0x10)=SPLAT_SCRIPT; t[9]=0; *(u16*)(t+0x14)=0; }
// GSV7 = 1 when the last trainer fought is a living officer
void police_info(void){
    u32 id=OPP; GSV(7)=0;
    if(id>=POL0&&id<POL0+NPOL){ u8* t=tmpl_for((u8)LASTTALKED); if(t&&t[1]!=GFX_SPLAT) GSV(7)=1; }
}
// shooting an officer: Kill Count +1 (counter), the officer becomes a splatter
void police_shoot(void){
    u8* t=tmpl_for((u8)LASTTALKED); if(t) kill_tmpl(t);
    u16* p=kc_var(KC_POL_KILLS); if(*p<KC_MAX) (*p)++;
}

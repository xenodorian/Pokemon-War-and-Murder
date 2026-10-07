// Stage 2 native routines (thumb, freestanding). Linked at a fixed ROM address by build.py.
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
#include "data.h"   // g_ids[], g_shoot[], g_vars[], NIDS, SPLAT_SCRIPT, GFX_SPLAT
#define SB1 (*(u8* volatile*)0x03005008)
#define GSV(n) (*(volatile u16*)(0x020370b8+2*(n)))      /* script special vars 0x8000..0x800B */
#define LASTTALKED (*(volatile u16*)0x020370d2)          /* VAR_LAST_TALKED (0x800F) */
#define OPP (*(volatile u16*)0x020386ae)                  /* gTrainerBattleOpponent_A */
#define EVENTS (*(u8* volatile*)(0x02036dfc+4))           /* gMapHeader.events */
#define STRVAR1 ((u8*)0x02021cd0)
typedef void (*fn_create)(void*,u16,u8,u8,u8,u32,u8,u32);
#define CreateMon      ((fn_create)(0x0803da54|1))
#define GiveMonToPlayer ((u8(*)(void*))(0x08040b14|1))
#define SetMonData     ((void(*)(void*,u32,const void*))(0x0804037c|1))
#define SpeciesToNat   ((u16(*)(u16))(0x08043298|1))
#define SetDexFlag     ((u32(*)(u16,u8))(0x08088e74|1))
#define AddMoney       ((void(*)(u32*,u32))(0x0809fda0|1))
#define TRAINERS 0x08798790

static int rank_of(u32 id){ for(int i=0;i<NIDS;i++) if(g_ids[i]==id) return i; return -1; }
static u16* varp(u32 bit){ return (u16*)(SB1+0x1000+((g_vars[bit>>4]-0x4000)<<1)); }
static int bit_get(u32 b){ return (*varp(b)>>(b&15))&1; }
static void bit_set(u32 b){ *varp(b) |= (u16)(1<<(b&15)); }

static u8* tmpl_for(u8 lid){
    u8 n=EVENTS[0]; u8* t=SB1+0x8E0;
    for(int i=0;i<n&&i<64;i++,t+=0x18) if(t[0]==lid) return t;
    return 0;
}
static int tmpl_trainer(u8* t){
    u32 s=*(u32*)(t+0x10);
    if(s<0x08000000||s>=0x0A000000) return -1;
    u8* p=(u8*)s;
    if(p[0]!=0x5c||p[1]!=0) return -1;
    return p[2]|(p[3]<<8);
}
static void kill_tmpl(u8* t){
    t[1]=GFX_SPLAT; *(u16*)(t+0xc)=0; *(u32*)(t+0x10)=SPLAT_SCRIPT; t[9]=0; *(u16*)(t+0x14)=0;
}
// called after the map's object templates are (re)loaded: shot trainers become splatters again
void apply_killed(void){
    u8 n=EVENTS[0]; u8* t=SB1+0x8E0;
    for(int i=0;i<n&&i<64;i++,t+=0x18){
        if(t[1]==GFX_SPLAT){ *(u32*)(t+0x10)=SPLAT_SCRIPT; continue; }
        if(*(u16*)(t+0xc)==0) continue;
        int id=tmpl_trainer(t); if(id<0) continue;
        int r=rank_of(id); if(r<0||!g_shoot[r]) continue;
        if(bit_get(512+r)) kill_tmpl(t);
    }
}
void wrap_load(void){ ((void(*)(void))(0x08054f68|1))(); apply_killed(); }
void wrap_scripts(void){ ((void(*)(void))(0x080550a8|1))(); apply_killed(); }

// GSV4 = already robbed, GSV5 = can be shot, GSV6 = trainer known
void rob_info(void){
    GSV(4)=0; GSV(5)=0; GSV(6)=0;
    u32 id=OPP; int r=rank_of(id);
#ifdef PROBE
    *(u16*)(SB1+0x1000+(0x40E5-0x4000)*2)=0x8000|(r<0?0x4000:0)|id; *(u16*)(SB1+0x1000+(0x40E4-0x4000)*2)=LASTTALKED;
#endif
    if(r<0) return;
    GSV(6)=1; GSV(4)=bit_get(r);
    u8* t=tmpl_for((u8)LASTTALKED);
    if(t&&g_shoot[r]&&tmpl_trainer(t)==(int)id&&!bit_get(512+r)) GSV(5)=1;
}
void rob_pay(void){
    u32 id=OPP; int r=rank_of(id); if(r<0) return;
    bit_set(r);
    u8* tr=(u8*)(TRAINERS+40*id);
    u8 n=tr[32]; u8* party=*(u8**)(tr+36);
    u32 sz=(tr[0]&1)?16:8;
    u32 lvl=party[sz*(n-1)+2], val=5, cls=tr[1];
    for(const u8* m=(const u8*)0x0824f220;m[0]!=0xFF;m+=4) if(m[0]==cls){ val=m[1]; break; }
    u32 amt=lvl*4*val;
    AddMoney((u32*)(SB1+0x290),amt);
    static const u32 pw[6]={100000,10000,1000,100,10,1};
    u8* o=STRVAR1; int started=0;
    for(int i=0;i<6;i++){ u32 d=0; while(amt>=pw[i]){amt-=pw[i];d++;} if(d||started||i==5){ *o++=(u8)(0xA1+d); started=1; } }
    *o=0xFF;
}
void shoot_do(void){
    u32 id=OPP; int r=rank_of(id); if(r<0) return;
    bit_set(512+r);
    GSV(7)=0;
    { u8 n=EVENTS[0]; u8* q=SB1+0x8E0;                      /* double-battle partners share one trainer id: both die */
      for(int i=0;i<n&&i<64;i++,q+=0x18){
        if(*(u16*)(q+0xc)==0||q[1]==GFX_SPLAT) continue;
        if(tmpl_trainer(q)==(int)id){ if(q[0]!=(u8)LASTTALKED) GSV(7)=q[0]; kill_tmpl(q); } } }
    u8* t=tmpl_for((u8)LASTTALKED); if(t) kill_tmpl(t);
    u8* tr=(u8*)(TRAINERS+40*id);
    u8 pf=tr[0], n=tr[32]; u8* party=*(u8**)(tr+36);
    u32 sz=(pf&1)?16:8;
    for(int i=0;i<n;i++){
        u8* e=party+sz*i;
        u32 iv=e[0]|(e[1]<<8); u8 lvl=e[2]; u16 sp=e[4]|(e[5]<<8);
        u32 mon[25];
        CreateMon(mon,sp,lvl,(u8)((iv*31*257)>>16),0,0,0,0);
        if(pf&2){ u16 it=e[6]|(e[7]<<8); SetMonData(mon,12,&it); }
        if(pf&1){
            u8* mv=e+((pf&2)?8:6);
            for(int k=0;k<4;k++){
                u16 m=mv[2*k]|(mv[2*k+1]<<8);
                if(m){ u8 pp=((u8*)0x08250c04)[12*m+4]; SetMonData(mon,13+k,&m); SetMonData(mon,17+k,&pp); }
            }
        }
        u8 res=GiveMonToPlayer(mon);
        if(res<=1){ u16 dn=SpeciesToNat(sp); SetDexFlag(dn,2); SetDexFlag(dn,3); }
    }
}

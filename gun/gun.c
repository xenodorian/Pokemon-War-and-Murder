// Natives for the JRA soldier options (bless / threaten / shoot). Linked at a fixed ROM address by tools/gun.py.
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
#include "../stage2/data.h"        // g_vars[], SPLAT_SCRIPT, GFX_SPLAT
#include "../leg2/killcount.h"     // kc_var, KC_POL_KILLS, KC_MAX
#include "gun_data.h"              // J_IDS[], NJ, ROB_WRAP_LOAD, ROB_WRAP_SCRIPTS
#define SB1 (*(u8* volatile*)0x03005008)
#define GSV(n) (*(volatile u16*)(0x020370b8+2*(n)))
#define LASTTALKED (*(volatile u16*)0x020370d2)
#define OPP (*(volatile u16*)0x020386ae)
#define EVENTS (*(u8* volatile*)(0x02036dfc+4))
#define STRVAR1 ((u8*)0x02021cd0)
typedef void (*fn_create)(void*,u16,u8,u8,u8,u32,u8,u32);
#define CreateMon      ((fn_create)(0x0803da54|1))
#define GiveMonToPlayer ((u8(*)(void*))(0x08040b14|1))
#define SetMonData     ((void(*)(void*,u32,const void*))(0x0804037c|1))
#define SpeciesToNat   ((u16(*)(u16))(0x08043298|1))
#define SetDexFlag     ((u32(*)(u16,u8))(0x08088e74|1))
#define AddMoney       ((void(*)(u32*,u32))(0x0809fda0|1))
#define TRAINERS 0x08798790
#define JB 417                      /* first spare rank in the shoot record (ranks 0..416 belong to the original trainers) */

static u16* varp(u32 bit){ return (u16*)(SB1+0x1000+((g_vars[bit>>4]-0x4000)<<1)); }
static int bit_get(u32 b){ return (*varp(b)>>(b&15))&1; }
static void bit_set(u32 b){ *varp(b) |= (u16)(1<<(b&15)); }
static int jidx(u32 id){ for(int i=0;i<NJ;i++) if(J_IDS[i]==id) return i; return -1; }
static u8* tmpl_for(u8 lid){
    u8 n=EVENTS[0]; u8* t=SB1+0x8E0;
    for(int i=0;i<n&&i<64;i++,t+=0x18) if(t[0]==lid) return t;
    return 0;
}
static int tmpl_trainer(u8* t){
    u32 s=*(u32*)(t+0x10);
    if(s<0x08000000||s>=0x0A000000) return -1;
    u8* p=(u8*)s;
    if(p[0]!=0x5c||p[1]>1) return -1;
    return p[2]|(p[3]<<8);
}
static void kill_tmpl(u8* t){
    t[1]=GFX_SPLAT; *(u16*)(t+0xc)=0; *(u32*)(t+0x10)=SPLAT_SCRIPT; t[9]=0; *(u16*)(t+0x14)=0;
}
// after the map's object templates are (re)loaded: shot JRA troops are splatters again
static void japply(void){
    u8 n=EVENTS[0]; u8* t=SB1+0x8E0;
    for(int i=0;i<n&&i<64;i++,t+=0x18){
        if(t[1]==GFX_SPLAT) continue;
        int id=tmpl_trainer(t); if(id<0) continue;
        int j=jidx(id); if(j<0) continue;
        if(bit_get(512+JB+j)) kill_tmpl(t);
    }
}
void gw_load(void){ ((void(*)(void))ROB_WRAP_LOAD)(); japply(); }
void gw_scripts(void){ ((void(*)(void))ROB_WRAP_SCRIPTS)(); japply(); }

// GSV3: 0 not a JRA trooper, 1 soldier, 2 Captain, 3 General
void jra_info(void){
    u32 id=OPP; GSV(3)=0;
    if(jidx(id)<0) return;
    u8 cls=((u8*)(TRAINERS+40*id))[1];
    GSV(3)=(cls==48)?1:(cls==44)?2:(cls==45)?3:0;
}
// cash for shooting a JRA trooper: highest level x 4 x class value; digits are left in gStringVar1
void jra_pay(void){
    u32 id=OPP; u8* tr=(u8*)(TRAINERS+40*id);
    u8 n=tr[32]; u8* party=*(u8**)(tr+36);
    u32 sz=(tr[0]&1)?16:8;
    u32 lvl=party[sz*(n-1)+2], cls=tr[1], val=(cls==44)?15:(cls==45)?30:5;
    u32 amt=lvl*4*val;
    AddMoney((u32*)(SB1+0x290),amt);
    static const u32 pw[6]={100000,10000,1000,100,10,1};
    u8* o=STRVAR1; int started=0;
    for(int i=0;i<6;i++){ u32 d=0; while(amt>=pw[i]){amt-=pw[i];d++;} if(d||started||i==5){ *o++=(u8)(0xA1+d); started=1; } }
    *o=0xFF;
}
// shooting a JRA trooper: splatter, Kill Count +1, the player takes their whole party
void jra_shoot(void){
    u32 id=OPP; int j=jidx(id); if(j<0) return;
    bit_set(512+JB+j);
    u8* t=tmpl_for((u8)LASTTALKED); if(t) kill_tmpl(t);
    u16* p=kc_var(KC_POL_KILLS); if(*p<KC_MAX) (*p)++;
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

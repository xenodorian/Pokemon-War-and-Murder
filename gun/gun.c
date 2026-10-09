// Natives for the JRA soldier options (bless / threaten / shoot). Linked at a fixed ROM address by tools/gun.py.
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32; typedef short s16;
#include "../stage2/data.h"        // g_vars[], SPLAT_SCRIPT, GFX_SPLAT
#include "../leg2/killcount.h"     // kc_var, KC_POL_KILLS, KC_MAX
#include "../leg2/leg2_data.h"      // T_KILLS, T_BLESS, T_KARMA, SIGN0, SIGN1
#include "gun_data.h"              // J_IDS[], NJ, ROB_WRAP_LOAD, ROB_WRAP_SCRIPTS, KILL_CHECK, T_LIB, T_HIDDEN
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
#define LIB_VAR 0x40AC              /* Liberty Count: JRA troopers shot (never touches Karma). Not 0x40AA: that is the quest log's own backup variable */
#define DEAL_VAR 0x40AB             /* bit0: the police made their offer, bit1: the player took the deal */
#define BLESS_VAR 0x40F4
#define POL0 55
#define NPOL 24
#define POL_HIDE 0x4AD
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
        if(bit_get(JB+j)) kill_tmpl(t);
    }
}
static int deal_on(void){ return (*kc_var(DEAL_VAR)&2)!=0; }
// with the deal made, the generated officers never show up
static void police_off(void){
    if(!deal_on()) return;
    u8 n=EVENTS[0]; u8* t=SB1+0x8E0;
    for(int i=0;i<n&&i<64;i++,t+=0x18){
        if(t[1]==GFX_SPLAT) continue;
        int id=tmpl_trainer(t); if(id<POL0||id>=POL0+NPOL) continue;
        SB1[0xEE0+(POL_HIDE>>3)]|=(u8)(1<<(POL_HIDE&7)); *(u16*)(t+0x14)=POL_HIDE;
    }
}
// Dark Spirits: a spirit is on the map only once the Spirit Witch has asked for it, and never after it was caught or defeated.
// Its template carries its own hide flag, which is recomputed on every map load.
#define SP_PROG 0x40F5
#define SP_INTRO 0x4DA
#define SP_CAUGHT 0x4D0
#define SP_DEF 0x4DB
#define SP_HIDE 0x4E5
static int fget(u32 f){ return (SB1[0xEE0+(f>>3)]>>(f&7))&1; }
static void fput(u32 f,int v){ u8* p=SB1+0xEE0+(f>>3); if(v) *p|=(u8)(1<<(f&7)); else *p&=(u8)~(1<<(f&7)); }
static void spirits_vis(void){
    u16 prog=*kc_var(SP_PROG);
    for(int k=0;k<10;k++) fput(SP_HIDE+k,!(fget(SP_INTRO)&&prog==k&&!fget(SP_CAUGHT+k)&&!fget(SP_DEF+k)));
}
void gw_load(void){ ((void(*)(void))ROB_WRAP_LOAD)(); japply(); police_off(); spirits_vis(); }
void gw_scripts(void){ ((void(*)(void))ROB_WRAP_SCRIPTS)(); japply(); police_off(); spirits_vis(); }
// the police's kill check, as before, but silent once the deal is made
void kill_check2(void){ ((void(*)(void))KILL_CHECK)(); if(deal_on()) GSV(7)=0; }
// GSV7: 1 = the officer in front of the player should make the offer now. GSV6: 1 = a generated officer (they vanish after the deal)
void deal_info(void){
    u32 id=GSV(4)?GSV(4):OPP; GSV(7)=0; GSV(6)=0; GSV(4)=0;
    if(id<50||id>=POL0+NPOL) return;
    if(id>=POL0) GSV(6)=1;
    if(*kc_var(DEAL_VAR)&3) return;
    if(*kc_var(LIB_VAR)>10 && kc_total()>10) GSV(7)=1;
}
void deal_accept(void){ *kc_var(DEAL_VAR)|=3; }
void deal_refuse(void){ *kc_var(DEAL_VAR)|=1; }
void deal_state(void){ GSV(7)=deal_on()?1:0; }
// after rob_info: once the deal is made, only the military can be shot
void deal_gate(void){ if(deal_on()) GSV(5)=0; }

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
    bit_set(JB+j);
    u8* t=tmpl_for((u8)LASTTALKED); if(t) kill_tmpl(t);
    u16* p=kc_var(LIB_VAR); if(*p<KC_MAX) (*p)++;
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

// the KILLS screen: Kill Count (hidden once the deal is made), Liberty Count, Bless Count, Karma. Text is built at gStringVar1.
static u8* put_str(u8* o,const u8* s){ while(*s!=0xFF) *o++=*s++; return o; }
static u8* put_num(u8* o,u32 v){
    static const u32 pw[5]={10000,1000,100,10,1};
    int started=0;
    for(int i=0;i<5;i++){ u32 d=0; while(v>=pw[i]){v-=pw[i];d++;} if(d||started||i==4){ *o++=(u8)(0xA1+d); started=1; } }
    return o;
}
void kc_show2(void){
    u32 n=kc_total(); u32 b=*kc_var(BLESS_VAR); int k=(int)b-(int)n; u32 lib=*kc_var(LIB_VAR);
    u8* o=STRVAR1;
    if(!deal_on()){ o=put_str(o,T_KILLS); o=put_num(o,n); *o++=0xFE; }      /* with the deal made the Kill Count entry is gone */
    o=put_str(o,T_LIB); o=put_num(o,lib);
    if(deal_on()){ *o++=0xFE; o=put_str(o,T_BLESS); o=put_num(o,b); *o++=0xFB; }
    else { *o++=0xFB; o=put_str(o,T_BLESS); o=put_num(o,b); *o++=0xFE; }
    o=put_str(o,T_KARMA);
    if(k<0){ *o++=SIGN0; if(SIGN1) *o++=SIGN1; k=-k; }
    o=put_num(o,(u32)k); *o++=0x00; *o=0xFF;
}
// the Hall of Justice speech: Liberty Count into gStringVar1; GSV7 = 1 when there is one to mention
void lib_text(void){
    u32 lib=*kc_var(LIB_VAR); u8* o=put_num(STRVAR1,lib); *o=0xFF; GSV(7)=lib?1:0;
}

// ---- Arceus floats: his object sprite gets this callback, which lifts it up to half a tile and back, never below its rest position (his tile)
#define GSPRITES 0x0202063C
#define OBJEVENTS 0x02036E38
#define SPRITE_ORIG_CB 0x080609D5
static const u8 BOB[90]={0,0,0,0,0,0,0,0,1,1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,6,6,6,6,7,7,7,7,7,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,7,7,7,7,7,6,6,6,6,5,5,5,5,4,4,4,4,3,3,3,3,2,2,2,2,1,1,1,1,1,0,0,0,0,0,0,0};
void arc_cb(u8* s){
    ((void(*)(u8*))SPRITE_ORIG_CB)(s);
    s16* ph=(s16*)(s+0x3C); int i=*ph; if(i<0||i>=90) i=0;
    *ph=(s16)(i+1>=90?0:i+1);
    *(s16*)(s+0x26)=(s16)(-(int)BOB[i]);
}
void arc_install(void){
    for(int i=0;i<16;i++){
        u8* o=(u8*)(OBJEVENTS+0x24*i);
        if(!(o[0]&1)||o[5]!=ARC_GFX) continue;
        u8* sp=(u8*)(GSPRITES+0x44*o[4]);
        *(u32*)(sp+0x1C)=((u32)(void*)arc_cb)|1;
    }
}

// ---- the Hall of Justice record: the team (species and level) at the moment General Gore fell, kept in its own variables (0x40AC..0x40B4), apart from the Hall of Fame
static const u16 JH_SPV[6]={0x40AD,0x40AF,0x40B0,0x40B1,0x40B2,0x40B3};   /* species of the six slots */
static const u16 JH_LVV[3]={0x40EC,0x40ED,0x40EE};                          /* levels, two to a variable */
#define PARTY 0x02024284
#define PARTYCOUNT 0x02024029
#define GETMON ((u32(*)(void*,u32,void*))(0x0803FBE8|1))
#define SPNAMES 0x08245EE0
void jh_record(void){
    u32 n=*(u8*)PARTYCOUNT; if(n>6) n=6;
    for(u32 i=0;i<6;i++){
        u32 sp=0, lv=0;
        if(i<n){ void* mon=(void*)(PARTY+100*i); sp=GETMON(mon,11,0); lv=GETMON(mon,56,0); }
        *kc_var(JH_SPV[i])=(u16)sp;
        u16* lp=kc_var(JH_LVV[i>>1]);
        if(i&1) *lp=(u16)((*lp&0x00FF)|(lv<<8)); else *lp=(u16)((*lp&0xFF00)|(lv&0xFF));
    }
}
static u32 jh_level(u32 i){ u16 v=*kc_var(JH_LVV[i>>1]); return (i&1)?(v>>8):(v&0xFF); }
// GSV1 = species of slot GSV4 (0 = none), gStringVar1 = its level
void jh_slot(void){
    u32 i=GSV(4); if(i>5){ GSV(1)=0; return; }
    GSV(1)=*kc_var(JH_SPV[i]);
    u8* o=put_num(STRVAR1,jh_level(i)); *o=0xFF;
}
// the roll of honour: "NAME Lv45" lines, two to a page, in gStringVar1. GSV7 = 1 when a team is recorded
void jh_roll(void){
    u8* o=STRVAR1; u32 k=0;
    for(u32 i=0;i<6;i++){
        u32 sp=*kc_var(JH_SPV[i]); if(!sp) continue;
        if(k){ *o++=(k&1)?0xFE:0xFB; }
        const u8* nm=(const u8*)(SPNAMES+11*sp);
        while(*nm!=0xFF) *o++=*nm++;
        o=put_str(o,T_LV); o=put_num(o,jh_level(i)); k++;
    }
    *o=0xFF; GSV(7)=k?1:0;
}

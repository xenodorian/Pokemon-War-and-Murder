// Trainer menu natives (tools/trainer_menu_fix.py). Freestanding thumb, linked at a fixed ROM address by the stage.
// One slot per ordinary trainer: slots 0..NG-1 are the original ranks (old bit store: used = bit r, killed = bit 512+r, see stage2/rob.c),
// slots NG.. are extra trainers (gym leaders, women of the camps ...) with all their bits in the new store.
// New store (BLOC): one 'blessed' bit per slot, then used and killed for each extra slot. A locator is a flag number (< 0x900)
// or 0x8000 | (var index << 4) | bit for a var 0x4000 + index.
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
#include "tm_gen.h"
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
#define KC_POL_KILLS 0x40F7
#define KC_MAX 999

static u16* varp(u32 id){ return (u16*)(SB1+0x1000+((id-0x4000)<<1)); }
// old store
static u16* ovar(u32 bit){ return varp(GVARS[bit>>4]); }
static int oget(u32 b){ return (*ovar(b)>>(b&15))&1; }
static void oset(u32 b){ *ovar(b) |= (u16)(1<<(b&15)); }
// new store
static int nget(u32 i){
    u16 v=BLOC[i];
    if(v&0x8000) return (*varp(0x4000+((v>>4)&0xFF))>>(v&15))&1;
    return (SB1[0xEE0+(v>>3)]>>(v&7))&1;
}
static void nset(u32 i){
    u16 v=BLOC[i];
    if(v&0x8000) *varp(0x4000+((v>>4)&0xFF)) |= (u16)(1<<(v&15));
    else SB1[0xEE0+(v>>3)] |= (u8)(1<<(v&7));
}
static int slot_of(u32 id){ for(int i=0;i<NSLOT;i++) if(TM_IDS[i]==id) return i; return -1; }
static int used_get(int s){ return s<NG ? oget(s) : nget(NSLOT+2*(s-NG)); }
static void used_set(int s){ if(s<NG) oset(s); else nset(NSLOT+2*(s-NG)); }
static int killed_get(int s){ return s<NG ? oget(512+s) : nget(NSLOT+2*(s-NG)+1); }
static void killed_set(int s){ if(s<NG) oset(512+s); else nset(NSLOT+2*(s-NG)+1); }

static u8* tmpl_for(u8 lid){
    u8 n=EVENTS[0]; u8* t=SB1+0x8E0;
    for(int i=0;i<n&&i<64;i++,t+=0x18) if(t[0]==lid) return t;
    return 0;
}
static void kill_tmpl(u8* t){
    t[1]=GFX_SPLAT; *(u16*)(t+0xc)=0; *(u32*)(t+0x10)=SPLAT_SCRIPT; t[9]=0; *(u16*)(t+0x14)=0;
}
// first and last+1 entry of the object table for the current map
static void map_range(int* a,int* z){
    u8 g=SB1[4], n=SB1[5]; int i=0;
    while(i<NMT && !(MT_G[i]==g&&MT_N[i]==n)) i++;
    int j=i; while(j<NMT && MT_G[j]==g&&MT_N[j]==n) j++;
    *a=i; *z=j;
}
// does object template t belong to trainer slot s on this map
static int tmpl_is(u8* t,int s,int a,int z){
    for(int k=a;k<z;k++) if(MT_L[k]==t[0]&&MT_S[k]==s) return 1;
    return 0;
}
// after the map's object templates are (re)loaded: shot trainers become splatters again
static void apply_killed(void){
    int a,z; map_range(&a,&z); if(a==z) return;
    u8 n=EVENTS[0]; u8* t=SB1+0x8E0;
    for(int i=0;i<n&&i<64;i++,t+=0x18){
        if(t[1]==GFX_SPLAT){ *(u32*)(t+0x10)=SPLAT_SCRIPT; continue; }
        for(int k=a;k<z;k++) if(MT_L[k]==t[0]&&killed_get(MT_S[k])){ kill_tmpl(t); break; }
    }
}
void tm_wrap_load(void){ ((void(*)(void))(0x08054f68|1))(); apply_killed(); }
void tm_wrap_scripts(void){ ((void(*)(void))(0x080550a8|1))(); apply_killed(); }

// GSV4: 0 fresh, 1 threatened (used), 2 blessed.  GSV6: trainer known.  GSV8: 1 when the object talked to is this trainer's (the splatter step is then safe).
void tm_info(void){
    GSV(4)=0; GSV(5)=0; GSV(6)=0; GSV(8)=0;
    int s=slot_of(OPP); if(s<0) return;
    GSV(6)=1; GSV(5)=1;
    GSV(4)= nget(s) ? 2 : (used_get(s) ? 1 : 0);
    int a,z; map_range(&a,&z);
    u8* t=tmpl_for((u8)LASTTALKED);
    if(t&&tmpl_is(t,s,a,z)) GSV(8)=1;
}
// blessing: the stock routine does the item, the Bless Count and the used bit of an original rank
void tm_bless(void){
    int s=slot_of(OPP);
    ((void(*)(void))(OLD_BLESS))();
    if(s<0) return;
    nset(s); used_set(s);
}
// threatening / the money of a shot trainer: highest level x 4 x class value, digits left in gStringVar1
void tm_pay(void){
    u32 id=OPP; int s=slot_of(id); if(s<0) return;
    used_set(s);
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
// shooting: the objects of this trainer on this map (a double battle has two) become splatters, GSV7 = the partner's local id, the party is taken
void tm_shoot(void){
    u32 id=OPP; int s=slot_of(id); if(s<0) return;
    killed_set(s);
    GSV(7)=0;
    int a,z; map_range(&a,&z);
    u8 n=EVENTS[0]; u8* q=SB1+0x8E0;
    for(int i=0;i<n&&i<64;i++,q+=0x18){
        if(q[1]==GFX_SPLAT) continue;
        if(tmpl_is(q,s,a,z)){ if(q[0]!=(u8)LASTTALKED) GSV(7)=q[0]; kill_tmpl(q); }
    }
    if(s>=NG){ u16* p=varp(KC_POL_KILLS); if(*p<KC_MAX) (*p)++; }   // the Kill Count counts the original ranks by their bits; extra trainers go on the officers' counter
    u8* tr=(u8*)(TRAINERS+40*id);
    u8 pf=tr[0], np=tr[32]; u8* party=*(u8**)(tr+36);
    u32 sz=(pf&1)?16:8;
    for(int i=0;i<np;i++){
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

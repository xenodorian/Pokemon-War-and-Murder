// Church native routines: kill price, forgiveness, and a replacement for the shot-trainer pass that hides forgiven splatters.
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
#include "../stage2/data.h"
#define SB1 (*(u8* volatile*)0x03005008)
#define GSV(n) (*(volatile u16*)(0x020370b8+2*(n)))
#define EVENTS (*(u8* volatile*)(0x02036dfc+4))
#define STRVAR1 ((u8*)0x02021cd0)
#define HIDE_FLAG 0x4AC
static u16* varp(u32 bit){ return (u16*)(SB1+0x1000+((g_vars[bit>>4]-0x4000)<<1)); }
static int bit_get(u32 b){ return (*varp(b)>>(b&15))&1; }
static int flag_get(u32 f){ return (SB1[0xEE0+(f>>3)]>>(f&7))&1; }
static void flag_clr(u32 f){ SB1[0xEE0+(f>>3)]&=(u8)~(1<<(f&7)); }
static int active_kill(u32 r){ return bit_get(512+r)&&flag_get(0x500+g_ids[r]); }
static int rank_of(u32 id){ for(int i=0;i<NIDS;i++) if(g_ids[i]==id) return i; return -1; }
static int tmpl_trainer(u8* t){
    u32 s=*(u32*)(t+0x10);
    if(s<0x08000000||s>=0x0A000000) return -1;
    u8* p=(u8*)s;
    if(p[0]!=0x5c||p[1]!=0) return -1;
    return p[2]|(p[3]<<8);
}
static void kill_tmpl(u8* t){ t[1]=GFX_SPLAT; *(u16*)(t+0xc)=0; *(u32*)(t+0x10)=SPLAT_SCRIPT; t[9]=0; *(u16*)(t+0x14)=0; }
static void hide_tmpl(u8* t){ *(u16*)(t+0x14)=HIDE_FLAG; }
// same as the original pass, but a shot trainer whose defeat flag was cleared by the church stays out of the world
void apply_killed2(void){
    u8 n=EVENTS[0]; u8* t=SB1+0x8E0;
    for(int i=0;i<n&&i<64;i++,t+=0x18){
        if(t[1]==GFX_SPLAT){ *(u32*)(t+0x10)=SPLAT_SCRIPT; continue; }
        if(*(u16*)(t+0xc)==0) continue;
        int id=tmpl_trainer(t); if(id<0) continue;
        int r=rank_of(id); if(r<0||!g_shoot[r]) continue;
        if(bit_get(512+r)){ if(flag_get(0x500+id)) kill_tmpl(t); else hide_tmpl(t); }
    }
}
// GSV7 = kill count capped at 10; STRVAR1 = price text (1000 per kill, 9999 for 10 or more)
void kill_price(void){
    u32 n=0;
    for(u32 r=0;r<NIDS;r++) if(active_kill(r)) n++;
    if(n>10) n=10;
    GSV(7)=(u16)n;
    u32 amt=n*1000; if(amt>9999) amt=9999;
    static const u32 pw[5]={10000,1000,100,10,1};
    u8* o=STRVAR1; int started=0;
    for(int i=0;i<5;i++){ u32 d=0; while(amt>=pw[i]){amt-=pw[i];d++;} if(d||started||i==4){ *o++=(u8)(0xA1+d); started=1; } }
    *o=0xFF;
}
void kill_forgive(void){
    for(u32 r=0;r<NIDS;r++) if(active_kill(r)) flag_clr(0x500+g_ids[r]);
}

// Church native routines: kill price, forgiveness, and a replacement for the shot-trainer pass that hides forgiven splatters.
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32; typedef short s16;
#include "../stage2/data.h"
#include "../leg2/killcount.h"
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
#define POL0 55
#define NPOL 24
#define POL_HIDE 0x4AD
#define POL_EPOCH 0x40F8
#define RND ((u32(*)(void))(0x08044ec8|1))
static void flag_set(u32 f){ SB1[0xEE0+(f>>3)]|=(u8)(1<<(f&7)); }
// random open outdoor tile for an officer; keeps the template's old position when nothing suitable turns up
static void pol_place(u8* t){
#ifdef NO_PLACE
    return;
#endif
    u8* hdr=(u8*)0x02036dfc; u32 lay=*(u32*)hdr; if(lay<0x08000000) return;
    int w=*(int*)lay, h=*(int*)(lay+4); u16* mp=*(u16**)(lay+12);
    u8* ev=(u8*)*(u32*)(hdr+4);
    s16 px=*(s16*)SB1, py=*(s16*)(SB1+2);
    u8 no=ev[0]; u8 nw=ev[1]; u8 nb=ev[3];
    for(int tries=0;tries<80;tries++){
        int x=(int)((RND()*(u32)w)>>16), y=(int)((RND()*(u32)h)>>16);
        if(x<2||y<2||x>=w-2||y>=h-2) continue;
        int dx=x-px, dy=y-py; if(dx<0) dx=-dx; if(dy<0) dy=-dy; if(dx+dy<6) continue;
        int ok=1;
        for(int k=-1;k<=1&&ok;k++) for(int j=-1;j<=1;j++){ u16 b=mp[(y+k)*w+(x+j)]; if((b&0xC00)||(b>>12)!=3){ ok=0; break; } }
        if(!ok) continue;
        u8* o=KC_SB1+0x8E0;
        for(int i=0;i<no&&i<64&&ok;i++,o+=0x18){ if(o==t) continue; int ox=*(s16*)(o+4), oy=*(s16*)(o+6); int ddx=ox-x, ddy=oy-y; if(ddx<0) ddx=-ddx; if(ddy<0) ddy=-ddy; if(ddx<=2&&ddy<=2) ok=0; }
        if(ok&&nw){ u8* wp=(u8*)*(u32*)(ev+8); for(int i=0;i<nw;i++){ int wx=*(s16*)(wp+8*i), wy=*(s16*)(wp+8*i+2); int ddx=wx-x, ddy=wy-y; if(ddx<0) ddx=-ddx; if(ddy<0) ddy=-ddy; if(ddx<=2&&ddy<=2) ok=0; } }
        if(ok&&nb){ u8* bp=(u8*)*(u32*)(ev+16); for(int i=0;i<nb;i++){ int bx=*(u16*)(bp+12*i), by=*(u16*)(bp+12*i+2); int ddx=bx-x, ddy=by-y; if(ddx<0) ddx=-ddx; if(ddy<0) ddy=-ddy; if(ddx<=1&&ddy<=1) ok=0; } }
        if(!ok) continue;
        *(s16*)(t+4)=(s16)x; *(s16*)(t+6)=(s16)y; return;
    }
}
static void police_pass(u8 n){
    u32 total=kc_total(); u16* ep=kc_var(POL_EPOCH);
#ifdef NO_EPOCH
    if(0){
#else
    if(total>*ep){
#endif
        for(u32 i=0;i<NPOL;i++){ u32 f=0x500+POL0+i; SB1[0xEE0+(f>>3)]&=(u8)~(1<<(f&7)); } *ep=(u16)total; }
    else if(total<*ep) *ep=(u16)total;
    u8* t=SB1+0x8E0;
    for(int i=0;i<n&&i<64;i++,t+=0x18){
        if(t[1]==GFX_SPLAT||*(u16*)(t+0xc)==0) continue;
        int id=tmpl_trainer(t); if(id<POL0||id>=POL0+NPOL) continue;
#ifdef NO_HIDE
        if(total>10){
#else
        if(total>10&&!flag_get(0x500+id)){
#endif
            *(u16*)(t+0x14)=0; pol_place(t); }
        else { flag_set(POL_HIDE); *(u16*)(t+0x14)=POL_HIDE; }
    }
}
void apply_killed2(void){
    u8 n=EVENTS[0]; u8* t=SB1+0x8E0;
    for(int i=0;i<n&&i<64;i++,t+=0x18){
        if(t[1]==GFX_SPLAT){ *(u32*)(t+0x10)=SPLAT_SCRIPT; continue; }
        if(*(u16*)(t+0xc)==0) continue;
        int id=tmpl_trainer(t); if(id<0) continue;
        int r=rank_of(id); if(r<0||!g_shoot[r]) continue;
        if(bit_get(512+r)){ if(flag_get(0x500+id)) kill_tmpl(t); else hide_tmpl(t); }
    }
    police_pass(n);
}
// GSV7 = kill count capped at 10; STRVAR1 = price text (1000 per kill, 9999 for 10 or more)
void kill_price(void){
    u32 n=kc_total();
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
    *kc_var(KC_POL_KILLS)=0;
}

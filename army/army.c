// JRA native routines: random patrol placement, and soldiers shooting bystanders (persistent blood splatters that never touch the player's Kill Count).
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32; typedef short s16;
#include "../stage2/data.h"
#include "army_data.h"
#include "../leg2/killcount.h"
#define SB1 (*(u8* volatile*)0x03005008)
#define EVENTS (*(u8* volatile*)(0x02036dfc+4))
#define STRVAR1 ((u8*)0x02021cd0)
#define GVAR(n) (*(volatile u16*)(0x020370b8+2*((n)-0x8000)))
#define RND ((u32(*)(void))(0x08044ec8|1))
#define OLD_PASS ((void(*)(void))OLD_APPLY)
static int flag_get(u32 f){ return (SB1[0xEE0+(f>>3)]>>(f&7))&1; }
static int tmpl_trainer(u8* t){
    u32 s=*(u32*)(t+0x10);
    if(s<0x08000000||s>=0x0A000000) return -1;
    u8* p=(u8*)s;
    if(p[0]!=0x5c||p[1]>1) return -1;
    return p[2]|(p[3]<<8);
}
static int pat_index(int id){ for(int i=0;i<NPAT;i++) if(PAT_ID[i]==id) return i; return -1; }
// random open outdoor tile away from the player, other objects, warps and signs (same rules as the police placement)
static void place(u8* t){
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
static void make_splat(u8* t){ t[1]=GFX_ARMY_SPLAT; *(u16*)(t+0xc)=0; *(u32*)(t+0x10)=*(volatile u32*)SPLAT_SLOT; t[9]=0; *(u16*)(t+0x14)=0; }
static int eligible(u8* t){
    if(t[1]>=0x58) return 0;                       // vanilla people only (no signs, trees, boulders, or any custom graphic)
    if(*(u16*)(t+0x14)!=0) return 0;               // anything with a hide flag may be story relevant
    u32 s=*(u32*)(t+0x10); if(s<0x08000000||s>=0x0A000000) return 0;
    if(tmpl_trainer(t)>=0) return 0;
    return t[0]<=16;
}
static void army_pass(u8 n){
    u8* t=SB1+0x8E0; int city=-1;
    for(int i=0;i<n&&i<64;i++,t+=0x18){
        if(t[1]!=GFX_SOLDIER) continue;
        int id=tmpl_trainer(t); if(id<0) continue;
        int k=pat_index(id); if(k<0) continue;
        city=k;
        if(flag_get(PAT_CLEARED[k])) continue;
        place(t);
    }
    if(city<0) return;
    if(flag_get(PAT_CLEARED[city])) return;
    u16* mv=kc_var(PAT_VICTIMS[city]); u16 mask=*mv;
    t=SB1+0x8E0;
    for(int i=0;i<n&&i<64;i++,t+=0x18) if(t[0]<=16&&((mask>>t[0])&1)&&t[1]<0x58) make_splat(t);
    int cnt=0; for(int b=1;b<=16;b++) cnt+=(mask>>b)&1;
    if(cnt>=MAX_VICTIMS) return;
    if(((RND()*4)>>16)!=0) return;                 // about one visit in four
    int pick=-1, seen=0; t=SB1+0x8E0;
    for(int i=0;i<n&&i<64;i++,t+=0x18){ if(!eligible(t)) continue; seen++; if(((RND()*(u32)seen)>>16)==0) pick=i; }
    if(pick<0) return;
    t=SB1+0x8E0+0x18*pick;
    *mv=mask|(u16)(1<<t[0]);
    make_splat(t);
}
void army_entry(void){
    OLD_PASS();
    army_pass(EVENTS[0]);
}
// examine script of a victim: puts an arbitrary reason (picked by the victim's local id) in STRVAR1
void army_note(void){
    u32 id=GVAR(0x800f)&0xff;
    id=id%NREASONS;
    const u8* s=REASONS[id]; u8* o=STRVAR1; while(*s!=0xFF) *o++=*s++; *o=0xFF;
}

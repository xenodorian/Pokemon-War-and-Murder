// Stage 3 native routines: SELL POKEMON (PC box browser + pricing). Freestanding thumb, linked at a fixed ROM address.
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
#include "sdata.h"   // NSP, g_mult[]
#define STORAGE (*(u8* volatile*)0x03005010)           /* gPokemonStoragePtr: [0]=currentBox, mons from +4, 80 bytes each */
#define SB1 (*(u8* volatile*)0x03005008)
#define GSV(n) (*(volatile u16*)(0x020370b8+2*(n)))    /* script special vars 0x8000.. */
#define RESULT (*(volatile u16*)0x020370d0)
#define BUF1 ((u8*)0x02021cd0)
#define BUF2 ((u8*)0x02021dd0)
#define BUF3 ((u8*)0x02021ed0)
#define GetMonData    ((u32(*)(void*,u32,void*))(0x0803fbe8|1))
#define GetBoxMonData ((u32(*)(void*,u32,void*))(0x0803fd44|1))
#define CalcStats     ((void(*)(void*))(0x0803e47c|1))
#define AddMoney      ((void(*)(u32*,u32))(0x0809fda0|1))
#define QuitShop      ((void(*)(u8))(0x0809acf8|1))
#define SPNAMES ((const u8*)0x08245ee0)
#define NMONS 420
#define PENDING 0x5E11

// no hardware divide on the GBA CPU: tiny shift-subtract helpers for the compiler's division calls
typedef unsigned long long u64;
u32 __aeabi_uidiv(u32 n,u32 d){ u32 q=0,r=0; for(int i=31;i>=0;i--){ r=(r<<1)|((n>>i)&1); if(r>=d){ r-=d; q|=1u<<i; } } return q; }
u64 __aeabi_uidivmod(u32 n,u32 d){ u32 q=0,r=0; for(int i=31;i>=0;i--){ r=(r<<1)|((n>>i)&1); if(r>=d){ r-=d; q|=1u<<i; } } return (u64)q|((u64)r<<32); }
int __aeabi_idiv(int n,int d){ int neg=0; u32 a=n,b=d; if(n<0){ a=-a; neg^=1; } if(d<0){ b=-b; neg^=1; } u32 q=__aeabi_uidiv(a,b); return neg?-(int)q:(int)q; }
u64 __aeabi_idivmod(int n,int d){ int q=__aeabi_idiv(n,d); int r=n-q*d; return (u64)(u32)q|((u64)(u32)r<<32); }

static u8 CH(char c){
    if(c>='0'&&c<='9') return 0xA1+(c-'0');
    if(c>='A'&&c<='Z') return 0xBB+(c-'A');
    if(c>='a'&&c<='z') return 0xD5+(c-'a');
    switch(c){
    case '$': return 0xB7; case '.': return 0xAD; case '-': return 0xAE; case '/': return 0xBA;
    case '!': return 0xAB; case '?': return 0xAC; case '\n': return 0xFE; case ',': return 0xB8;
    }
    return 0;
}
static u8* P(u8* d,const char* s){ while(*s) *d++=CH(*s++); return d; }
static u8* PN(u8* d,u32 n){
    u8 t[10]; int k=0;
    do{ t[k++]=0xA1+n%10; n/=10; }while(n);
    while(k) *d++=t[--k];
    return d;
}
static u8* PNAME(u8* d,u32 sp){
    const u8* s=SPNAMES+11*sp;
    for(int i=0;i<10&&s[i]!=0xFF;i++) *d++=s[i];
    return d;
}
static u32 value_of(u8* m,u32* lvl,u32* sp){
    u32 s=GetBoxMonData(m,11,0);
    u32 tmp[25];
    u8* t=(u8*)tmp;
    for(int k=0;k<80;k++) t[k]=m[k];
    for(int k=80;k<100;k++) t[k]=0;
    CalcStats(t);
    u32 sum=0;
    for(u32 f=58;f<=63;f++){ u32 v=GetMonData(t,f,0); sum+=v;
#ifdef DEBUGFILL
        GSV(f-58)=(u16)v;
#endif
    }
    *lvl=GetMonData(t,56,0); *sp=s;
    u32 mult=(s<NSP)?g_mult[s]:1; if(!mult) mult=1;
    return sum*mult;
}
// the mart's SELL POKEMON menu entry: ends the shop and flags the script to run the sell flow
void ps_choose(u8 taskId){
    RESULT=PENDING;
    QuitShop(taskId);
}
#define SELLFLAG (*(volatile u16*)0x020370c8)          /* script special var 0x8008: 1 while selling from the PC */
#define CURSOR_AREA (*(volatile signed char*)0x02039820) /* PC storage cursor: 0 = box, 1 = party */
#define CURSOR_POS  (*(volatile signed char*)0x02039821)
#define G_VALUE_LO GSV(9)
#define G_VALUE_HI GSV(10)
static u8* cursor_mon(void){
    if(CURSOR_AREA==0){ u8 b=STORAGE[0]; return STORAGE+4+(b*30+CURSOR_POS)*80; }
    if(CURSOR_AREA==1) return (u8*)0x02024284+100*CURSOR_POS;
    return 0;
}
// replaces the PC storage messages while selling: 9 = "Release this POKeMON?", 10 = "was released.", 11 = "Bye-bye"
const u8* ps_text(u32 id,const u8* dflt){
    if(SELLFLAG!=0x5E11) return dflt;
    if(id==9){
        u8* m=cursor_mon(); if(!m) return dflt;
        u32 lvl,sp; u32 v=value_of(m,&lvl,&sp);
        G_VALUE_LO=(u16)v; G_VALUE_HI=(u16)(v>>16);
        u8* d=BUF2; d=P(d,"Sell for $"); d=PN(d,v); d=P(d,"?"); *d=0xFF;
        d=BUF1; d=P(d,"Sold for $"); d=PN(d,v); d=P(d,"!"); *d=0xFF;
        return BUF2;
    }
    if(id==10){
        AddMoney((u32*)(SB1+0x290),(u32)G_VALUE_LO|((u32)G_VALUE_HI<<16));
        return BUF1;
    }
    if(id==11){
        u8* d=BUF3; d=P(d,"Pleasure doing business!"); *d=0xFF; return BUF3;
    }
    return dflt;
}
#ifdef DEBUGFILL
typedef void (*fn_create)(void*,u16,u8,u8,u8,u32,u8,u32);
#define CreateMon ((fn_create)(0x0803da54|1))
void ps_debugfill(void){
    static const u16 sp[]={150,5,6,4,25,26,133,1,129,249,251,131};
    static const u8 lv[]={70,20,36,10,5,30,15,100,10,60,50,40};
    static const u16 slot[]={0,1,2,3,4,5,6,7,30,31,60,419};
    for(int n=0;n<12;n++){
        u32 tmp[25]; CreateMon(tmp,sp[n],lv[n],31,0,0,0,0);
        u8* m=STORAGE+4+slot[n]*80; u8* t=(u8*)tmp;
        for(int k=0;k<80;k++) m[k]=t[k];
    }
}
#endif

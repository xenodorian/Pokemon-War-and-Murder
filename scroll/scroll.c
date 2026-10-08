/* Scrolling pause menu: shows at most V rows above the description box and scrolls one row at a time. */
typedef unsigned char u8; typedef signed char s8; typedef unsigned short u16; typedef short s16; typedef unsigned int u32;
#include "scroll_data.h"   /* TBL (action table address), ACTARR */
#define V 7
#define NUM (*(volatile u8*)0x020370f5)
#define CUR (*(volatile s8*)0x020370f4)
#define MPOS (*(volatile s8*)0x0203ade6)
#define ACT ((volatile u8*)ACTARR)
#define gStringVar4 ((u8*)0x02021d18)
typedef u8 (*f_v)(void);
#define GetWin ((f_v)0x080f793d)
#define ATP ((void(*)(u8,u8,const u8*,u8,u8,u8,void*))0x08002c49)
#define SEP ((u8*(*)(u8*,const u8*))0x08008fcd)
#define PPN ((void(*)(u8,const u8*,u16,u16))0x0812e6dd)
#define FPR ((void(*)(u8,u8,u16,u16,u16,u16))0x08004379)
#define MIC ((u8(*)(u8,u8,u8,u8,u8,u8,u8))0x0810f7d9)
#define MMC ((s8(*)(s8))0x0810f905)
#define CSMW ((u8(*)(u8))0x080f78e1)

static int off_for(int g,int n){
    int off;
    if(n<=V) return 0;
    if(g<0||g>=n) g=0;
    off=g-(V-1); if(off<0) off=0; if(off>n-V) off=n-V;
    return off;
}
static void print_item(int idx,int y){
    u8 win=GetWin(); u8 a=ACT[idx];
    const u8 *txt=*(const u8* const*)(TBL+a*8);
    if(a==3||a==8) PPN(win,txt,8,y);
    else { SEP(gStringVar4,txt); ATP(win,2,gStringVar4,8,y,0xff,0); }
}
/* replaces PrintStartMenuItems(s8 *cursor, u8 n): prints only rows inside the visible window */
int psm(s8 *cp,u8 n){
    int c=*cp, N=NUM, off=off_for(CUR,N);
    do{
        if(c>=off && c<off+V) print_item(c,(c-off)*15);
        c++;
        if(c>=N){ *cp=c; return 1; }
        n--;
    }while(n);
    *cp=c; return 0;
}
/* replaces the Menu_InitCursor call: cursor shows a local row, the stored value stays the global index */
u8 init_cursor(u8 win,u8 font,u8 l,u8 t,u8 h,u8 n,u8 pos){
    int N=NUM, off;
    if(N<=V) return MIC(win,font,l,t,h,n,pos);
    if(pos>=N) pos=0;
    off=off_for(pos,N);
    MIC(win,font,l,t,h,V,pos-off);
    return pos;
}
static void reprint(int off,int local){
    u8 win=GetWin(); int i;
    FPR(win,1,0,0,56,104);
    for(i=0;i<V;i++) print_item(off+i,i*15);
    MIC(win,2,0,0,15,V,local);
}
/* replaces Menu_MoveCursor in the pause menu: returns the new global index */
s8 scroll_move(s8 d){
    int N=NUM, g=CUR, off, ng, noff;
    if(N<=V) return MMC(d);
    off=g-MPOS;
    ng=g+d; if(ng<0) ng=N-1; else if(ng>=N) ng=0;
    noff=off;
    if(ng<off) noff=ng; else if(ng>=off+V) noff=ng-V+1;
    if(noff==off){ MMC(d); return ng; }
    reprint(noff,ng-noff);
    return ng;
}
/* window height never exceeds V rows */
u8 win_h(u8 n){ return CSMW(n>V?V:n); }

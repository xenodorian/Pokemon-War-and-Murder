// Native routines of the Viridian arrest scene: MAX's PIKACHU joins the party for the double battle, and leaves again.
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
#define PARTY ((u8*)0x02024284)
#define COUNT (*(volatile u8*)0x02024029)
#define OUTCOME (*(volatile u8*)0x02023e8a)
#define RESULT (*(volatile u16*)0x020370d0)
#define GetMonData ((u32(*)(void*,int,void*))(0x0803FBE8|1))
#define ZeroMonData ((void(*)(void*))(0x0803D994|1))
#define CreateMon ((void(*)(void*,u16,u8,u8,u8,u32,u8,u32))(0x0803DA54|1))
#define MAXOT 0x4D415821u
// MAX's PIKACHU (Lv 10, marked by the trainer id MAX!) takes the next free slot; a full party has no room for it and fights alone
void viri_prepare(void){
    int n=COUNT;
    for(int i=0;i<n;i++) if(GetMonData(PARTY+100*i,1,0)==MAXOT) return;
    if(n>=6) return;
    CreateMon(PARTY+100*n,25,10,32,0,0,2,MAXOT); COUNT=(u8)(n+1);
}
static void drop(int i){
    int n=COUNT;
    for(int k=i;k<n-1;k++){ u32* d=(u32*)(PARTY+100*k); u32* s=(u32*)(PARTY+100*(k+1)); for(int w=0;w<25;w++) d[w]=s[w]; }
    ZeroMonData(PARTY+100*(n-1)); COUNT=(u8)(n-1);
}
// after the fight: PIKACHU leaves, RESULT = 1 when the player's side lost (outcome is not "won")
void viri_cleanup(void){
    for(int i=0;i<COUNT;i++) if(GetMonData(PARTY+100*i,1,0)==MAXOT){ drop(i); break; }
    RESULT=(OUTCOME==1)?0:1;
}

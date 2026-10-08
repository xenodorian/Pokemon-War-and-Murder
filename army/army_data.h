#define GFX_SOLDIER 159
#define GFX_ARMY_SPLAT 161
#define SPLAT_SLOT 0x08ed617c
#define OLD_APPLY 0x08ec2709
#define MAX_VICTIMS 3
#define NPAT 2
static const unsigned short PAT_ID[]={7,8};
static const unsigned short PAT_CLEARED[]={1216,1216};
static const unsigned short PAT_VICTIMS[]={16633,16633};
#define NREASONS 12
static const unsigned char R0[]={196,187,211,209,187,198,197,195,200,193,255};
static const unsigned char R1[]={209,191,187,204,195,200,193,0,206,194,191,0,209,204,201,200,193,0,194,187,206,255};
static const unsigned char R2[]={201,209,200,195,200,193,0,187,0,204,187,206,206,187,206,187,255};
static const unsigned char R3[]={194,207,199,199,195,200,193,0,201,192,192,0,197,191,211,255};
static const unsigned char R4[]={187,190,199,195,204,195,200,193,0,197,187,200,206,201,255};
static const unsigned char R5[]={198,201,201,197,195,200,193,0,205,207,205,202,195,189,195,201,207,205,255};
static const unsigned char R6[]={205,200,191,191,212,195,200,193,0,187,206,0,187,0,205,201,198,190,195,191,204,255};
static const unsigned char R7[]={187,205,197,195,200,193,0,203,207,191,205,206,195,201,200,205,255};
static const unsigned char R8[]={188,191,195,200,193,0,207,200,202,187,206,204,195,201,206,195,189,255};
static const unsigned char R9[]={205,206,187,200,190,195,200,193,0,201,200,0,187,0,205,194,187,190,201,209,255};
static const unsigned char R10[]={194,187,208,195,200,193,0,187,0,200,195,189,191,0,205,199,195,198,191,255};
static const unsigned char R11[]={200,201,206,0,205,187,198,207,206,195,200,193,255};
static const unsigned char* const REASONS[]={R0,R1,R2,R3,R4,R5,R6,R7,R8,R9,R10,R11};

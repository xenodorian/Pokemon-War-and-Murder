// usage: harness rom.gba script.txt outprefix
// script lines: "<frame> <keys hex> " set key mask from that frame; "shot <frame>" ; "save <frame>"; "load <file>"
#include <mgba/core/core.h>
#include <mgba/gba/core.h>
#include <mgba/core/blip_buf.h>
#include <mgba-util/vfs.h>
#include <mgba/internal/arm/arm.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef struct {int frame; int keys;} Ev;
int main(int argc,char**argv){
  struct mCore* core=mCoreFind(argv[1]);
  core->init(core);
  mCoreLoadFile(core,argv[1]);
  mCoreConfigInit(&core->config,"h");
  unsigned w,h; core->desiredVideoDimensions(core,&w,&h);
  color_t* buf=malloc(w*h*4);
  core->setVideoBuffer(core,buf,w);
  // optional battery save
  if(argc>4){ struct VFile*sv=VFileOpen(argv[4],O_CREAT|O_RDWR); if(sv) core->loadSave(core,sv);}  
  core->reset(core);
  blip_set_rates(core->getAudioChannel(core,0),core->frequency(core),48000); blip_set_rates(core->getAudioChannel(core,1),core->frequency(core),48000);
  if(getenv("LOADSTATE")){ FILE*sf=fopen(getenv("LOADSTATE"),"rb"); static char sb[700000]; size_t sn=sf?fread(sb,1,sizeof sb,sf):0; if(sf)fclose(sf); fprintf(stderr,"loadState %zu -> %d\n",sn,(int)core->loadState(core,sb)); }
  FILE*f=fopen(argv[2],"r");
  static Ev ev[100000]; int ne=0; static int shots[1000]; int ns=0; static int dumps[1000]; int nd=0; static int pk[4000][4]; int npk=0; static int rams[200][3]; int nr=0; static unsigned wr[2000][4]; int nwr=0; int total=0;
  char line[256];
  while(fgets(line,256,f)){
    int a,b,c2,d2; char c[32];
    if(sscanf(line,"shot %d",&a)==1) shots[ns++]=a;
    else if(sscanf(line,"poke2 %d %x %x",&a,&b,&c2)==3){pk[npk][0]=a;pk[npk][1]=b;pk[npk][2]=c2;pk[npk][3]=2;npk++;}
    else if(sscanf(line,"poke %d %x %x",&a,&b,&c2)==3){pk[npk][0]=a;pk[npk][1]=b;pk[npk][2]=c2;pk[npk][3]=0;npk++;}
    else if(sscanf(line,"setbit %d %x %x",&a,&b,&c2)==3){pk[npk][0]=a;pk[npk][1]=b;pk[npk][2]=c2;pk[npk][3]=1;npk++;}
    else if(sscanf(line,"ram %d %x %d",&a,&b,&c2)==3){rams[nr][0]=a;rams[nr][1]=b;rams[nr][2]=c2;nr++;}
    else if(sscanf(line,"wr %d %x %x %d",&a,&b,&c2,&d2)==4){wr[nwr][0]=a;wr[nwr][1]=b;wr[nwr][2]=c2;wr[nwr][3]=d2;nwr++;}   /* wr FRAME ADDR VALUE SIZE(1,2,4): write RAM before that frame runs */
    else if(sscanf(line,"dump %d",&a)==1) dumps[nd++]=a;
    else if(sscanf(line,"end %d",&a)==1) total=a;
    else if(sscanf(line,"%d %x",&a,&b)==2){ev[ne].frame=a;ev[ne].keys=b;ne++;}
  }
  int keys=0,ei=0;
  for(int fr=0;fr<=total;fr++){
    while(ei<ne&&ev[ei].frame<=fr){keys=ev[ei].keys;ei++;}
    for(int i=0;i<npk;i++) if(pk[i][0]==fr){unsigned sb=core->busRead32(core,pk[i][3]==2?0x0300500c:0x03005008); if(pk[i][3]==1) core->busWrite8(core,sb+pk[i][1],core->busRead8(core,sb+pk[i][1])|pk[i][2]); else core->busWrite8(core,sb+pk[i][1],pk[i][2]);}
    for(int i=0;i<nwr;i++) if((int)wr[i][0]==fr){ if(wr[i][3]==1) core->busWrite8(core,wr[i][1],wr[i][2]); else if(wr[i][3]==2) core->busWrite16(core,wr[i][1],wr[i][2]); else core->busWrite32(core,wr[i][1],wr[i][2]); }
    core->setKeys(core,keys);
    if(getenv("WATCHFRAMES")&&getenv("WATCHOFF")){   /* WATCHFRAMES=a:b WATCHOFF=hex offset in SaveBlock1 (absolute address when WATCHABS is set): single-step those frames and report every write to that 16-bit word */
      int wa,wb; sscanf(getenv("WATCHFRAMES"),"%d:%d",&wa,&wb);
      if(fr>=wa&&fr<=wb){
        unsigned off=strtoul(getenv("WATCHOFF"),0,16);
        int absw=getenv("WATCHABS")!=0; unsigned sb=absw?0:core->busRead32(core,0x03005008); unsigned last=core->busRead16(core,sb+off); unsigned long n=0; int frame0=core->frameCounter(core);
        while(core->frameCounter(core)==frame0 && n<400000){
          core->step(core); n++;
          unsigned sb2=absw?0:core->busRead32(core,0x03005008);
          unsigned v=core->busRead16(core,sb2+off);
          if(sb2!=sb){ struct ARMCore*c=core->cpu; fprintf(stderr,"WATCH f%d step %lu: SB1 pointer %08x -> %08x pc=%08x lr=%08x\n",fr,n,sb,sb2,c->gprs[15],c->gprs[14]); sb=sb2; last=v; continue; }
          if(v!=last){ struct ARMCore*c=core->cpu; fprintf(stderr,"WATCH f%d step %lu: %04x -> %04x pc=%08x lr=%08x r0=%08x r1=%08x r2=%08x r3=%08x\n",fr,n,last,v,c->gprs[15],c->gprs[14],c->gprs[0],c->gprs[1],c->gprs[2],c->gprs[3]); fprintf(stderr,"   sp=%08x r4=%08x r5=%08x stack:",c->gprs[13],c->gprs[4],c->gprs[5]); for(int q=0;q<16;q++) fprintf(stderr," %08x",core->busRead32(core,c->gprs[13]+4*q)); fprintf(stderr,"\n"); last=v; }
        }
        continue;
      }
    }
    core->runFrame(core);
    if(getenv("SAVEAT")&&fr==atoi(getenv("SAVEAT"))){ static char st[0x90000]; memset(st,0,sizeof st); int ok=core->saveState(core,st); FILE*so=fopen(getenv("SAVEOUT"),"wb"); fwrite(st,1,0x81040,so); fclose(so); fprintf(stderr,"saved %d\n",ok); }
    { static short ab[16384]; int pk2=0; for(int ch=0;ch<2;ch++){ blip_t*bl=core->getAudioChannel(core,ch); int n=blip_samples_avail(bl); if(n>16384)n=16384; n=blip_read_samples(bl,ab,n,0); if(ch==0&&getenv("AUDIOOUT")){static FILE*af=0; if(!af) af=fopen(getenv("AUDIOOUT"),"wb"); fwrite(ab,2,n,af); fflush(af);} for(int q=0;q<n;q++){int v=ab[q]<0?-ab[q]:ab[q]; if(v>pk2)pk2=v;} } if(getenv("AUDIO")&&fr%300==0) fprintf(stderr,"dbg f%d pk=%d\n",fr,pk2); if(getenv("AUDIO")&&pk2>300) fprintf(stderr,"audio f%d peak=%d\n",fr,pk2); }
    if(getenv("PCS")&&fr>=atoi(getenv("PCS"))&&fr%atoi(getenv("PCE"))==0){struct ARMCore*c=core->cpu;fprintf(stderr,"f%d pc=%08x lr=%08x sp=%08x r0=%08x\n",fr,c->gprs[15],c->gprs[14],c->gprs[13],c->gprs[0]);}
    for(int i=0;i<nr;i++) if(rams[i][0]==fr){ fprintf(stderr,"RAM f%d %08x:",fr,rams[i][1]); for(int k=0;k<rams[i][2];k++) fprintf(stderr," %02x",core->busRead8(core,rams[i][1]+k)); fprintf(stderr,"\n"); }
    for(int i=0;i<nd;i++) if(dumps[i]==fr){
      unsigned sb=core->busRead32(core,pk[i][3]==2?0x0300500c:0x03005008);
      char name[300]; sprintf(name,"%s_%05d.sb1",argv[3],fr);
      FILE*o=fopen(name,"wb");
      for(unsigned k=0;k<0x2000;k++) fputc(core->busRead8(core,sb+k),o);
      fclose(o);
    }
    for(int i=0;i<ns;i++) if(shots[i]==fr){
      char name[300]; sprintf(name,"%s_%05d.ppm",argv[3],fr);
      FILE*o=fopen(name,"wb"); fprintf(o,"P6\n%u %u\n255\n",w,h);
      for(unsigned p=0;p<w*h;p++){ unsigned px=buf[p]; fputc(px&0xff,o);fputc((px>>8)&0xff,o);fputc((px>>16)&0xff,o);} fclose(o);
    }
  }
  core->deinit(core);
  return 0;
}

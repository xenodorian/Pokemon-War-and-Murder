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
  static Ev ev[100000]; int ne=0; static int shots[1000]; int ns=0; static int dumps[1000]; int nd=0; static int pk[4000][4]; int npk=0; static int rams[200][3]; int nr=0; int total=0;
  char line[256];
  while(fgets(line,256,f)){
    int a,b,c2; char c[32];
    if(sscanf(line,"shot %d",&a)==1) shots[ns++]=a;
    else if(sscanf(line,"poke2 %d %x %x",&a,&b,&c2)==3){pk[npk][0]=a;pk[npk][1]=b;pk[npk][2]=c2;pk[npk][3]=2;npk++;}
    else if(sscanf(line,"poke %d %x %x",&a,&b,&c2)==3){pk[npk][0]=a;pk[npk][1]=b;pk[npk][2]=c2;pk[npk][3]=0;npk++;}
    else if(sscanf(line,"setbit %d %x %x",&a,&b,&c2)==3){pk[npk][0]=a;pk[npk][1]=b;pk[npk][2]=c2;pk[npk][3]=1;npk++;}
    else if(sscanf(line,"ram %d %x %d",&a,&b,&c2)==3){rams[nr][0]=a;rams[nr][1]=b;rams[nr][2]=c2;nr++;}
    else if(sscanf(line,"dump %d",&a)==1) dumps[nd++]=a;
    else if(sscanf(line,"end %d",&a)==1) total=a;
    else if(sscanf(line,"%d %x",&a,&b)==2){ev[ne].frame=a;ev[ne].keys=b;ne++;}
  }
  int keys=0,ei=0;
  for(int fr=0;fr<=total;fr++){
    while(ei<ne&&ev[ei].frame<=fr){keys=ev[ei].keys;ei++;}
    for(int i=0;i<npk;i++) if(pk[i][0]==fr){unsigned sb=core->busRead32(core,pk[i][3]==2?0x0300500c:0x03005008); if(pk[i][3]==1) core->busWrite8(core,sb+pk[i][1],core->busRead8(core,sb+pk[i][1])|pk[i][2]); else core->busWrite8(core,sb+pk[i][1],pk[i][2]);}
    core->setKeys(core,keys);
    core->runFrame(core);
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

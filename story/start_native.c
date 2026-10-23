// Start menu REPORT and REMAP natives (see tools/start_menu_fix.py). Thumb-1, no libc.
// Script scratch variables 0x8004.. live at 0x020370B8 + 2*(n-0x8000).
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
#define GSV(n) (*(volatile u16*)(0x020370b8+2*((n)-0x8000)))
// VAR_RESULT (0x800D) is not part of the contiguous block: it lives at 0x020370D0
#define RESULT (*(volatile u16*)0x020370D0)
#define KEYS() ((u16)(~*(volatile u16*)0x04000130) & 0x3ff)
#define SB1 (*(u8* volatile*)0x03005008)
#define SB2 (*(u8* volatile*)0x0300500c)
#define SAVED(id) (*(volatile u16*)(SB1+VARS_OFF+2*((id)-0x4000)))     // VARS_OFF, VAR_A, VAR_B come from the build line
#define WRITE_SECTOR ((u8(*)(u8,const void*))0x080DA5E1)               // WriteTrainerTowerSector: copies 0xFFC bytes, returns 1 on success
#define BUF ((volatile u8*)0x02039A3C)                                   // save scratch buffer + 4: the routine copies from here onto itself

// ---- controller report: sample the raw key register once per frame (from the key hook) while a start menu script runs ----
// Working memory is the save scratch buffer (4 KB, only live during a save): text first, then the sample state at +0x400.
struct St { u16 mode, done, run, n, quiet, wait, idle, tlen, ca; u16 raw[150]; u16 map[150]; };
#define ST ((volatile struct St*)(0x02039A3C + 0x400))
static u16 mapped(u16 k);
static u16 low(u16 k){ return k & (u16)(-k); }

static void ch(char c){ if(ST->tlen < 0x3F0) BUF[ST->tlen++] = c; }        // the text may never reach the sample state at +0x400
static void put(const char *s){ while(*s) ch(*s++); }
static void hex4(u16 v){ int i; for(i = 12; i >= 0; i -= 4){ u8 d = (v >> i) & 15; ch(d < 10 ? '0' + d : 'A' + d - 10); } }
static void dec(u16 v){
    u16 h = 0, t = 0; int on = 0;
    while(v >= 100){ v -= 100; h++; }
    while(v >= 10){ v -= 10; t++; }
    if(h){ ch('0' + h); on = 1; }
    if(on || t) ch('0' + t);
    ch('0' + v);
}
static void names(u16 v){
    static const char *const nm[10] = {"A", "B", "SELECT", "START", "RIGHT", "LEFT", "UP", "DOWN", "R", "L"};
    u16 i, any = 0;
    ch('('); for(i = 0; i < 10; i++) if(v & (1 << i)){ if(any) ch('+'); put(nm[i]); any = 1; }
    if(!any) put("none"); ch(')');
}
static void rle(volatile u16 *a, u16 n){
    u16 i = 0, runs = 0;
    while(i < n){
        u16 j = i; while(j < n && a[j] == a[i]) j++;
        if(runs == 10){ put(",..."); return; }
        if(runs) ch(',');
        hex4(a[i]); ch('*'); dec(j - i); runs++; i = j;
    }
}

// one sample per frame while a script holds the keys (0x8009 = 0xC0DE); k = raw pressed keys this frame
static void rec(u16 k){
    volatile struct St *s = ST;
    if(s->done || s->mode > 4 || s->n >= 150) return;      // also ignores garbage left in the scratch buffer
    if(s->mode == 1){ if(k) s->quiet = 0; else s->quiet++; if(++s->wait >= 300 || s->quiet >= 20) s->done = 1; }
    else if(s->mode == 2){ s->idle |= k; if(++s->n >= 60) s->done = 1; }
    else if(s->mode == 4){          // REMAP: the lowest pressed key wins; for B the key already chosen for A is ignored (n = 1 when it was pressed)
        u16 use = s->run ? (k & ~s->ca) : k, p = low(use);
        if(s->run && (k & s->ca)) s->n = 1;
        if(p){ s->idle = p; s->done = 1; }
        else if(++s->wait >= 1800){ s->idle = 0; s->done = 1; }
    }
    else if(s->mode == 3){
        if(!s->run){ if(k) s->run = 1; else if(++s->wait >= 1800) s->done = 1; }
        if(s->run){
            s->raw[s->n] = k; s->map[s->n] = mapped(k); s->n++;
            if(k) s->quiet = 0; else s->quiet++;
            if(s->quiet >= 20 || s->n >= 150) s->done = 1;
        }
    }
}
static void arm(u16 mode){ volatile struct St *s = ST; s->mode = mode; s->done = 0; s->run = 0; s->n = 0; s->quiet = 0; s->wait = 0; s->idle = 0; }
void kn_settle(void){ arm(1); }        // wait until no key has been held for 20 frames (at most 300 frames)
void kn_idle(void){ arm(2); }          // 60 frames with the hands off
void kn_rec(void){ arm(3); }           // wait for a first key, then record until 20 quiet frames
void kn_poll(void){ RESULT = ST->done; }
void kn_off(void){ volatile struct St *s = ST; s->mode = 0; s->done = 1; s->ca = 0; }     // REMAP start: no sampling, whatever the scratch buffer held
void kn_pickA(void){ arm(4); ST->run = 0; }
void kn_pickB(void){ arm(4); ST->run = 1; }
// RESULT = 1 when a key was chosen (0x8004 = that key); 0 on timeout (30 seconds); 2 on timeout when only the key already chosen for A was pressed
void kn_got(void){ volatile struct St *s = ST; GSV(0x8004) = s->idle; RESULT = s->idle ? 1 : (s->n ? 2 : 0); if(s->run == 0) s->ca = s->idle; }
// start of the report: header lines
void kn_begin(void){
    u32 i; u8 mode = SB2 ? SB2[19] : 0xFF;
    for(i = 0; i < 0xFFC; i++) BUF[i] = 0;
    put("PWAMRPT v2\n");
    put("key bits: 0001=A 0002=B 0004=SELECT 0008=START 0010=RIGHT 0020=LEFT 0040=UP 0080=DOWN 0100=R 0200=L\n");
    put("game: button mode="); hex4(mode); put(" remap A="); hex4(SB1 ? SAVED(VAR_A) : 0); put(" B="); hex4(SB1 ? SAVED(VAR_B) : 0); ch('\n');
}
void kn_idlefin(void){ put("idle (hands off, 60 frames) keys="); hex4(ST->idle); ch('\n'); }
static void fin(char which){
    volatile struct St *s = ST;
    u16 i, first = 0, uni = 0, held = 0;
    for(i = 0; i < s->n; i++){ if(!first) first = s->raw[i]; uni |= s->raw[i]; if(s->raw[i]) held++; }
    ch(which); put(" press: ");
    if(!s->run){ put("no key seen in 30 seconds\n"); return; }
    put("first="); hex4(first); names(first); put(" union="); hex4(uni); names(uni); put(" frames_held="); dec(held); put(" total_frames="); dec(s->n);
    put("\n  raw (hardware) "); rle(s->raw, s->n);
    put("\n  seen by game   "); rle(s->map, s->n); ch('\n');
}
void kn_finA(void){ fin('A'); }
void kn_finB(void){ fin('B'); }
// the report text is in the buffer: flash it to sector 31, VAR_RESULT = 1 on success
void kn_write(void){ RESULT = WRITE_SECTOR(31, (const void*)BUF) == 1; }

// The key chosen for A (ra) and for B (rb) take the A and B places; the old A and B keys move into the places they leave.
// Any pair of different keys works, including the old A key as B and the old B key as A (a swap) or one key out of the three-way cycle.
static int one(u16 v){ return v && v <= 0x3ff && !(v & (v - 1)); }
static u16 remap(u16 k, u16 ra, u16 rb){
    u16 out, d[2], f[2]; int nd = 0, nf = 0, i;
    if(!one(ra)) ra = 1;
    if(!one(rb)) rb = 2;
    if(ra == rb || (ra == 1 && rb == 2)) return k;
    out = k & ~(u16)(3 | ra | rb);
    if(k & ra) out |= 1;
    if(k & rb) out |= 2;
    if(ra != 1 && rb != 1) d[nd++] = 1;
    if(ra != 2 && rb != 2) d[nd++] = 2;
    if(ra != 1 && ra != 2) f[nf++] = ra;
    if(rb != 1 && rb != 2) f[nf++] = rb;
    for(i = 0; i < nd && i < nf; i++) if(k & d[i]) out |= f[i];
    return out;
}
// the key hook: k = pressed keys; the chosen keys take the A and B places, then the old A/B swap option
static u16 mapped(u16 k){
    u8 *s1 = SB1, *s2 = SB2;
    if(s1) k = remap(k, SAVED(VAR_A), SAVED(VAR_B));
    if(s2 && s2[19] == 3){ u16 t = k & 3; k = (k & ~(u16)3) | ((t & 1) << 1) | (t >> 1); }
    return k;
}
u16 kn_map(u16 k){
    if(GSV(0x8009) == 0xC0DE){ rec(k); return 0; }   // a start menu script is reading the raw keys: the game itself sees none (L and R would open HELP)
    return mapped(k);
}

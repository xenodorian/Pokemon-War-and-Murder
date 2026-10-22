// Liberty shop prices, JRA bless/threaten memory, signed liberty, shackle for captains and Nero.
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef short s16;
#include "liberty_gen.h"

#define SB1 (*(u8* volatile*)0x03005008)
#define GSV(n) (*(volatile u16*)(0x020370b8 + 2 * (n)))
#define OPP (*(volatile u16*)0x020386ae)
#define STR ((u8*)0x02021cd0)
#define TRAINERS 0x08798790
#define LIB_VAR 0x40AC
#define GVARS ((const u16*)GVARS_ADDR)
#define JIDS ((const u16*)JIDS_ADDR)
#define OLD_SCALE ((u32(*)(u32))(OLD_SCALE_ADDR | 1))
#define OLD_SHOOT ((void(*)(void))(OLD_SHOOT_ADDR | 1))
#define OLD_KC ((void(*)(void))(OLD_KC_ADDR | 1))
#define OLD_LIBTXT ((void(*)(void))(OLD_LIBTXT_ADDR | 1))
#define OLD_GW ((void(*)(void))(OLD_GW_ADDR | 1))
#define GIVE ((u8(*)(u16, u8, u16, u32, u32, u8))(0x080a011c | 1))

static u16* sv(u32 id) { return (u16*)(SB1 + 0x1000 + ((id - 0x4000) << 1)); }
static u16* bitvar(u32 bit) { return sv(GVARS[bit >> 4]); }
static int bit_get(u32 bit) { return (*bitvar(bit) >> (bit & 15)) & 1; }
static void bit_set(u32 bit) { *bitvar(bit) |= (u16)(1u << (bit & 15)); }
static void bit_clr(u32 bit) { *bitvar(bit) &= (u16)~(1u << (bit & 15)); }

static int jidx(u32 id) {
    for (int i = 0; i < NJ; i++) if (JIDS[i] == id) return i;
    return -1;
}

/* threatened bits: one per JRA index, in mystery-gift vars the story never touches */
static const u16 TVARS[6] = {0x40B6, 0x40B7, 0x40B8, 0x40B9, 0x40BA, 0x40BB};
static int t_get(int j) { return (*sv(TVARS[j >> 4]) >> (j & 15)) & 1; }
static void t_set(int j) { *sv(TVARS[j >> 4]) |= (u16)(1u << (j & 15)); }
static void t_clr(int j) { *sv(TVARS[j >> 4]) &= (u16)~(1u << (j & 15)); }

static s16 lib_get(void) { return (s16)*sv(LIB_VAR); }
static void lib_set(int v) {
    if (v > 9999) v = 9999;
    if (v < -9999) v = -9999;
    *sv(LIB_VAR) = (u16)(s16)v;
}

static u32 divu(u32 n, u32 d) {
    u32 q = 0, r = 0;
    for (int i = 31; i >= 0; i--) {
        r = (r << 1) | ((n >> i) & 1);
        if (r >= d) { r -= d; q |= 1u << i; }
    }
    return q;
}

/* blessed bit for JRA index j lives at g_vars bit 929+j (928 is the last kill bit) */
#define BBIT(j) (929u + (u32)(j))

/* GSV4: 0 fresh, 1 threatened, 2 blessed. GSV5: 1 if they can still be shot. */
void jra_state(void) {
    int j = jidx(OPP);
    GSV(4) = 0;
    GSV(5) = 0;
    if (j < 0) return;
    int bl = bit_get(BBIT(j));
    int th = t_get(j);
    int shot = bit_get(417u + (u32)j);
    if (bl) GSV(4) = 2;
    else if (th) GSV(4) = 1;
    if (!bl && !shot) GSV(5) = 1;
}

void jra_bless_do(void) {
    int j = jidx(OPP);
    if (j < 0) return;
    bit_set(BBIT(j));
    t_clr(j);
    lib_set((int)lib_get() - 1);
}

void jra_threat_do(void) {
    int j = jidx(OPP);
    if (j < 0) return;
    if (bit_get(BBIT(j))) return;
    t_set(j);
}

/* the stock shoot refuses to climb out of a negative count (it treats the var as unsigned) */
void jra_shoot_fix(void) {
    int j = jidx(OPP);
    s16 before = lib_get();
    OLD_SHOOT();
    if (j < 0) return;
    if (lib_get() == before && before < 9999) lib_set((int)before + 1);
}

void shop_lib_on(void) { bit_set(1023); GSV(15) = 0x4C42; }
void shop_lib_off(void) { bit_clr(1023); GSV(15) = 0; }

/* map load drops a liberty-shop flag left behind by a reset mid-purchase */
void gw_load_wrap(void) {
    bit_clr(1023);
    GSV(15) = 0;
    OLD_GW();
}

/* liberty 0 is the neutral price. Above 0 is a discount, below 0 a markup. Floor 1, never free. */
u32 scale_price2(u32 price) {
    if (!bit_get(1023)) return OLD_SCALE(price);
    int L = lib_get();
    u32 pct;
    if (L >= 99) pct = 1;
    else if (L >= 0) pct = (u32)(100 - L);
    else pct = 100u + (u32)(-L);
    u32 p = divu(price * pct, 100);
    if (price && p == 0) p = 1;
    return p;
}

static const u16 CAPS[] = {15, 6, 442, 86, 460, 176, 284, 399, 24, 433, 530};
#define NCAP 11
#define SH_FLAG 0x871
static int cap_index(u16 id) {
    for (int i = 0; i < NCAP; i++) if (CAPS[i] == id) return i;
    return -1;
}
static int flag_get(u32 f) { return (SB1[0xEE0 + (f >> 3)] >> (f & 7)) & 1; }
static void flag_set(u32 f) { SB1[0xEE0 + (f >> 3)] |= (u8)(1u << (f & 7)); }

/* GSV12 = 1 when this defeated trainer may be shackled. GSV11 = 1 for the general. */
void shackle_check2(void) {
    u16 id = OPP;
    int i = cap_index(id);
    u8 cls = *(const u8*)(TRAINERS + 40u * id + 1);
    int ok = (i >= 0 && i < 10 && cls == 44) || (i == 10 && cls == 45);
    GSV(11) = (ok && i == 10) ? 1 : 0;
    GSV(12) = (ok && !flag_get(SH_FLAG + (u32)i)) ? 1 : 0;
}

void shackle_do2(void) {
    u16 id = OPP;
    int i = cap_index(id);
    const u8* t = (const u8*)(TRAINERS + 40u * id);
    u32 n = t[32];
    u32 sz = (t[0] & 1) ? 16 : 8;
    const u8* last = (const u8*)(*(const u32*)(t + 36)) + sz * (n - 1);
    u8 res = 2;
    if (i >= 0 && n) res = GIVE(*(const u16*)(last + 4), last[2], 0, 0, 0, 0);
    if (i >= 0) {
        flag_set(SH_FLAG + (u32)i);
        lib_set((int)lib_get() + 5);
    }
    GSV(0xD) = res;
    GSV(11) = (i == 10) ? 1 : 0;
}

static u8* emit_num(u8* d, int v) {
    if (v < 0) { *d++ = 0xAE; v = -v; }
    u8 tmp[8];
    int n = 0;
    u32 x = (u32)v;
    do { tmp[n++] = (u8)(0xA1 + (x - divu(x, 10) * 10)); x = divu(x, 10); } while (x);
    while (n) *d++ = tmp[--n];
    return d;
}

static int prefix_at(const u8* p) {
    for (int i = 0; i < LIB_PREFIX_LEN; i++) if (p[i] != LIB_PREFIX[i]) return 0;
    return 1;
}

void kc_show_wrap(void) {
    OLD_KC();
    int L = lib_get();
    if (L >= 0) return;
    u8* hit = 0;
    for (u8* p = STR; p < STR + 180 && *p != 0xFF; p++) {
        if (prefix_at(p)) { hit = p + LIB_PREFIX_LEN; break; }
    }
    if (!hit) return;
    u8* end = hit;
    while (*end != 0xFE && *end != 0xFB && *end != 0xFF) end++;
    u8 tail[96];
    int tn = 0;
    for (u8* q = end; tn < 95; q++) { tail[tn++] = *q; if (*q == 0xFF) break; }
    u8* o = emit_num(hit, L);
    for (int i = 0; i < tn; i++) *o++ = tail[i];
}

void lib_text_wrap(void) {
    OLD_LIBTXT();
    int L = lib_get();
    if (L >= 0) return;
    u8* o = emit_num(STR, L);
    *o = 0xFF;
}

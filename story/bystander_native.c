// Bless / threaten on a bystander, once. No item. Blessing raises reputation.
// Threatening pays 50..200 and lowers reputation. The bit lives in SaveBlock1 unused_348C.
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
#include "bystander_gen.h"

#define SB1 (*(u8* volatile*)0x03005008)
#define GSV(n) (*(volatile u16*)(0x020370b8 + 2 * (n)))
#define Random ((u32(*)(void))(0x08044ec8 | 1))
#define REP_CALC ((u32(*)(void))(REP_CALC_ADDR))
#define BLESS_VAR 0x40F4
#define VAR_REPADJ 0x40E9
#define BITS 0x348C

static u16* sv(u32 id) { return (u16*)(SB1 + 0x1000 + ((id - 0x4000) << 1)); }

static int bit_get(int i) { return (SB1[BITS + (i >> 3)] >> (i & 7)) & 1; }
static void bit_set(int i) { SB1[BITS + (i >> 3)] |= (u8)(1u << (i & 7)); }

static int find(void) {
    u8 g = SB1[4], m = SB1[5], id = (u8)GSV(15);
    for (int i = 0; i < BY_N; i++) {
        if (BY_ENT[i * 3] == g && BY_ENT[i * 3 + 1] == m && BY_ENT[i * 3 + 2] == id)
            return i;
    }
    return -1;
}

/* GSV8 = 1 when this person was already blessed or threatened (menu shows Leave only). */
void by_gate(void) {
    int i = find();
    GSV(8) = (i < 0 || bit_get(i)) ? 1 : 0;
}

void by_bless(void) {
    int i = find();
    if (i < 0 || bit_get(i)) return;
    bit_set(i);
    u16* b = sv(BLESS_VAR);
    if (*b < 999) (*b)++;
    REP_CALC();
}

void by_threat(void) {
    int i = find();
    if (i < 0 || bit_get(i)) return;
    bit_set(i);
    u16* adj = sv(VAR_REPADJ);
    if (*adj < 500) *adj = 1000;
    if (*adj > 500) (*adj)--;
    REP_CALC();
    u32 rnd = Random();
    u32 amt = 50u + ((rnd * 151u) >> 16);
    u32* money = (u32*)(SB1 + 0x290);
    if (*money > 999999u - amt) *money = 999999u;
    else *money += amt;
    GSV(0) = (u16)amt;
}

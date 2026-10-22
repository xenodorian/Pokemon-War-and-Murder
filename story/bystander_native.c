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
#define CUR  (BITS + 396)
#define MARK (BITS + 399)
#define MARKV 0xA5

static u16* sv(u32 id) { return (u16*)(SB1 + 0x1000 + ((id - 0x4000) << 1)); }

static int bit_get(int i) { return (SB1[BITS + (i >> 3)] >> (i & 7)) & 1; }
static void bit_set(int i) { SB1[BITS + (i >> 3)] |= (u8)(1u << (i & 7)); }

/* Old saves have garbage in this unused block, which read as "already used". */
static void ensure(void) {
    if (SB1[MARK] == MARKV) return;
    for (int i = BITS; i < MARK; i++) SB1[i] = 0;
    SB1[MARK] = MARKV;
}

/* The dialogue can overwrite last-talked. The wrapper records who this is first. */
void by_note(void) {
    ensure();
    u16 gm = GSV(1);
    SB1[CUR] = (u8)(gm >> 8);
    SB1[CUR + 1] = (u8)gm;
    SB1[CUR + 2] = (u8)GSV(0);
}

static int find(void) {
    u8 g = SB1[CUR], m = SB1[CUR + 1], id = SB1[CUR + 2];
    for (int i = 0; i < BY_N; i++) {
        if (BY_ENT[i * 3] == g && BY_ENT[i * 3 + 1] == m && BY_ENT[i * 3 + 2] == id)
            return i;
    }
    return -1;
}

/* GSV8 = 1 only after this person was blessed or threatened. */
void by_gate(void) {
    ensure();
    int i = find();
    GSV(8) = (i >= 0 && bit_get(i)) ? 1 : 0;
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

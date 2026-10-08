// Shared kill counting: shot trainers whose defeat flag is still set, plus officers shot (counter variable), capped at 999.
#ifndef KILLCOUNT_H
#define KILLCOUNT_H
#define KC_SB1 (*(u8* volatile*)0x03005008)
#define KC_POL_KILLS 0x40F7
#define KC_MAX 999
static inline u16* kc_var(u32 id){ return (u16*)(KC_SB1+0x1000+((id-0x4000)<<1)); }
static inline u16* kc_gvar(u32 bit){ return (u16*)(KC_SB1+0x1000+((g_vars[bit>>4]-0x4000)<<1)); }
static inline int kc_flag(u32 f){ return (KC_SB1[0xEE0+(f>>3)]>>(f&7))&1; }
static inline u32 kc_bit_kills(void){
    u32 n=0;
    for(u32 r=0;r<NIDS;r++) if(((*kc_gvar(512+r))>>((512+r)&15))&1 && kc_flag(0x500+g_ids[r])) n++;
    return n;
}
static inline u32 kc_total(void){ u32 n=kc_bit_kills()+*kc_var(KC_POL_KILLS); return n>KC_MAX?KC_MAX:n; }
#endif

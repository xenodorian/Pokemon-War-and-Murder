// One native: start the red screen fade when the palette fade is idle. VAR_RESULT = 1 if it started, 0 if a fade was still running.
// The death script calls it in a loop, because the fade from the lost battle is still running when the death script begins and
// BeginNormalPaletteFade refuses to start while a fade is active.
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
#define FADE ((u32(*)(u32,signed char,u8,u8,u16))(0x08070588|1))
void death_fade_try(void){
    *(volatile u16*)0x020370d0 = (u16)(FADE(0xFFFFFFFFu,0,0,16,0x001F) ? 1 : 0);
}

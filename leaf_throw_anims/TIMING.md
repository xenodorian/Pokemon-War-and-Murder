# Timing data

Units are game frames at 60 fps (assumed, not verified). t is time since the throw animation started. GIFs were sampled every 2 frames and shown at 30, 30, 40 ms per frame, repeating.

## Leaf throw frames
Drawn at screen position (48, 48), 64x64 each.

| Frame file | Starts at t | Lasts | Notes |
|---|---|---|---|
| leaf_frame1 | 0 | 20 | wind-up |
| leaf_frame2 | 20 | 6 | |
| leaf_frame3 | 26 | 6 | arm extended, ball release |
| leaf_frame4 | 32 | 24 | follow-through |
| leaf_frame0 | 56 | 1 | idle, then hold |

## Moves
"Effect start" is the first frame where the move's effect appears on screen. The throw is positioned so this lands on the t shown.

| Move | Engine effect | Throw frame at effect start | Effect start at t | Effect length | Notes |
|---|---|---|---|---|---|
| Ball Throw | Tackle (target shake at start, blink after) | ball lands | 44 | about 55 frames | Ball sprite flies t=26 to 44 from (102, 74) to (170, 50) with a 34 px arc. Text box shows the full name for the whole clip |
| Slap | Tackle | frame 4 | 32 | about 60 frames | no ball; shake first, then target blink about 30 frames later |
| Barrage | Barrage (red balls fly in, hit) | frame 3 | 26 | about 100 frames | no ball |
| Egg Bomb | Egg Bomb (egg fly, explosion) | frame 3 | 26 | about 65 frames | no ball; recording has a second window after the first that is not used |
| Shadow Ball | Shadow Ball (screen tint, ball, impact) | frame 3 for the ball | screen effect first | screen effect about 54 frames before the ball appears, ball flight about 40 frames | the throw starts when the ball appears, so frame 3 is 26 frames after that. Clip ends right after impact |
| Swift | Swift (star swarm) | frame 3 | 26 | about 60 frames | no ball |
| Spike Cannon | Spike Cannon (needle volley) | frame 3 | 26 | about 35 frames | no ball |
| Sludge Bomb | Sludge Bomb (arc, pink tint) | frame 3 | 26 | about 75 frames | no ball; clip ends before the tint fades |

Notes:
- Ball Throw's effect start is not frame 3 or 4 (it was timed to the ball landing).
- The effects are the engine's own move animations, recorded on a test battle. They launch from the attacker's battler position, not Leaf's hand.
- The effect lengths are approximate, read from recorded frame ranges, not exact.

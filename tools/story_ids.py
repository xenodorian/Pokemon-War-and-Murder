"""Flag, var, species, item and trainer ids of the Shinigami / Yveltal / Nero storyline. One place so no script reuses an id.
Flags 0x4EF..0x4F6 belong to the opening (cry_open.py); 0x4D0..0x4EE are the spirit quests; 0x4A7..0x4AD, 0x4C0..0x4CB are older scenes.
Vars 0x40EC..0x40F0 are unused vanilla vars (0x4090.. is the robbery pool, 0x40E6..0x40EB and 0x40F1 are vanilla daily vars)."""
# ---- flags (0x4F7..0x4FF)
F_FREED=0x4F7          # Shinigami is free (set when Max opens his cell in base 1)
HIDE_STORY=0x4F8       # crime-scene objects (bodies, feathers, story officers) are hidden while this is SET; map transition scripts keep it equal to NOT F_FREED
HIDE_CELL=0x4F9        # Shinigami in his cell is hidden once this is SET (set when freed)
F_SCROLL=0x4FA         # Max carries the scroll
HIDE_ANNE=0x4FB        # Anne at the Pewter base door is hidden while SET (cleared by the news scene)
F_FATHER_ALIVE=0x4FC   # father revived, the FATHER team box and the father NPC exist
F_YV_RISEN=0x4FD       # Yveltal has been woken at the Tower grave
F_ENDED=0x4FE          # the epilogue has played
F_CAPTAIN_DOWN=0x4C0   # base 1 cleared flag (existing FLAG_CLEARED0): soldiers gone, Captain beaten
# ---- vars
VAR_STORY=0x40EC       # 0 start, 1 left home, 2 Shinigami freed (go outside), 3 choice made, 4 Yveltal resolved, 5 Nero beaten, 6 epilogue done
VAR_REP=0x40ED         # reputation + 100 (0..200), 100 = neutral
VAR_NERO=0x40EE        # 0 not beaten, 1 arrested, 2 executed, 3 crowned
VAR_YV=0x40EF          # 0 none, 1 chosen (scroll spoken), 2 tamed (caught), 3 beaten, 4 Max fell
VAR_CHOICE=0x40F0      # 0 none, 1 father, 2 yveltal
# ---- species slots (see build.py: 252 TAUNTER, 253 SLIMOSAUR)
SP_YVELTAL=254
SP_MAX=255
# ---- epilogue
TITLE_KIND,TITLE_KINGSLAYER,TITLE_GODSLAYER,TITLE_BLOODY=1,2,3,4

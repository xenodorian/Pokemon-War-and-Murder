# Shinigami / Yveltal / Nero storyline (design decisions, 2026-10-13)

Written for the unattended import of CryMon's main story into War and Murder. Where the request left room I chose the simplest thing that works on the FireRed engine; each choice is marked DECISION.

## Flow
1. New game: start at home (done). Father is sick in bed. Max takes SANDSHREW, Mason and Anne outside (done).
2. First JRA base (Pewter, map 2,69): SHINIGAMI is locked up in the Captain's room. Before the Captain is beaten he only speaks through his cell (talk script). After the Captain is beaten (flag 0x4C0), talking to him frees him: Max gets the SCROLL (a key item), a SPELL TAG and TM30, he walks off (hidden), F_FREED set, VAR_STORY = 2.
3. The crime scenes (bodies, black feathers, story officers in Pallet, Viridian, Pewter, Cerulean, Vermilion) and the Lavender plaza shoot-out are hidden until F_FREED (Shinigami is the killer; they start once he is out). The generated patrol police (Kill Count based) are unchanged.
4. Max leaves the base: ANNE is waiting outside and tells her that her father has died (map script on frame while VAR_STORY == 2). The CHOICE: unroll the scroll over her father (FATHER) or speak YVELTAL's name (YVELTAL).
   - FATHER: cut to home, father stands up and joins her. DECISION: the engine has a fixed 6-slot party, so "+6 Pokemon slots" is a second team of 6 kept in PC box 14 ("FATHER") that Max swaps with her party at will (father NPC at home and a Start menu entry), not a 12 slot party.
   - YVELTAL: the scroll burns, the runes point to the grave at the top of the Pokemon Tower (Lavender). DECISION: Yveltal wakes there when Max walks up to the grave with the scroll and fights it at Lv 60: caught = tamed, knocked out = Godslayer, Max blacks out = Max The Bloody (game over epilogue).
5. The ten JRA bases continue as before. DECISION: the last base's General is NERO (name, battle picture, dialogue). After beating him: ARREST (trial), EXECUTE, or be CROWNED.
6. Epilogue cards chosen from: Nero outcome, father alive or not, Yveltal outcome, title (Max The Kind, Kingslayer, Godslayer, Max The Bloody) and reputation.
7. Reputation: -100..+100 stored as VAR_REP = value+100. Kills lower it, blessings and mercy raise it. DECISION: shop prices scale with it (1% per point off at good rep, 5% per point on at bad rep, refuse at -100, free at +100 is not implemented because free items would break PokeMart accounting; instead the price floors at 1).
8. Max with no Pokemon: she fights as herself (species MAX, Lv 1, Caterpie stats, only TACKLE, CryMon sprite).

## Ids
See tools/story_ids.py. Species 254 YVELTAL, 255 MAX.

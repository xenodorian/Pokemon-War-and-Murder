# Spec: Max, the Viridian arrest, soldier fights, rewards, and party death rules

Status: written 2026-10-16 from the user's instructions in the working session. Items marked DECISION were not stated by the user; the stated default is what gets built unless the user changes it. Plain text only (no em dashes, no emoji).

## 1. Cast
- LEAF: the player. Female. Save name LEAF; rival MASON.
- MAX: a separate child NPC. CryMon refers to Max as "she" (content/dialogue.json), so Max is female.
  - DECISION: Max uses pret OBJ_EVENT_GFX_LITTLE_GIRL (17). Anne also uses 17 (already in the build). Two children with the same sprite is acceptable; change Max to LITTLE_BOY (16) if the user prefers.
- SOLDIER 1 and SOLDIER 2: two Weeping Army (JRA) soldiers. Use the JRA soldier trainer sprite already in the ROM (grunt-type).
- Party: LEAF's team in the Viridian fight is LEAF's own party (the normal party). Max is a battle partner with his/her own party (below).

## 2. Location and trigger
- Town: VIRIDIAN CITY. Map id not yet verified. Find it with tools/mapinfo.py before scripting.
- Trigger: the first time LEAF walks into Viridian City (a map-enter script with a one-time flag F_ARREST).
- Scene is played where LEAF can see it. The cutscene does not take control away from the player after the walk.

## 3. Arrest sequence (in order)
1. Max enters from the north side of town, walking east to west across the screen, between SOLDIER 1 (leading) and SOLDIER 2 (following). Max is in the middle, escorted.
2. All three walk across the screen together, then stop in place at the stop tile (DECISION (see section 12, item 5): tile chosen from the Viridian map at build time).
3. Max says: "Let me go! Pikachu, I choose you!"
4. The three stop. The walk ends. Nothing else happens until the player interacts.
5. Interaction with MAX or either SOLDIER (talk, or walking into them) starts the DOUBLE BATTLE. There is no escape option.

## 4. Double battle
- Player side: LEAF plus MAX (battle partner). MAX has ONLY one Pokemon: PIKACHU, level 10.
- Enemy side: SOLDIER 1 and SOLDIER 2, both in the battle.
  - SOLDIER 1: TOTODILE, CYNDAQUIL, CHIKORITA, all level 5. (The user wrote "tododile"; the species is Totodile.)
  - SOLDIER 2: SQUIRTLE, CHARMANDER, BULBASAUR, all level 5.
- LEAF's side uses her normal party. If her party is empty, the stand-in rule applies (see section 7).
- No white-out on a loss (section 5).

## 5. Battle outcomes
### 5a. Player and MAX WIN
- After the battle, MAX says (SOLDIER 2 is still alive at this point):
  - MAX notices SOLDIER 2's Kanto Pokemon and says: "A traitor and a coward. You fight with Kanto POKeMON, but you serve Johto."
  - RESOLVED: the user's text said SOLDIER 2 used Kanto Pokemon but was called a traitor for "defecting to Johto", which is inconsistent. The line above keeps the intent (traitor and coward for defecting) and matches his team.
- SOLDIER 2 says: "A child could never understand the burdens of a soldier." Then SOLDIER 2 shoots himself. He falls and leaves a blood splatter on the ground.
- SOLDIER 1 says: "Arceus in heaven, he actually shot himself! I have to alert the captain!" and walks off screen.
- MAX says: "A worm returning to the dirt. There's nothing here to mourn. Thank you for saving me. I have more battles to fight. But as an expression of gratitude, here, take this." MAX gives LEAF the XP SHARE item (FireRed ITEM_EXP_SHARE).
- The gun SOLDIER 2 used (it drops at the blood splatter) can be picked up by LEAF. The gun is in the repo's gun/ mod (see gun.py).

### 5b. Player and MAX LOSE
- The loss does NOT white out LEAF (no Pokemon Center trip for this fight).
- After the exchange (same traitor/coward line from MAX, as above), SOLDIER 2 says: "A child could never understand the burdens of a soldier." Then SOLDIER 2 shoots BOTH MAX and LEAF dead.
- LEAF and MAX both die. Afterlife rule (section 6) decides heaven or hell for LEAF. MAX also goes to heaven or hell, comes back to the screen once, and then STAYS DEAD: MAX is a blood splatter on the ground for the rest of the game.
- DECISION: LEAF's death in this fight follows the same run mode rule as any other death (section 6). In a normal run she is then taken to the Pokemon Center as a white-out would. This is the one exception to "no white-out". In a playable-Pokemon run she dies permanently.

## 6. Death, afterlife, and run mode
- Afterlife destination: reputation rule already in the ROM (tools/story_yveltal.py, VAR_REP 0x40E7, value = reputation + 100). VAR_REP >= 100 goes to HEAVEN (Arceus); below 100 goes to HELL (Giratina). Same rule as being shot.
- Run mode: DECISION: a run is either NORMAL or PLAYABLE. The choice is made once, in the house, on the first wake-up before LEAF leaves the house, as a YES/NO box. Flag F_PLAYABLE records it.
  - NORMAL: losing a battle white-outs to the Pokemon Center as usual.
  - PLAYABLE: losing a battle where LEAF is in the fight means death: heaven or hell by reputation, permanent for that run.

## 7. Party model (needed for the PC prompt and for LEAF in fights)
- Current ROM: LEAF is a stand-in ONLY when the party is completely empty. She is not a party member.
- For the PC prompt the requirement is that LEAF is a party member, so the party can be full with her in it.
- DECISION: LEAF becomes a permanent party member (species 255 "LEAF", Hitmonchan stats) the moment LEAF is given her first Pokemon by Oak or the Sandshrew shelf. She occupies one of the 6 party slots while she is in the party.
- DECISION: with LEAF in the party, the player has 5 other Pokemon. "Six Pokemon including themselves" in the user's spec means: the party is full (6 slots) counting LEAF.

## 8. PC-or-withdraw prompt
- Trigger: a catch (or a gift) happens while the party is full (6 slots, LEAF included).
- Prompt (YES/NO style, two options, DECISION: keep the user's wording):
  - "Send [POKEMON] to the PC?" YES: the new Pokemon goes to the PC box.
  - NO: "Remove LEAF from combat?" YES: LEAF is withdrawn from the party (she stays in the box; she is not lost). NO: back to the prompt.
- When LEAF is withdrawn, the party has one free slot for the catch.

## 9. Max as a party partner after the arrest
- MAX joins the party as a partner for the story fights only when called: double battles, plus the later battles the user specified (Raichu instead of Pikachu later in the game).
- MAX does not take a party slot of LEAF's.
- DECISION: MAX's later double battles are placed at the story points listed in CURRENT_WORK; no new trigger is designed here.

## 10. Data needed (to build)
- Trainer records: 2 soldier trainers (double battle, two parties), 1 Max trainer (party: Pikachu Lv 10; Raichu later).
- Text: all lines in sections 3 to 5 in story_assets/text/story_text.json (keys to be added).
- Scripts: map-enter script (Viridian, flag F_ARREST), arrest walk script, battle start (double battle), outcome scripts (win, lose), death scripts (heaven/hell, MAX blood splatter), XP Share gift, gun pickup (object), PC prompt (party full on catch), run-mode prompt (house).
- Flags: F_ARREST, F_PLAYABLE, F_MAX_DEAD, F_GUN_TAKEN. Choose free flag ids in tools/story_ids.py.

## 11. Acceptance checks (must pass before a step is called done)
- Arrest: walk into Viridian once; the escort plays; Max says the line; the three stop; interaction starts a double battle.
- Battle: LEAF + MAX vs two soldiers (teams above); no white-out on loss.
- Win: traitor line; soldier 2 shoots himself and leaves a splatter; soldier 1 leaves; MAX gives XP SHARE; gun can be picked up.
- Loss: soldier 2 shoots both; MAX dies, comes back once, stays a splatter; LEAF to heaven/hell by VAR_REP; NORMAL run goes to the Pokemon Center; PLAYABLE run is permanent.
- PC prompt: with a full party (LEAF in it), a catch prompts PC or withdraw.
- Build: apply_all.sh rebuilds; newgame_test passes; battle_test passes.

## 12. Decisions (all resolved 2026-10-16; change here if the user disagrees)
1. Soldier 2 line: resolved as in 5a (traitor for serving Johto while fighting with Kanto POKeMON).
2. Max's sprite: LITTLE_GIRL (17). Resolved.
3. Run mode choice point: the house, first wake-up, YES/NO. Resolved.
4. LEAF as a permanent party member: from her first Pokemon. Resolved.
5. Arrest stop tile: set at build time from the Viridian map (tools/mapinfo.py). An implementation detail, not a user decision.
6. Hyperpunch type: Fighting (matches the other punches). Resolved; the user did not object.
7. CryMon names (Calder, Weeping Army, Prison) in Mason's dialogue: kept as the user asked. Resolved.

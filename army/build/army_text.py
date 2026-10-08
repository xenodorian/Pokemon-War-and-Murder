"""Dialogue and names for the JRA bases. Every base soldier / patrol / guard line is picked deterministically per trainer from the pools below,
the Captains have their own names. Text only uses characters the game font has (no '#', no straight quotes)."""
import random
JOHTO=['GOLDENROD','ECRUTEAK','OLIVINE','CHERRYGROVE','VIOLET CITY','AZALEA TOWN','NEW BARK','CIANWOOD','MAHOGANY TOWN','BLACKTHORN','MT. SILVER','LAKE OF RAGE','ILEX FOREST','UNION CAVE']
SURNAMES=['BELL','CROSS','DRAKE','EVANS','HOLT','REYES','FINCH','VOSS','CRANE','DALE','FROST','GRANT','HALE','IVES','JARVIS','KNOX','LANE','MORSE','NASH','OAKES','PIKE','QUILL','RAND','SHAW','TATE','URBAN','VANCE','WADE','YORK','ZANE','ABBOT','BRAY','COLE','DEAN','ELLIS','FOX','GRAY','HOOK','INGE','JUDD','KIRK','LOWE','MACK','NOLAN','ORR','PRICE','REED','SLADE','TRENT','WYATT',
         'ARCHER','BOWEN','CASTLE','DRAPER','EASTON','FORD','GRIFFIN','HAYES','JENNER','KEMP','LOGAN','MASON','NEWTON','OSBORN','PORTER','RIVERS','SUTTON','TURNER','WALSH','YATES',
         'BOONE','CLAY','DUNN','EAMES','FLINT','GAGE','HART','IRVIN','KANE','LOCKE','MARS','NOBLE','OWENS','PERRY','RHYS','STONE','THAYER','UPTON','VAIL','WEBB']
CAPTAIN={'PALLET':'HAWTHORN','VIRIDIAN':'KESTREL','PEWTER':'MARLOW','CERULEAN':'VANCE','VERMILION':'DRAYTON','LAVENDER':'CORVIN','CELADON':'ASHFORD','SAFFRON':'THORNE','FUCHSIA':'BRANDT','CINNABAR':'LOCKHART'}
BASE_INTRO=[
 "Intruder! This base belongs to the Johto Revolutionary Army!\n\nPEACE THROUGH CONQUEST!",
 "KANTO's age of weakness is over. We march from {J} to bring you peace.\n\nThrough conquest!",
 "I walked from {J} to {CITY} to teach you obedience. Surrender!",
 "Halt, rebel! Every stone in {CITY} belongs to the Revolution!",
 "You dare enter JRA BASE NO. {N}? The Revolution will remember your face.",
 "Johto's flag will fly over {CITY} by dawn. Stand aside or fall.",
 "My POKéMON trained in {J}. Yours look soft. Prepare yourself!",
 "Bow to the Revolution, KANTO scum!\n\nPEACE THROUGH CONQUEST!",
 "The old League failed you. The JRA will not. Surrender your POKéMON!",
 "Papers! Nobody walks through BASE NO. {N} without the Revolution's blessing."]
BASE_DEFEAT=[
 "My POKéMON... {J} forgive me.","Tch... the flames of {J} still burn.","Impossible. We trained under MT. SILVER itself!","The Revolution... will not end with me.",
 "I lost?! The Captain will hear of this.","Argh! {J} will send more of us.","How? We are the future of KANTO!","Peace... through... conquest..."]
BASE_AFTER=[
 "CAPT. {CAP} will crush you. Long live Johto!","Beat me, and a hundred more will come from {J}.","Surrender now. Peace through conquest, brat.","JOHTO wins in the end. It always does.",
 "You only delay the inevitable. {CITY} is ours.","Go on, then. The Captain is waiting.","Enjoy it while it lasts. The Revolution never sleeps.","One day KANTO will thank us."]
PAT_INTRO=[
 "Papers, citizen! The Johto Revolutionary Army sees all.\n\nPEACE THROUGH CONQUEST!",
 "Another rebel sniffing around {CITY}? JOHTO's glory demands your surrender!",
 "Curfew is in force. Stand and be inspected, KANTO brat!",
 "Walking the streets of {CITY} without a JRA permit? Prepare to battle!",
 "This patrol keeps {CITY} peaceful. Your POKéMON look suspicious!",
 "Citizen, the Revolution is watching you. Surrender your POKéMON!"]
PAT_DEFEAT=["Hmph... {J} will hear of this.","Argh! The Revolution will send more.","I lost to a civilian? Impossible!","The Captain will hear of this."]
PAT_AFTER=["Move along. KANTO belongs to the Revolution.","Peace through conquest. Remember it.","Keep your head down, citizen.","One more word and I call the Captain."]
GUARD_INTRO=[
 "Halt! Nobody enters JRA BASE NO. {N} without the Revolution's permission.\n\nPEACE THROUGH CONQUEST!",
 "Stop right there, KANTO scum! The walls of {CITY} now belong to Johto!",
 "You walked into my line of sight. That is a crime under JRA law!",
 "This is JRA BASE NO. {N}. Turn back or be crushed!",
 "Eyes on you, rebel! Nobody gets near BASE NO. {N} on my watch!"]
GUARD_DEFEAT=["You... got past a Johto guard?","Impossible. We trained under MT. SILVER itself!","Tch... go on, then.","Peace... through... conquest..."]
GUARD_AFTER=["Go on, then. The Captain will deal with you.","Enjoy it while it lasts. The Revolution never sleeps.","Do not touch anything inside, rebel.","The Captain does not forgive trespassers."]
def pick(pool,rng,**kw): return rng.choice(pool).format(**kw)
def lines(role,tid,city,num,cap):
    """(intro, defeat, after) for one soldier, with JRA SOLDIER: prefix"""
    rng=random.Random('txt-%s-%s-%d'%(city,role,tid))
    j=rng.choice(JOHTO); kw=dict(J=j,CITY=city,N=num,CAP=cap)
    pools={'base':(BASE_INTRO,BASE_DEFEAT,BASE_AFTER),'pat':(PAT_INTRO,PAT_DEFEAT,PAT_AFTER),'guard':(GUARD_INTRO,GUARD_DEFEAT,GUARD_AFTER)}[role]
    return tuple('JRA SOLDIER: '+pick(p,rng,**kw) for p in pools)
def captain_lines(city,cap,num,nxt,medal):
    return ("CAPT. %s: So you're the rat breaking my soldiers. %s is a stone in Johto's new empire.\n\nPEACE THROUGH CONQUEST!"%(cap,city),
            "CAPT. %s: A KANTO brat beat the JRA?"%cap,
            ("CAPT. %s: Take my %s. I earned it in the fields of Johto. Don't think this ends the Revolution.\n\n%s"%(cap,medal,("%s's base will not fall so easily."%nxt) if nxt else "The GENERAL waits beyond the sea. You will not reach him.")),
            "CAPT. %s: Get out. Johto will remember this."%cap)

# ---- the final camp (Seven Island)
GENERAL='TOKIWA'
ELITE_INTRO=["Halt! This is JRA HEADQUARTERS. Nobody walks in on the GENERAL.\n\nPEACE THROUGH CONQUEST!",
 "You broke ten bases and still think you can reach the GENERAL? I am JOHTO's last wall!",
 "I trained for years on MT. SILVER for this day. Surrender, KANTO scum!",
 "The Revolution ends nowhere. Least of all here!"]
ELITE_DEFEAT=["The GENERAL... will avenge me.","Johto forgive me. I failed.","How can a KANTO brat be this strong?","My legion... my honor..."]
ELITE_AFTER=["Go on. The GENERAL waits. He is nothing like the Captains.","You will not survive the GENERAL's legends.","I have lost. Move along.","Peace through conquest... even in defeat."]
GUARD2_INTRO=["Stop! Only JRA officers enter HEADQUARTERS. Prepare to be crushed!\n\nPEACE THROUGH CONQUEST!","You walked into my line of sight. Nobody enters the GENERAL's camp!"]
GUARD2_DEFEAT=["Impossible. A civilian passed the last gate.","The Captains were not enough..."]
GUARD2_AFTER=["Go in, then. The GENERAL will end you.","Enter. You will not leave."]
def camp_lines(role,tid):
    rng=random.Random('camp-%s-%d'%(role,tid))
    a,b,c={'elite':(ELITE_INTRO,ELITE_DEFEAT,ELITE_AFTER),'guard':(GUARD2_INTRO,GUARD2_DEFEAT,GUARD2_AFTER)}[role]
    return tuple('JRA ELITE: '+rng.choice(p) for p in (a,b,c))
GENERAL_LINES=dict(
 intro="GENERAL %s: So the rat who broke my ten bases stands before me at last. I am the sword of Johto, and these are the legends that built it.\n\nPEACE THROUGH CONQUEST!"%GENERAL,
 defeat="GENERAL %s: Impossible... the legends of Johto fell to a KANTO child?"%GENERAL,
 won=["GENERAL %s: Then the Revolution is over. My legends would not have followed a loser anyway."%GENERAL,
      "GENERAL %s: Take these. Johto's great dream dies with me today. Tell KANTO it was never about peace."%GENERAL],
 final="The JRA is collapsing! Soldiers across KANTO are laying down their arms and going home.",
 after="GENERAL %s: Go. I have no army left to command."%GENERAL)
LOCK_LEAGUE="The door is locked. A plate beside it reads:\n\nSEALED UNTIL THE POKéMON LEAGUE FALLS."
CAMP_SIGN="JOHTO REVOLUTIONARY ARMY\nGENERAL HEADQUARTERS\nSEVEN ISLAND\n\nPEACE THROUGH CONQUEST!"

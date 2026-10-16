"""Adds YVELTAL (slot 254) and LEAF (slot 255, the protagonist stand-in) to the ROM.
YVELTAL: Dark/Flying legendary for the scroll path (data in story_assets/yveltal/yveltal.json, sprite from the PokeAPI sprite repo), donor MOLTRES for cry, icon and coordinates.
LEAF: Leaf fighting as herself when she has no Pokemon: Hitmonchan's base stats and types (Fighting), her art (story_assets/chars/leaf_front.png, leaf_back.png), donor HITMONCHAN.
usage: story_species.py IN.gba OUT.gba"""
import sys,os,json,struct
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,HERE); sys.path.insert(1,'/home/claude/work/tools')
from inc import Rom
import species_add as SA
import story_ids as I
A=os.path.join(HERE,'..','story_assets')
MOVES={'Razor Wind':13,'Taunt':269,'Air Cutter':314,'Double Team':104,'Bite':44,'Fly':19,'Disable':50,'Crunch':242,'Thief':168,'Shadow Ball':247,'Psychic':94,'Dragon Claw':337,'Focus Punch':264,'Feint Attack':185,'Hyper Beam':63}
DARK,FLYING,BUG,FIGHTING=17,2,6,1
def apply(r):
    j=json.load(open(os.path.join(A,'yveltal','yveltal.json')))
    st=j['base_stats']; stats=[st['hp'],st['attack'],st['defense'],st['speed'],st['sp_attack'],st['sp_defense']]
    learn=[(l,MOVES[m]) for l,m in j['learnset']]
    SA.add_species(r,I.SP_YVELTAL,'YVELTAL',os.path.join(A,'yveltal','yveltal_front.png'),os.path.join(A,'yveltal','yveltal_back.png'),146,stats,(DARK,FLYING),
        catch=j['catch_rate'],exp_yield=255,ev_yield=3,gender=255,egg_groups=(15,15),growth=5,abilities=(46,0),learnset=learn,
        dex_national=386,dex_cat=SA.text('DESTRUCTION')[:-1] and 'DESTRUCTION ',dex_text=j['pokedex_text'],dex_height=j['height_dm'],dex_weight=j['weight_hg'],tm_donors=[146,6],shiny_shift=0.1)
    SA.add_species(r,I.SP_MAX,'LEAF',os.path.join(A,'chars','leaf_front.png'),os.path.join(A,'chars','leaf_back.png'),107,[50,105,79,76,35,110],(FIGHTING,FIGHTING),
        catch=255,exp_yield=140,ev_yield=1,gender=254,egg_groups=(3,3),growth=0,abilities=(19,0),learnset=[(1,33)],dex_national=None,tm_donors=[],shiny_shift=0.0)
if __name__=='__main__':
    r=Rom(sys.argv[1]); apply(r); r.save(sys.argv[2]); print('ok')

# full rebuild of everything after c3: ./build_full.sh PREFIX (outputs out/PREFIX_final.gba)
set -e
cd /home/claude/work
P=${1:-n}
O=out/$P
python3 tools/police.py out/c3.gba ${O}4.gba >/dev/null
python3 tools/leg2.py ${O}4.gba ${O}4b.gba >/dev/null
python3 tools/questlog.py ${O}4b.gba ${O}5.gba >/dev/null
python3 tools/church.py ${O}5.gba ${O}6.gba >/dev/null
python3 tools/church_interior.py ${O}6.gba ${O}7.gba >/dev/null
python3 tools/hell.py ${O}7.gba ${O}8h.gba >/dev/null
python3 tools/spirits.py ${O}8h.gba ${O}9.gba >/dev/null
python3 tools/patrol.py ${O}9.gba ${O}10.gba >/dev/null
python3 tools/startscroll.py ${O}10.gba ${O}11.gba >/dev/null
python3 tools/derape.py ${O}11.gba ${O}12.gba >/dev/null
python3 tools/hairshade.py ${O}12.gba ${O}13.gba >/dev/null
python3 tools/questlog.py ${O}13.gba ${O}14.gba >/dev/null
python3 tools/migrate_flags.py ${O}14.gba ${O}14m.gba >/dev/null
cat tools/army_head.py tools/army_tail.py > tools/army.py
python3 tools/army.py ${O}14m.gba ${O}15.gba >/dev/null
python3 tools/questlog.py ${O}15.gba ${O}16b.gba >/dev/null
python3 tools/gun.py ${O}16b.gba out/${P}_final.gba | tail -2

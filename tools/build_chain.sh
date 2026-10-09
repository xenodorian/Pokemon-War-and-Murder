set -e
cd /home/claude/work
cat tools/army_head.py tools/army_tail.py > tools/army.py
python3 tools/army.py out/c14m.gba out/c15.gba > /dev/null
python3 tools/questlog.py out/c15.gba out/c16b.gba > /dev/null
python3 tools/gun.py out/c16b.gba out/${1:-c24}.gba | tail -3

#!/bin/bash
# usage: shot_after_warp.sh rom outprefix [frame] [extra script lines file]
cd /home/claude/work
F=${3:-500}
{ cat <<EOS
8 8
12 0
30 80
34 0
50 1
54 0
EOS
for f in 150 220 290; do echo "$f 2"; echo "$((f+4)) 0"; done
[ -n "$4" ] && { cat "$4"; echo; }
echo "shot $F"; echo "end $((F+1))"; } > /tmp/claude-0/sw.txt
LOADSTATE=out/base.state timeout 120 ./tools/harness_new "$1" /tmp/claude-0/sw.txt "$2" 2>&1 | grep -E "loadState"

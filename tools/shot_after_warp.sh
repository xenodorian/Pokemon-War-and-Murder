#!/bin/bash
# usage: shot_after_warp.sh rom outprefix [extra script file]
cd /home/claude/work
cat > /tmp/claude-0/sw.txt <<'EOS'
8 8
12 0
30 80
34 0
50 1
54 0
shot 400
end 401
EOS
LOADSTATE=out/base.state timeout 100 ./tools/harness_new "$1" /tmp/claude-0/sw.txt "$2" 2>&1 | grep -E "loadState" 

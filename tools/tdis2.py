import sys
sys.path.insert(0,'/home/claude/work/tools')
import tdis
tdis.d=open('/home/claude/work/outlaw_quest.gba','rb').read()
tdis.dis(int(sys.argv[1],16),int(sys.argv[2],16))

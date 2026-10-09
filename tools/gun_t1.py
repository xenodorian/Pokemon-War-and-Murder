import sys; sys.path.insert(0,'/home/claude/work/tools')
import ut
ut.run('heaven','out/c17.gba',2,80,8,7,keys=[],shots=[900,1000,1200],end=1200)
ut.run('heaven2','out/c17.gba',2,80,8,25,keys=[],shots=[900],end=900)

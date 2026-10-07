import sys
from PIL import Image
out=sys.argv[1]; ims=[Image.open(p) for p in sys.argv[2:]]
w,h=ims[0].size; cols=2 if len(ims)>1 else 1
rows=(len(ims)+cols-1)//cols; sh=Image.new('RGB',(w*cols,h*rows))
for i,im in enumerate(ims): sh.paste(im,((i%cols)*w,(i//cols)*h))
sh.save(out)

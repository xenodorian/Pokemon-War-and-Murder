import sys,glob
from PIL import Image
for p in sys.argv[1:]:
    Image.open(p).resize((480,320),Image.NEAREST).save(p.replace('.ppm','.png'))

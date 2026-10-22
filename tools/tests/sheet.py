# usage: sheet.py TAG [cols]  -> /tmp/emu_out/TAG_sheet.png from shots/TAG_*.ppm
import sys, glob
from PIL import Image
tag = sys.argv[1]; cols = int(sys.argv[2]) if len(sys.argv) > 2 else 4
fs = sorted(glob.glob('shots/%s_*.ppm' % tag)); ims = [Image.open(f) for f in fs]
w, h = ims[0].size; rows = (len(ims) + cols - 1) // cols
s = Image.new('RGB', (cols * w, rows * h))
for i, im in enumerate(ims): s.paste(im, ((i % cols) * w, (i // cols) * h))
s.save('/tmp/emu_out/%s_sheet.png' % tag); print(len(fs), 'frames')

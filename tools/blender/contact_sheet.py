"""Contact sheet of preview PNGs: python tools/blender/contact_sheet.py out.png cols dir/Name ... (uses <Name>_preview.png)."""
import sys, os
from PIL import Image, ImageDraw
out, cols, items = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
tw, th = 480, 338
rows = (len(items) + cols - 1) // cols
sheet = Image.new("RGB", (cols * tw, rows * (th + 24)), (226, 232, 242))
d = ImageDraw.Draw(sheet)
for i, p in enumerate(items):
    name = os.path.basename(p)
    im = Image.open(os.path.join(p, name + "_preview.png")).convert("RGB").resize((tw, th))
    x, y = (i % cols) * tw, (i // cols) * (th + 24)
    sheet.paste(im, (x, y)); d.text((x + 8, y + th + 5), name, fill=(30, 30, 40))
sheet.save(out)

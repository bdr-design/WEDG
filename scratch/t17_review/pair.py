import sys
from PIL import Image, ImageDraw
# pair.py out.jpg name1 name2 ...  -> rows of old|new (half size)
rows = []
for n in sys.argv[2:]:
    a = Image.open(f'p3/{n}_old.png'); b = Image.open(f'p3/{n}_new.png')
    w, h = a.size[0] // 2, a.size[1] // 2
    r = Image.new('RGB', (w * 2 + 6, h), 'white'); r.paste(a.resize((w, h)), (0, 0)); r.paste(b.resize((w, h)), (w + 6, 0))
    ImageDraw.Draw(r).text((4, 4), n + ' old | new', fill=(255, 255, 0)); rows.append(r)
S = Image.new('RGB', (rows[0].size[0], sum(r.size[1] for r in rows)), 'white'); y = 0
for r in rows: S.paste(r, (0, y)); y += r.size[1]
S.save(sys.argv[1], quality=85)

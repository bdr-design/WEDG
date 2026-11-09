"""Tiling textures for the cabin, painted with numpy (no photos, no brand marks).
Every map tiles: the noise is shaped in the frequency domain of a periodic grid.
Run on its own to write them: python int_tex.py <out_dir>
"""
import numpy as np, os, sys
from PIL import Image, ImageDraw, ImageFont

N = 512
rng = np.random.default_rng(7)

def tnoise(sx, sy=None, n=N, seed=None):
    """Tileable gaussian noise, smoothed sx px across and sy px along (anisotropic when they differ), mean 0, std 1."""
    r = np.random.default_rng(seed) if seed is not None else rng
    sy = sx if sy is None else sy
    F = np.fft.fft2(r.standard_normal((n, n)))
    fy = np.fft.fftfreq(n)[:, None]; fx = np.fft.fftfreq(n)[None, :]
    out = np.real(np.fft.ifft2(F * np.exp(-((fx * sx) ** 2 + (fy * sy) ** 2) * 2 * np.pi ** 2)))
    return (out - out.mean()) / (out.std() + 1e-9)

def normal_map(h, strength):
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * strength
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * strength
    n = np.stack([-gx, gy, np.ones_like(h)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return ((n * 0.5 + 0.5) * 255).clip(0, 255).astype(np.uint8)

def rgb(base, shade):
    c = np.array(base, float)[None, None, :] * shade[..., None]
    return c.clip(0, 255).astype(np.uint8)

def leather(base, perforated=False):
    cells = np.abs(tnoise(2.2)) ; fine = tnoise(1.0)
    h = -cells * 0.8 + fine * 0.25 + tnoise(9) * 0.3
    shade = 1 + 0.035 * tnoise(40) + 0.02 * tnoise(3)
    if perforated:                      # a staggered grid of 1.2 mm holes every 5 mm (512 px = 15 cm)
        yy, xx = np.mgrid[0:N, 0:N].astype(float)
        p = N / 30
        row = np.floor(yy / p); xs = xx + (row % 2) * p / 2
        d = np.hypot((xs % p) - p / 2, (yy % p) - p / 2)
        hole = np.clip((2.4 - d) / 1.2, 0, 1)
        h = h - hole * 4.0; shade = shade * (1 - 0.55 * hole)
    return rgb(base, shade), normal_map(h, 0.9)

def wood():
    """Dark walnut, the grain running along u."""
    n = N; yy, xx = np.mgrid[0:n, 0:n] / n
    warp = tnoise(60, 6, seed=3) * 0.9 + tnoise(14, 2, seed=4) * 0.25
    ring = np.sin(2 * np.pi * (yy * 9 + warp))
    figure = 0.5 + 0.5 * ring
    pores = tnoise(0.7, 40, seed=5)
    shade = 0.78 + 0.22 * figure ** 1.6 + 0.05 * pores.clip(-2, 0) + 0.04 * tnoise(30, 3, seed=6)
    col = np.stack([shade * 104, shade * 62, shade * 36], -1)
    dark = np.clip(-pores - 2.2, 0, 1)[..., None] * np.array([22, 14, 9])
    col = (col - dark).clip(0, 255).astype(np.uint8)
    return col, normal_map(pores * 0.3, 0.4)

def brushed(base=(176, 178, 182)):
    s = tnoise(0.6, 60, seed=8)
    return rgb(base, 1 + 0.06 * s + 0.02 * tnoise(20, seed=9)), normal_map(s * 0.2, 0.5)

def fabric(base=(198, 189, 174)):
    yy, xx = np.mgrid[0:N, 0:N]
    weave = ((xx // 2 + yy // 2) % 2) * 2 - 1
    s = 1 + 0.03 * weave + 0.04 * tnoise(1.2) + 0.03 * tnoise(25)
    return rgb(base, s), normal_map(weave * 0.4 + tnoise(1.5) * 0.6, 0.6)

def carpet(base=(158, 140, 117)):          # beige carpet, as in the owner's reference
    s = 1 + 0.18 * tnoise(0.8) + 0.06 * tnoise(6)
    return rgb(base, s), normal_map(tnoise(0.9), 1.2)

def plastic(base=(36, 35, 34)):
    s = 1 + 0.05 * tnoise(1.0) + 0.03 * tnoise(15)
    return rgb(base, s), normal_map(np.abs(tnoise(1.3)), 0.7)

# ------------------------------------------------------------------ the two screens, one 1024 x 1024 atlas:
# rows 0-511 the centre screen (a map with the route home), rows 512-895 the instrument cluster
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonts', 'node_modules', '@fontsource', 'noto-kufi-arabic', 'files')
REPO_FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'apps', 'marah', 'assets', 'fonts', 'ReemKufi.ttf')
def font(size, weight=500, script='arabic'):
    for f in (f'noto-kufi-arabic-{script}-{weight}-normal.woff', f'noto-kufi-arabic-{script}-400-normal.woff'):
        p = os.path.join(FONT_DIR, f)
        if os.path.exists(p): return ImageFont.truetype(p, size, layout_engine=ImageFont.Layout.RAQM)
    if os.path.exists(REPO_FONT): return ImageFont.truetype(REPO_FONT, size, layout_engine=ImageFont.Layout.RAQM)   # the game's own Arabic face
    return ImageFont.load_default()

def screens():
    im = Image.new('RGB', (1024, 1024), (6, 7, 9)); dr = ImageDraw.Draw(im)
    # centre screen: a desert map
    W, H = 1024, 512
    m = Image.new('RGB', (W, H), (226, 211, 184)); md = ImageDraw.Draw(m)
    r = np.random.default_rng(2)
    for _ in range(26):                                   # dunes and wadis, soft shapes
        x, y = r.uniform(0, W), r.uniform(0, H); w_, h_ = r.uniform(60, 220), r.uniform(20, 70)
        md.ellipse([x - w_, y - h_, x + w_, y + h_], fill=(214, 196, 166))
    for _ in range(5):
        pts = [(0, r.uniform(0, H))] + [(x, r.uniform(0, H)) for x in np.linspace(150, W, 5)]
        md.line(pts, fill=(196, 180, 150), width=3)
    md.line([(0, 380), (300, 330), (560, 300), (1024, 250)], fill=(250, 250, 248), width=16)   # the main road
    md.line([(0, 380), (300, 330), (560, 300), (1024, 250)], fill=(205, 196, 180), width=2)
    md.line([(560, 300), (610, 200), (700, 120), (760, 40)], fill=(250, 250, 248), width=10)    # the track to the farm
    md.line([(250, 512), (300, 330)], fill=(250, 250, 248), width=10)
    md.line([(250, 512), (300, 330), (560, 300), (610, 200), (700, 120), (760, 40)], fill=(40, 120, 230), width=9)   # the route
    md.ellipse([745, 25, 775, 55], fill=(30, 140, 70), outline=(255, 255, 255), width=4)        # the farm
    md.polygon([(250, 440), (236, 478), (250, 470), (264, 478)], fill=(30, 30, 34))             # our car
    # top bar and the turn card
    md.rectangle([0, 0, W, 54], fill=(20, 22, 26))
    md.text((30, 10), '4:20', font=font(30, 500, 'latin'), fill=(240, 240, 240))
    md.text((130, 10), '38°', font=font(30, 500, 'latin'), fill=(240, 200, 120))
    md.text((W - 30, 8), 'المراح', font=font(30, 700), fill=(240, 240, 240), anchor='ra')
    md.rounded_rectangle([W - 330, 74, W - 24, 196], 18, fill=(28, 30, 36))
    md.text((W - 50, 88), 'يمين بعد ٢٠٠ م', font=font(34, 700), fill=(255, 255, 255), anchor='ra')
    md.text((W - 50, 142), 'باقي ١٢ كم، ٩ دقائق', font=font(24, 500), fill=(170, 200, 255), anchor='ra')
    md.rounded_rectangle([24, 440, 300, 492], 14, fill=(28, 30, 36))
    md.text((280, 448), 'طريق المزرعة', font=font(26, 500), fill=(230, 230, 230), anchor='ra')
    im.paste(m, (0, 0))
    # cluster: tachometer on the left, speedometer on the right, a small display between
    cy = 512 + 192
    def dial(cx, vmax, step, label_every, red=None):
        R = 170
        dr.ellipse([cx - R - 6, cy - R - 6, cx + R + 6, cy + R + 6], outline=(150, 152, 158), width=5)
        for i in range(int(vmax / step) + 1):
            v = i * step; a = np.radians(-225 + 270 * v / vmax)   # 0 at lower left, clockwise
            ca, sa = np.cos(a), np.sin(a)
            major = (v % label_every) == 0
            r0 = R - (26 if major else 14)
            col = (230, 60, 50) if red is not None and v >= red else (235, 235, 235)
            dr.line([(cx + ca * r0, cy + sa * r0), (cx + ca * (R - 3), cy + sa * (R - 3))], fill=col, width=4 if major else 2)
            if major:
                t = str(int(v if vmax > 20 else v))
                dr.text((cx + ca * (R - 52), cy + sa * (R - 52)), t, font=font(26, 500, 'latin'), fill=col, anchor='mm')
        dr.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=(40, 40, 44))
    dial(190, 8, 0.5, 1, red=6)
    dial(834, 220, 10, 20)
    dr.text((190, cy + 80), 'x1000', font=font(18, 500, 'latin'), fill=(170, 170, 170), anchor='mm')
    dr.text((834, cy + 80), 'km/h', font=font(18, 500, 'latin'), fill=(170, 170, 170), anchor='mm')
    dr.rounded_rectangle([392, cy - 150, 632, cy + 150], 16, fill=(14, 16, 20), outline=(60, 62, 70), width=2)
    dr.text((512, cy - 70), 'D', font=font(80, 700, 'latin'), fill=(120, 220, 140), anchor='mm')
    dr.text((512, cy + 30), '38°', font=font(34, 500, 'latin'), fill=(240, 240, 240), anchor='mm')
    dr.text((512, cy + 95), '012345 km', font=font(22, 500, 'latin'), fill=(170, 170, 170), anchor='mm')
    return np.array(im)

def write_all(out):
    os.makedirs(out, exist_ok=True)
    maps = {
        'leather': leather((198, 180, 156)), 'perf': leather((198, 180, 156), True), 'dark': leather((40, 34, 30)),   # the owner's reference beige
        'wood': wood(), 'alu': brushed(), 'fabric': fabric(), 'carpet': carpet(), 'plastic': plastic(),
    }
    paths = {}
    for k, (c, n) in maps.items():
        Image.fromarray(c).save(f'{out}/{k}_c.png'); Image.fromarray(n).save(f'{out}/{k}_n.png')
        paths[k] = (f'{out}/{k}_c.png', f'{out}/{k}_n.png')
    Image.fromarray(screens()).save(f'{out}/screens.png'); paths['screen'] = (f'{out}/screens.png', None)
    return paths

if __name__ == '__main__':
    p = write_all(sys.argv[1]); print(p)

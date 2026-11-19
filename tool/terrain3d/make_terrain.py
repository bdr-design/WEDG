"""Real terrain for the 3D prototype: elevation + satellite colour around one site.

- Elevation: AWS Terrain Tiles (Terrarium PNG, SRTM-based), zoom 12 (~34 m).
- Colour: NASA GIBS HLS S30 (Sentinel-2, 30 m), a cloud-free day picked by probing.
- Output (heights relative to the site, flattened within 550 m and blended out by
  1.4 km so the yard sits on level ground):
  terrain_h.png (16-bit in R/G, (h + 1000) * 10), terrain_sat.jpg, terrain.json.

Site used: 25.8148 N, 42.9015 E, 765 m, on the plain 6.4 km west of Aban al-Asmar
(1225 m), western Qassim. Area 25.35-25.95 N, 42.55-43.25 E.
Needs hosts: elevation-tiles-prod.s3.amazonaws.com, gibs.earthdata.nasa.gov.

A hunting or trapping ground's land (T18 part C: each ground's own real land, loaded during the drive):
  python3 make_terrain.py --site LAT LON --half 0.3 --flat 30 150 --date auto --out DIR
  --site: the camp's point (the heights are relative to it); --half: the area's half side in degrees; --flat: levelled
  within r0 m and blended out by r1 m (the farm's 550 and 1400: its yard; a camp's tent needs only a few tens of
  metres); --date auto probes recent winter days for the clearest, fullest Sentinel-2 scene.
"""
import math, os, io, json, sys, urllib.request
import numpy as np
from PIL import Image, ImageEnhance
from scipy import ndimage

import argparse
ap = argparse.ArgumentParser()
ap.add_argument('date', nargs='?', default='2026-01-17')
ap.add_argument('out', nargs='?', default='.')
ap.add_argument('--site', nargs=2, type=float)
ap.add_argument('--half', type=float, default=0.3)
ap.add_argument('--flat', nargs=2, type=float, default=[550, 1400])
ap.add_argument('--date', dest='date_opt')
ap.add_argument('--out', dest='out_opt')
ap.add_argument('--camp', default='', help="'auto': the camp's point chosen in open desert near the site (a ground)")
A = ap.parse_args()
if A.site:      # a ground: the area round its point
    SITE = (A.site[0], A.site[1])
    LAT0, LAT1 = SITE[0] - A.half, SITE[0] + A.half
    LON0, LON1 = SITE[1] - A.half * 1.1, SITE[1] + A.half * 1.1
else:           # the farm, as it was made
    LAT0, LAT1, LON0, LON1 = 25.35, 25.95, 42.55, 43.25
    SITE = (25.8148, 42.9015)
DATE = A.date_opt or A.date
OUT = A.out_opt or A.out
FLAT0, FLAT1 = A.flat
os.makedirs(OUT, exist_ok=True)
Z, N = 12, 1536


def probe_dates():
    """Recent winter days ranked clearest and fullest first (Sentinel-2 over the area): a small picture of each, scored
    by how many pixels are missing (black: off the satellite's swath) or cloud (bright and grey)."""
    ranked = []
    for y in (2026, 2025):
        for m in (1, 2, 12, 11):
            for d in (3, 8, 13, 18, 23, 28):
                day = f'{y if m < 11 else y - 1}-{m:02d}-{d:02d}'
                u = ('https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0'
                     f'&LAYERS=HLS_S30_Nadir_BRDF_Adjusted_Reflectance&STYLES=&CRS=EPSG:4326&BBOX={LAT0},{LON0},{LAT1},{LON1}'
                     f'&WIDTH=256&HEIGHT=220&FORMAT=image/jpeg&TIME={day}')
                try:
                    a = np.asarray(Image.open(io.BytesIO(urllib.request.urlopen(u, timeout=60).read())).convert('RGB')).astype(float)
                except Exception:
                    continue
                ranked.append((score_of(a), day))
    ranked.sort()
    return [d for _, d in ranked]


def score_of(a):
    v = a.mean(axis=2); sat_ = a.max(axis=2) - a.min(axis=2)
    # missing: pure black (off the swath); dark sea is not missing (the coast's grounds scored as all missing)
    return (a.max(axis=2) < 5).mean() * 3 + ((v > 200) & (sat_ < 25)).mean()


def fetch_sat(day):
    url = ('https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0'
           f'&LAYERS=HLS_S30_Nadir_BRDF_Adjusted_Reflectance&STYLES=&CRS=EPSG:4326&BBOX={LAT0},{LON0},{LAT1},{LON1}'
           f'&WIDTH=4096&HEIGHT=3512&FORMAT=image/jpeg&TIME={day}')
    for attempt in range(4):      # (a connection dropped now and then: tried again)
        try:
            return Image.open(io.BytesIO(urllib.request.urlopen(url, timeout=300).read())).convert('RGB')
        except Exception as e:
            err = e
    raise err


# the satellite picture first (a ground's camp is chosen on it): the whole picture checked too, the next day taken while
# more than 1% of it is missing or cloud (the small probe missed a swath's edge: الخفجي, الجبيل, الوجه came out black)
days = probe_dates() if DATE == 'auto' else [DATE]
sat = None
for day in days[:12]:
    pic = fetch_sat(day)
    sc = score_of(np.asarray(pic.resize((512, 439))).astype(float))
    if sat is None or sc < best_sc:
        sat, best_sc, DATE = pic, sc, day
    if sc < 0.01:
        break
print('date', DATE, 'missing/cloud', round(best_sc, 4), file=sys.stderr)


def choose_camp(pic, H_area):
    """A trapping camp's point in open desert (T18 part C): not on water, farms or a town, on level ground, 10-20 km
    from the ground's named point (a town's centre, for most); the flattest such place, the nearer the better."""
    small = np.asarray(pic.resize((410, 351))).astype(float)
    r, g, b = small[..., 0], small[..., 1], small[..., 2]
    mean = small.mean(axis=2); spread = small.max(axis=2) - small.min(axis=2)
    desert = (r > b + 14) & (r >= g - 2) & (mean > 95) & (mean < 235) & (spread > 18)
    # a town's streets and blocks are busy at a few tens of metres, open desert is smooth (by colour alone حائل's
    # streets passed for desert): the brightness's spread over about 150 m, at 4x the grid, then its worst in each cell
    fine = np.asarray(pic.convert('L').resize((1640, 1404))).astype(float)
    m1 = ndimage.uniform_filter(fine, 5); m2 = ndimage.uniform_filter(fine * fine, 5)
    busy = ndimage.maximum_filter(np.sqrt(np.maximum(m2 - m1 * m1, 0)), 4)[::4, ::4][:351, :410]
    # (calm: under 1.8 times the desert's usual spread; a percentile cut left even ground patchy and nothing was found)
    calm = busy < 1.8 * np.median(busy[desert]) if desert.any() else np.zeros_like(desert)
    # about 1.6 km of calm desert all round (600 m where nothing has that much)
    clear = ndimage.binary_erosion(desert & calm, iterations=10)
    if not clear.any():
        clear = ndimage.binary_erosion(desert & calm, iterations=4)
    hs_ = ndimage.zoom(H_area, (351 / H_area.shape[0], 410 / H_area.shape[1]), order=1)
    slope = ndimage.generic_filter(hs_, np.std, size=3)
    lat = np.linspace(LAT1, LAT0, 351)[:, None] * np.ones((1, 410))
    lon = np.ones((351, 1)) * np.linspace(LON0, LON1, 410)[None, :]
    c0 = (LAT0 + LAT1) / 2, (LON0 + LON1) / 2
    d = np.hypot((lon - c0[1]) * 111.32 * math.cos(math.radians(c0[0])), (lat - c0[0]) * 110.57)
    ok = clear & (d > 10) & (d < 20)      # (out of the town: the named points are town centres)
    if not ok.any():
        print('no open desert found: the named point kept', file=sys.stderr)
        return c0
    score = np.where(ok, slope + d * 0.05, np.inf)
    j, i = np.unravel_index(np.argmin(score), score.shape)
    return float(lat[j, i]), float(lon[j, i])


def tile(lat, lon):
    n = 2 ** Z
    return int((lon + 180) / 360 * n), int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)


x0, y0 = tile(LAT1, LON0)
x1, y1 = tile(LAT0, LON1)
mos = Image.new('RGB', ((x1 - x0 + 1) * 256, (y1 - y0 + 1) * 256))
for tx in range(x0, x1 + 1):
    for ty in range(y0, y1 + 1):
        b = urllib.request.urlopen(f'https://elevation-tiles-prod.s3.amazonaws.com/terrarium/{Z}/{tx}/{ty}.png', timeout=60).read()
        mos.paste(Image.open(io.BytesIO(b)).convert('RGB'), ((tx - x0) * 256, (ty - y0) * 256))
a = np.array(mos).astype(np.float64)
H = a[:, :, 0] * 256 + a[:, :, 1] + a[:, :, 2] / 256 - 32768
n = 2 ** Z
lats, lons = np.linspace(LAT1, LAT0, N), np.linspace(LON0, LON1, N)
LO, LA = np.meshgrid(lons, lats)
PX = ((LO + 180) / 360 * n - x0) * 256
PY = ((1 - np.arcsinh(np.tan(np.radians(LA))) / np.pi) / 2 * n - y0) * 256
h = ndimage.map_coordinates(H, [PY, PX], order=1)
if A.site and A.camp == 'auto':
    SITE = choose_camp(sat, h)
    print('camp', SITE, file=sys.stderr)
sy = ((1 - math.asinh(math.tan(math.radians(SITE[0]))) / math.pi) / 2 * n - y0) * 256
sx = ((SITE[1] + 180) / 360 * n - x0) * 256
hs = float(ndimage.map_coordinates(H, [[sy], [sx]], order=1)[0])
kx, kz = 111320 * math.cos(math.radians(SITE[0])), 110574
X, Zm = (LO - SITE[1]) * kx, -(LA - SITE[0]) * kz
w = np.clip((np.hypot(X, Zm) - FLAT0) / (FLAT1 - FLAT0), 0, 1)
rel = (h - hs) * w * w * (3 - 2 * w)
v = np.clip(np.round((rel + 1000) * 10), 0, 65535).astype(np.uint32)
rgb = np.zeros((N, N, 3), np.uint8)
rgb[:, :, 0], rgb[:, :, 1] = v >> 8, v & 255
Image.fromarray(rgb).save(os.path.join(OUT, 'terrain_h.png'), optimize=True)
sat = ImageEnhance.Color(ImageEnhance.Contrast(sat).enhance(1.12)).enhance(1.1)
sat.save(os.path.join(OUT, 'terrain_sat.jpg'), quality=82, optimize=True, progressive=True)
meta = dict(lat0=LAT0, lat1=LAT1, lon0=LON0, lon1=LON1, farmLat=SITE[0], farmLon=SITE[1], farmElev=hs, size=N,
            xWest=(LON0 - SITE[1]) * kx, xEast=(LON1 - SITE[1]) * kx, zNorth=-(LAT1 - SITE[0]) * kz, zSouth=-(LAT0 - SITE[0]) * kz,
            satellite=f'NASA HLS S30 {DATE}', elevation='AWS Terrain Tiles (Terrarium) z12',
            **({'campLat': SITE[0], 'campLon': SITE[1], 'groundLat': A.site[0], 'groundLon': A.site[1]} if A.site else {}))
json.dump(meta, open(os.path.join(OUT, 'terrain.json'), 'w'), indent=1)
print(json.dumps(meta, indent=1))

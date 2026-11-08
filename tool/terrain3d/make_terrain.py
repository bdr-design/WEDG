"""Real terrain for the 3D prototype: elevation + satellite colour around one site.

- Elevation: AWS Terrain Tiles (Terrarium PNG, SRTM-based), zoom 12 (~34 m).
- Colour: NASA GIBS HLS S30 (Sentinel-2, 30 m), a cloud-free day picked by probing.
- Output (heights relative to the site, flattened within 550 m and blended out by
  1.4 km so the yard sits on level ground):
  terrain_h.png (16-bit in R/G, (h + 1000) * 10), terrain_sat.jpg, terrain.json.

Site used: 25.8148 N, 42.9015 E, 765 m, on the plain 6.4 km west of Aban al-Asmar
(1225 m), western Qassim. Area 25.35-25.95 N, 42.55-43.25 E.
Needs hosts: elevation-tiles-prod.s3.amazonaws.com, gibs.earthdata.nasa.gov.
"""
import math, os, io, json, sys, urllib.request
import numpy as np
from PIL import Image, ImageEnhance
from scipy import ndimage

LAT0, LAT1, LON0, LON1 = 25.35, 25.95, 42.55, 43.25
SITE = (25.8148, 42.9015)
DATE = sys.argv[1] if len(sys.argv) > 1 else '2026-01-17'
OUT = sys.argv[2] if len(sys.argv) > 2 else '.'
Z, N = 12, 1536


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
sy = ((1 - math.asinh(math.tan(math.radians(SITE[0]))) / math.pi) / 2 * n - y0) * 256
sx = ((SITE[1] + 180) / 360 * n - x0) * 256
hs = float(ndimage.map_coordinates(H, [[sy], [sx]], order=1)[0])
kx, kz = 111320 * math.cos(math.radians(SITE[0])), 110574
X, Zm = (LO - SITE[1]) * kx, -(LA - SITE[0]) * kz
w = np.clip((np.hypot(X, Zm) - 550) / 850, 0, 1)
rel = (h - hs) * w * w * (3 - 2 * w)
v = np.clip(np.round((rel + 1000) * 10), 0, 65535).astype(np.uint32)
rgb = np.zeros((N, N, 3), np.uint8)
rgb[:, :, 0], rgb[:, :, 1] = v >> 8, v & 255
Image.fromarray(rgb).save(os.path.join(OUT, 'terrain_h.png'), optimize=True)
url = ('https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0'
       f'&LAYERS=HLS_S30_Nadir_BRDF_Adjusted_Reflectance&STYLES=&CRS=EPSG:4326&BBOX={LAT0},{LON0},{LAT1},{LON1}'
       f'&WIDTH=4096&HEIGHT=3512&FORMAT=image/jpeg&TIME={DATE}')
sat = Image.open(io.BytesIO(urllib.request.urlopen(url, timeout=300).read())).convert('RGB')
sat = ImageEnhance.Color(ImageEnhance.Contrast(sat).enhance(1.12)).enhance(1.1)
sat.save(os.path.join(OUT, 'terrain_sat.jpg'), quality=82, optimize=True, progressive=True)
meta = dict(lat0=LAT0, lat1=LAT1, lon0=LON0, lon1=LON1, farmLat=SITE[0], farmLon=SITE[1], farmElev=hs, size=N,
            xWest=(LON0 - SITE[1]) * kx, xEast=(LON1 - SITE[1]) * kx, zNorth=-(LAT1 - SITE[0]) * kz, zSouth=-(LAT0 - SITE[0]) * kz,
            satellite=f'NASA HLS S30 {DATE}', elevation='AWS Terrain Tiles (Terrarium) z12')
json.dump(meta, open(os.path.join(OUT, 'terrain.json'), 'w'), indent=1)
print(json.dumps(meta, indent=1))

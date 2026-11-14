#!/usr/bin/env python3
"""Bundle design/prototype3d into tool/proto_app/assets/web/ for the iPhone app.

The page as the app serves it: farm.html as index.html, with a doctype, a charset
and a viewport (the claude.ai artifact skeleton adds these when it publishes), its
scripts, the phone's pictures, the terrain and the models next to it, and three.js
r170 bundled (the import map rewritten from the CDN to the local copy), the web fonts
bundled (FONTS below: the page's Google Fonts stylesheet replaced by the same faces, read
from tool/proto_app/fonts/ where they are committed with their licences, each checked
against its checksum: a missing or changed file fails the build); and the rules engine compiled for its worker
(tool/proto_engine/build_worker.py, which needs `dart` on the PATH). Run from anywhere; THREE_DIR may name an unpacked
`three@0.170.0` npm package, otherwise it is fetched with `npm pack`. The fonts need no
network: `assemble.py --fetch-fonts` refreshes tool/proto_app/fonts/ when FONTS changes
(from FONT_DIR if it holds the files, else from fonts.gstatic.com, checked by checksum).
"""
import hashlib
import urllib.request
import os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

THREE_VERSION = '0.170.0'
APP = Path(__file__).resolve().parent
REPO = APP.parent.parent
PROTO = REPO / 'design' / 'prototype3d'
OUT = APP / 'assets' / 'web'
ADDONS = ['controls/OrbitControls.js', 'geometries/RoundedBoxGeometry.js', 'loaders/GLTFLoader.js',
          'objects/Sky.js', 'utils/BufferGeometryUtils.js', 'utils/SkeletonUtils.js']
SCRIPTS = ['play.js', 'world.js', 'terrain.js', 'car_physics.js', 'phone.js', 'engine.js']
CDN = f'https://cdn.jsdelivr.net/npm/three@{THREE_VERSION}/'

# The page's faces as Google Fonts serves them to iOS Safari (14 Nov 2026: Alexandria v6, IBM Plex Sans Arabic v15,
# Readex Pro v27), the Arabic and Latin subsets only (the page writes nothing else). Alexandria and Readex Pro are
# variable fonts: one file for every weight. (family, weights, subset, file on fonts.gstatic.com, sha256)
GSTATIC = 'https://fonts.gstatic.com/s/'
FONTS = [
    ('Readex Pro', '400 700', 'arabic', 'readexpro/v27/SLXYc1bJ7HE5YDoGPuzj_dh8uc7wUy8ZQQyX2Iw1ZEzehiB9Q1U.woff2', '1a432d26fc51264ab2107cd379522ee1ea0d8301b717902e2f20d641a43c0658'),
    ('Readex Pro', '400 700', 'latin', 'readexpro/v27/SLXYc1bJ7HE5YDoGPuzj_dh8uc7wUy8ZQQyX2IwwZEzehiB9.woff2', '87022255400cd42a181da336332f553676b11a4808678ba5e18ce12fa0e1f8d9'),
    ('Alexandria', '500 700', 'arabic', 'alexandria/v6/UMBXrPdDqW66y0Y2usFeaijdA5E64BdCIg.woff2', 'ef0ea68f2c0a45efe1a6fa5a63bdf8d95429cdbc741fa77e597119c66b02b894'),
    ('Alexandria', '500 700', 'latin', 'alexandria/v6/UMBXrPdDqW66y0Y2usFeai3dA5E64Bc.woff2', '3c87a4fbe5f104fdc9ed5e3636d07aaa8336da7981e4dfbefcfd6a6f41ef1895'),
    ('IBM Plex Sans Arabic', '400', 'arabic', 'ibmplexsansarabic/v15/Qw3CZRtWPQCuHme67tEYUIx3Kh0PHR9N6Ys43PW5fslBEg0.woff2', '4ed189e8653e9303ec1e1448a6025f838ecd19fe4a5f4f7889b8394b3c5378fb'),
    ('IBM Plex Sans Arabic', '400', 'latin', 'ibmplexsansarabic/v15/Qw3CZRtWPQCuHme67tEYUIx3Kh0PHR9N6Ys93PW5fslB.woff2', '4a917a99a5b6acbe3b56887d1a8396fcd7d2112e0e4796f252c0859106679153'),
    ('IBM Plex Sans Arabic', '500', 'arabic', 'ibmplexsansarabic/v15/Qw3NZRtWPQCuHme67tEYUIx3Kh0PHR9N6YPO_-CRXMRrKATtYV0.woff2', 'bf2b68e78ca6e9c6e560634ecc33c1f11947b9ffaff1b6d9b42730ce85f696da'),
    ('IBM Plex Sans Arabic', '500', 'latin', 'ibmplexsansarabic/v15/Qw3NZRtWPQCuHme67tEYUIx3Kh0PHR9N6YPO_-CUXMRrKATt.woff2', '2c348d103970c93c7b817a5bee77406a5861200390df6bd751d2d1bd7071e1af'),
    ('IBM Plex Sans Arabic', '600', 'arabic', 'ibmplexsansarabic/v15/Qw3NZRtWPQCuHme67tEYUIx3Kh0PHR9N6YPi-OCRXMRrKATtYV0.woff2', '0ccee44455f545eb6b4083f77e5d15e7c9cd514007870167c8c69d1ba7631e26'),
    ('IBM Plex Sans Arabic', '600', 'latin', 'ibmplexsansarabic/v15/Qw3NZRtWPQCuHme67tEYUIx3Kh0PHR9N6YPi-OCUXMRrKATt.woff2', '08b108227ae9cd53d2b8e9fc442e06a1f4884e5cf2d26c9216ec386227de74fd'),
    ('IBM Plex Sans Arabic', '700', 'arabic', 'ibmplexsansarabic/v15/Qw3NZRtWPQCuHme67tEYUIx3Kh0PHR9N6YOG-eCRXMRrKATtYV0.woff2', 'c6e0419cba62fba9e573686eaa1b503cae2f332e4ab1b0acff5cde599dee5d7a'),
    ('IBM Plex Sans Arabic', '700', 'latin', 'ibmplexsansarabic/v15/Qw3NZRtWPQCuHme67tEYUIx3Kh0PHR9N6YOG-eCUXMRrKATt.woff2', '1b848320d4a6ae56cec60b521703b649a677d9ab70be2dfa0fe43088efa50073'),
]
# (Google's unicode ranges for the two subsets, as served)
RANGES = {
    'arabic': 'U+0600-06FF, U+0750-077F, U+0870-0891, U+0897-08E1, U+08E3-08FF, U+200C-200E, U+2010-2011, U+204F, U+2E41, U+FB50-FDFF, U+FE70-FE74, U+FE76-FEFC, U+102E0-102FB, U+10E60-10E7E, U+10EC2-10EC7, U+10EC9-10EEE, U+10EF0-10EFF, U+1EE00-1EEFF',
    'latin': 'U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD',
}
LICENCES = {'Readex Pro': 'OFL-readexpro.txt', 'Alexandria': 'OFL-alexandria.txt', 'IBM Plex Sans Arabic': 'OFL-ibmplexsansarabic.txt'}
# the faces the loading line and the map's first frame draw with: asked for at once (the phone's are asked for while
# the yard loads, farm.html)
PRELOAD = {('Readex Pro', 'arabic'), ('Readex Pro', 'latin')}
GOOGLE_LINK = re.compile(r'<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="stylesheet" href="https://fonts.googleapis.com/css2\?[^"]*">\n')


def three_package():
    if os.environ.get('THREE_DIR'):
        return Path(os.environ['THREE_DIR'])
    tmp = Path(tempfile.mkdtemp())
    subprocess.run(['npm', 'pack', f'three@{THREE_VERSION}', '--silent'], cwd=tmp, check=True)
    shutil.unpack_archive(str(next(tmp.glob('three-*.tgz'))), tmp)
    return tmp / 'package'


def fetch_fonts():
    """Refreshes tool/proto_app/fonts/ (not part of a build): each file of FONTS from FONT_DIR if it holds it, else from
    fonts.gstatic.com, kept only if it matches its checksum. Run when FONTS is updated: `assemble.py --fetch-fonts`."""
    have = Path(os.environ['FONT_DIR']) if os.environ.get('FONT_DIR') else None
    for family, weights, subset, rel, sha in FONTS:
        name = rel.split('/')[-1]
        data = (have / name).read_bytes() if have and (have / name).is_file() else None
        if data is None or hashlib.sha256(data).hexdigest() != sha:
            with urllib.request.urlopen(GSTATIC + rel, timeout=30) as r:
                data = r.read()
        if hashlib.sha256(data).hexdigest() != sha:
            sys.exit(f'font {name} from fonts.gstatic.com does not match its checksum: update FONTS')
        (APP / 'fonts' / name).write_bytes(data)
    print(f'fonts refreshed in {APP / "fonts"}')


def bundle_fonts():
    """The faces into OUT/fonts/ with their licences, from tool/proto_app/fonts/ (committed: the build needs no
    network for them), each checked against its checksum: a missing or changed file fails the build. Returns the
    @font-face rules and preloads that take the place of the page's Google Fonts stylesheet."""
    out = OUT / 'fonts'
    out.mkdir(parents=True, exist_ok=True)
    rules, preload, done = [], [], set()
    for family, weights, subset, rel, sha in FONTS:
        name = rel.split('/')[-1]
        if name not in done:
            src = APP / 'fonts' / name
            if not src.is_file():
                sys.exit(f'font {name} is missing from {APP / "fonts"} (assemble.py --fetch-fonts fetches it)')
            data = src.read_bytes()
            if hashlib.sha256(data).hexdigest() != sha:
                sys.exit(f'font {name} does not match its checksum in FONTS')
            (out / name).write_bytes(data)
            done.add(name)
        # (block, not swap: the file is beside the page, in within a frame or two, and a frame of a fallback face is not
        # drawn first)
        rules.append(f"@font-face {{ font-family: '{family}'; font-style: normal; font-weight: {weights}; font-display: block; "
                     f"src: url(fonts/{name}) format('woff2'); unicode-range: {RANGES[subset]}; }}")
        if (family, subset) in PRELOAD:
            preload.append(f'<link rel="preload" href="fonts/{name}" as="font" type="font/woff2" crossorigin>')
    for lic in LICENCES.values():
        shutil.copy2(APP / 'fonts' / lic, out / lic)
    # (preloads once each: Readex Pro's file serves every weight)
    return '\n'.join(dict.fromkeys(preload)) + '\n<style>\n  /* the faces bundled with the app (tool/proto_app/assemble.py) */\n  ' + '\n  '.join(rules) + '\n</style>\n'


def copy_module(src_root, rel, seen):
    """Copy a module and, following its relative imports, everything it needs."""
    if rel in seen:
        return
    seen.add(rel)
    src = src_root / rel
    dst = OUT / 'three' / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    for dep in re.findall(r"""(?:from|import)\s*['"](\.{1,2}/[^'"]+)['"]""", src.read_text(encoding='utf-8')):
        copy_module(src_root, os.path.normpath(str(Path(rel).parent / dep)), seen)


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for name in SCRIPTS:
        shutil.copy2(PROTO / name, OUT / name)
    shutil.copytree(PROTO / 'phone', OUT / 'phone')
    sys.path.insert(0, str(REPO / 'tool' / 'proto_engine'))
    import build_worker
    build_worker.build(OUT / 'engine_worker.js')
    for folder in ('terrain', 'models'):
        for f in (PROTO / folder).iterdir():
            if f.is_file():
                shutil.copy2(f, OUT / f.name)
    page = (PROTO / 'farm.html').read_text(encoding='utf-8')
    if CDN not in page:
        sys.exit(f'farm.html does not import three.js from {CDN}: update THREE_VERSION')
    page = page.replace(CDN + 'build/three.module.js', './three/build/three.module.js').replace(CDN + 'examples/jsm/', './three/examples/jsm/')
    faces = bundle_fonts()
    if not GOOGLE_LINK.search(page):
        sys.exit('farm.html does not link the Google Fonts stylesheet as assemble.py expects: update GOOGLE_LINK')
    page = GOOGLE_LINK.sub(lambda m: faces, page, count=1)
    head = ('<!doctype html>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">\n')
    (OUT / 'index.html').write_text(head + page, encoding='utf-8')
    pkg = three_package()
    seen = set()
    copy_module(pkg, 'build/three.module.js', seen)
    for a in ADDONS:
        copy_module(pkg, f'examples/jsm/{a}', seen)
    # every folder that holds a file must be listed in pubspec.yaml (Flutter takes asset folders one level at a time)
    listed = set(re.findall(r'^\s*-\s*(assets/web/\S*)$', (APP / 'pubspec.yaml').read_text(encoding='utf-8'), re.M))
    folders = {('assets/web/' + str(p.parent.relative_to(OUT)) + '/').replace('/./', '/') for p in OUT.rglob('*') if p.is_file()}
    missing = sorted(f for f in folders if f not in listed)
    if missing:
        sys.exit('add these asset folders to pubspec.yaml: ' + ', '.join(missing))
    total = sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())
    print(f'bundled {sum(1 for p in OUT.rglob("*") if p.is_file())} files, {total / 1e6:.1f} MB, into {OUT}')


if __name__ == '__main__':
    fetch_fonts() if '--fetch-fonts' in sys.argv else main()

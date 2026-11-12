#!/usr/bin/env python3
"""Bundle design/prototype3d into tool/proto_app/assets/web/ for the iPhone app.

The page as the app serves it: farm.html as index.html, with a doctype, a charset
and a viewport (the claude.ai artifact skeleton adds these when it publishes), its
scripts, the phone's pictures, the terrain and the models next to it, and three.js
r170 bundled (the import map rewritten from the CDN to the local copy), so only the
web fonts come from the network; and the rules engine compiled for its worker
(tool/proto_engine/build_worker.py, which needs `dart` on the PATH). Run from anywhere; THREE_DIR may name an unpacked
`three@0.170.0` npm package, otherwise it is fetched with `npm pack`.
"""
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


def three_package():
    if os.environ.get('THREE_DIR'):
        return Path(os.environ['THREE_DIR'])
    tmp = Path(tempfile.mkdtemp())
    subprocess.run(['npm', 'pack', f'three@{THREE_VERSION}', '--silent'], cwd=tmp, check=True)
    shutil.unpack_archive(str(next(tmp.glob('three-*.tgz'))), tmp)
    return tmp / 'package'


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
    main()

#!/usr/bin/env python3
"""T11 reviewer: write a GLB's embedded images to outdir (for judging the painted plumage by eye). usage: dump_tex.py file.glb outdir"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glb_read import read_glb
js, b = read_glb(sys.argv[1]); os.makedirs(sys.argv[2], exist_ok=True)
for k, im in enumerate(js.get('images', [])):
    bv = js['bufferViews'][im['bufferView']]; ext = 'png' if 'png' in im.get('mimeType', '') else 'jpg'
    fn = os.path.join(sys.argv[2], f'{os.path.basename(sys.argv[1])[:-4]}_{k}_{im.get("name", "")}.{ext}')
    open(fn, 'wb').write(b[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']]); print(fn)

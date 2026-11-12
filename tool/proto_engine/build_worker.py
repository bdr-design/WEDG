#!/usr/bin/env python3
"""Compile the rules engine's worker (bin/worker.dart) to JavaScript for the 3D prototype.

  python3 tool/proto_engine/build_worker.py [OUT]

OUT defaults to design/prototype3d/engine_worker.js, where the page (engine.js) loads it from; it is built, not
committed. tool/proto_app/assemble.py builds it into the iPhone app's bundle the same way. Needs `dart` on the PATH.
"""
import subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT = HERE.parent.parent / 'design' / 'prototype3d' / 'engine_worker.js'


def build(out):
    out = Path(out).resolve()  # (the compiler runs in this folder: a relative OUT is the caller's)
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['dart', 'compile', 'js', '-O2', '--no-source-maps', str(HERE / 'bin' / 'worker.dart'), '-o', str(out)],
                   cwd=HERE, check=True, stdout=subprocess.DEVNULL)
    Path(str(out) + '.deps').unlink(missing_ok=True)
    return out


if __name__ == '__main__':
    out = build(sys.argv[1] if len(sys.argv) > 1 else DEFAULT)
    print(f'{out} ({out.stat().st_size / 1e3:.0f} KB)')

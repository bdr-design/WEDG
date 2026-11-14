# One textual mutation at a time on the work copy; runs the given tests; restores.
# Usage: python3 -I mutate.py <work_root> <mutations.json> <test_dir> <test_files...>
import json, subprocess, sys, pathlib, os
root = pathlib.Path(sys.argv[1]); muts = json.load(open(sys.argv[2]))
tdir = root / sys.argv[3]; tests = sys.argv[4:]
env = dict(os.environ, PATH='/opt/flutter/bin:/opt/flutter/bin/cache/dart-sdk/bin:' + os.environ['PATH'])
for m in muts:
    f = root / m['file']; src = f.read_text(encoding='utf-8')
    n = src.count(m['old'])
    if n != 1:
        print(f"{m['id']}: SKIP (old found {n} times)"); continue
    f.write_text(src.replace(m['old'], m['new']), encoding='utf-8')
    try:
        r = subprocess.run(['dart', 'test', '--concurrency=2', *tests], cwd=tdir, env=env,
                           capture_output=True, text=True, timeout=900)
        out = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-200:]
        print(f"{m['id']}: {'KILLED' if r.returncode else 'SURVIVED'} | {m['what']} | {out[-90:]}", flush=True)
    finally:
        f.write_text(src, encoding='utf-8')

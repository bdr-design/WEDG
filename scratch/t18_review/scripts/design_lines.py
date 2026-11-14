# Extracts every Arabic text run from the approved design files (phone_falcon.cjs,
# trip.cjs, season.cjs) into one line each, for phase 2's word-for-word check of
# the worker's Arabic. Usage: python3 -I design_lines.py <repo> > design_lines.txt
import re, sys, pathlib
repo = pathlib.Path(sys.argv[1])
files = ['design/ui/phone_falcon.cjs', 'design/hunt/trip.cjs', 'design/hunt/season.cjs']
out = set()
for f in files:
    t = (repo / f).read_text(encoding='utf-8')
    t = re.sub(r'<[^>]+>', '\n', t)            # tags split runs
    t = re.sub(r'[$]\{|\}', '\n', t)        # template holes' edges split runs
    for run in re.split(r"[\n'`\"]", t):
        run = run.strip(' ,;:()[]{}·')
        if re.search(r'[؀-ۿ]', run) and not run.startswith('//'):
            out.add(run)
for s in sorted(out):
    print(s)

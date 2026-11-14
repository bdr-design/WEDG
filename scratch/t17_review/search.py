#!/usr/bin/env python3
"""T11 reviewer: Commons file search (namespace 6). usage: search.py 'query' [limit]"""
import sys, json, time, urllib.request, urllib.parse, subprocess
q = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(dict(action='query', list='search', srsearch=sys.argv[1], srnamespace=6, srlimit=int(sys.argv[2]) if len(sys.argv) > 2 else 40, format='json'))
for k in range(5):
    r = subprocess.run(['curl', '-sS', '-m', '40', q], capture_output=True, text=True)
    try: d = json.loads(r.stdout); break
    except Exception: time.sleep(20 * (k + 1))
for m in d['query']['search']: print(m['title'])

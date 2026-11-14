#!/usr/bin/env python3
"""T11 reviewer: list a Commons category (files only), politely (one request, retry on 429)."""
import sys, json, time, urllib.request, urllib.parse
def api(params):
    url = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(dict(params, format='json'))
    for k in range(6):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'MarahReview/1.0 (one-off review script)'}), timeout=30)
            return json.load(r)
        except Exception as e:
            time.sleep(20 * (k + 1))
    raise SystemExit('gave up')
if __name__ == '__main__':
    if sys.argv[1] == 'cat':
        d = api(dict(action='query', list='categorymembers', cmtitle=sys.argv[2], cmlimit=500, cmtype='file|subcat'))
        for m in d['query']['categorymembers']: print(m['title'])
    elif sys.argv[1] == 'info':
        d = api(dict(action='query', titles='|'.join(sys.argv[2:]), prop='imageinfo', iiprop='url|size|extmetadata', iiurlwidth=960, iiextmetadatafilter='Artist|LicenseShortName|ImageDescription'))
        for p in d['query']['pages'].values():
            ii = p.get('imageinfo', [{}])[0]
            em = ii.get('extmetadata', {})
            print(json.dumps(dict(title=p['title'], w=ii.get('width'), h=ii.get('height'), thumb=ii.get('thumburl'),
                  artist=em.get('Artist', {}).get('value', '')[:120], lic=em.get('LicenseShortName', {}).get('value'),
                  desc=em.get('ImageDescription', {}).get('value', '')[:200]), ensure_ascii=False))

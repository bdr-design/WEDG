#!/bin/bash
# T11 reviewer: fetch Commons thumbnails slowly with curl (its default agent); URL computed from the file name.
# usage: fetch.sh W outdir listfile  -> outdir/<md5-8>.jpg, outdir/index.tsv (file, name, url)
W=$1; OUT=$2
while IFS= read -r name; do
  [ -z "$name" ] && continue
  read h url < <(python3 -I -c 'import sys,hashlib,urllib.parse as u;n=sys.argv[1].replace(" ","_");h=hashlib.md5(n.encode()).hexdigest();q=u.quote(n);print(h[:8],f"https://upload.wikimedia.org/wikipedia/commons/thumb/{h[0]}/{h[:2]}/{q}/{sys.argv[2]}px-{q}")' "$name" $W)
  f=$OUT/$h.jpg; [ -s $f ] && continue
  for k in 1 2 3 4; do
    c=$(curl -sS -m 40 -o $f -w '%{http_code}' "$url"); [ "$c" = 200 ] && break
    echo "retry $k $c $name"; rm -f $f; [ "$c" = 400 -o "$c" = 404 ] && break; python3 -c "import time;time.sleep(20*$k)"
  done
  [ -s $f ] && { printf '%s\t%s\t%s\n' $f "$name" "$url" >> $OUT/index.tsv; echo "ok $name"; }
  python3 -c "import time;time.sleep(3)"
done < $3

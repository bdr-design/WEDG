import json,sys
p=sys.argv[1]; n=int(sys.argv[2]) if len(sys.argv)>2 else 9000
last=None
with open(p,errors='replace') as f:
    for line in f:
        try: o=json.loads(line)
        except Exception: continue
        m=o.get('message') or {}
        if m.get('role')!='assistant': continue
        c=m.get('content')
        if isinstance(c,list):
            for b in c:
                if b.get('type')=='text' and len(b.get('text',''))>200: last=b['text']
                if b.get('type')=='tool_use' and 'andback' in b.get('name',''):
                    last=json.dumps(b.get('input'),ensure_ascii=False)
print((last or 'NONE')[:n])

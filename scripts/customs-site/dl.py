import json, os, re, urllib.request, urllib.parse, time
UA={'User-Agent':'Mozilla/5.0'}
o=json.load(open('customs_files.json'))
start=time.time(); n=0; skipped=0; failed=[]
for x in o:
    if time.time()-start>150: print('PAUSE'); break
    cat=x['category'].strip('/').split('/')[-1]
    name=urllib.parse.unquote(x['file'].split('/')[-1])
    name=re.sub(r'[\\/:*?"<>|]','_',name)
    d=os.path.join('files',cat); os.makedirs(d,exist_ok=True)
    p=os.path.join(d,name)
    if os.path.exists(p) and os.path.getsize(p)>0: skipped+=1; continue
    try:
        r=urllib.request.urlopen(urllib.request.Request(x['file'],headers=UA),timeout=120)
        data=r.read(); open(p,'wb').write(data); n+=1
    except Exception as e: failed.append((x['file'],str(e)[:80]))
print('downloaded',n,'already',skipped,'failed',len(failed)); [print(' ',f) for f in failed[:10]]

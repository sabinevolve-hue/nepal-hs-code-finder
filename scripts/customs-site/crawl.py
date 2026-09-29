import re, html, json, urllib.request, time
UA={'User-Agent':'Mozilla/5.0'}
def get(u):
    for _ in range(2):
        try: return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=40).read().decode('utf-8','ignore')
        except Exception as e: time.sleep(1)
    return ''
def h1(h):
    m=re.search(r'<h1[^>]*>(.*?)</h1>',h,re.S); return html.unescape(re.sub(r'<[^>]+>','',m.group(1))).strip() if m else ''
base='https://customs.gov.np'
home=get(base+'/content/1139/ftskkksss/')
cats=sorted(set(c.strip() for c in re.findall(r'href="\s*(/category/[^"]+?)\s*"',home)))
import os,sys
state=json.load(open('state.json')) if os.path.exists('state.json') else {'done':[],'out':[]}
out=state['out']; seen=set(o['page'] for o in out)
start=time.time()
for c in cats:
    if c in state['done']: continue
    if time.time()-start>140: print('PAUSE'); break
    items=[]
    for pg in range(1,30):
        h=get(base+c.rstrip('/')+'/'+(f'?page={pg}' if pg>1 else ''))
        if not h: break
        cards=re.findall(r'class="grid__card".*?</h3>',h,re.S)
        new=[]
        for cd in cards:
            m=re.search(r'href="\s*(/content/[^"]+?)\s*"[^>]*>\s*(.*?)\s*</a>',cd,re.S)
            if m and m.group(1) not in [x[0] for x in items]: new.append((m.group(1),html.unescape(re.sub(r'<[^>]+>','',m.group(2))).strip()))
        if not new: break
        items+=new
        if 'page=%d'%(pg+1) not in h: break
    ct=h1(get(base+c)) if items else ''
    for it,title in items:
        if base+it in seen: continue
        seen.add(base+it)
        ph=get(base+it)
        m=re.search(r'<main.*?</main>',ph,re.S); body=m.group(0) if m else ph
        date=re.search(r'(\d{1,2}\s+\S+,\s*२?[०-९]{4}|[०-९]{1,2}\s+\S+,\s*[०-९]{4})',re.sub(r'<[^>]+>',' ',body))
        for f,txt in re.findall(r'<a[^>]+href="\s*(https?://[^"]+?\.(?:xlsx|xls|pdf|csv|zip|docx?|rar))\s*"[^>]*>(.*?)</a>',body,re.S|re.I):
            out.append(dict(category=c,category_title=ct,page=base+it,page_title=title,date=date.group(1) if date else '',link_text=html.unescape(re.sub(r'<[^>]+>','',txt)).strip(),file=html.unescape(f)))
        time.sleep(0.2)
    print(c,'|',ct,'| pages',len(items),'| files',len([o for o in out if o['category']==c]),flush=True)
    state['done'].append(c); json.dump(state,open('state.json','w'),ensure_ascii=False)
json.dump(out,open('customs_files.json','w'),ensure_ascii=False,indent=1)
import csv
w=csv.writer(open('customs_files.csv','w',newline='')); w.writerow(['category','category_title','page','page_title','date','link_text','file'])
for o in out: w.writerow([o[k] for k in ['category','category_title','page','page_title','date','link_text','file']])
print('TOTAL files',len(out))

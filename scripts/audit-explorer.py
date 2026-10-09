"""Replay every published aggregate against saved source records; separately audit live DOIs.
Does not import or execute the builder. No browser automation or synthetic research records.
"""
import collections, concurrent.futures, datetime, gzip, hashlib, json, re, sys, time, unicodedata, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'explorer/data'; BOOK=ROOT.parent/'syeds-research-book/data'
OUT=ROOT.parent/'output/journal-explorer'; OUT.mkdir(parents=True,exist_ok=True)
def read(p):return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_text(encoding='utf-8-sig'))
def norm(s):return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',s or '').lower())
catalog=read(DATA/'catalog.json'); registry=read(BOOK/'management-journals.json'); manifest=read(BOOK/'management/manifest.json')
assert catalog['inputManifestSha256']==hashlib.sha256((BOOK/'management/manifest.json').read_bytes()).hexdigest(), 'Input release manifest changed'
reg={r['scopusSourceId']:r for r in registry['journals'] if r['sourceType']=='journal'}
published={j['id']:read(DATA/(j['id']+'.json')) for j in catalog['journals']}
assert set(reg)==set(published)
sources=collections.defaultdict(set); aliases=collections.defaultdict(set); names=collections.defaultdict(set)
for k,r in reg.items():
    if r.get('sourceMatch')=='exact-issn' and r.get('sourceId'):sources[r['sourceId']].add(k)
    names[norm(r['name'])].add(k)
    for s in [r['name'],r.get('sourceName')]:
        if s:aliases[norm(s)].add(k)
def single(values):return next(iter(values)) if len(values)==1 else None
def journal_id(p):
    exact=single(sources[p.get('sourceId')])
    if exact:return exact
    name=norm(p.get('journal'));return single(names[name]) or single(aliases[name])
patterns={k:re.compile(r'\b(?:'+v['pattern']+r')\b',re.I) for k,v in catalog['topics'].items()}
years=collections.defaultdict(collections.Counter); topics=collections.defaultdict(lambda:collections.defaultdict(collections.Counter))
expected={}; examples=0; metadata_errors=[]
for k,j in published.items():
    for field in ['name','publisher','issns','sourceId','quartile','rankingYear','status']:
        if j.get(field)!=reg[k].get(field):metadata_errors.append([k,field])
    for sample in j['recent']+[p for t in j['topics'].values() for p in t['examples']]:
        key=(sample.get('doi') or sample.get('openalexId') or '').lower().removeprefix('https://doi.org/')
        expected.setdefault(key,[]).append((k,sample)); examples+=1
seen=set(); verified=set(); sample_errors=[]; source_hashes={}; scanned=0
files=[BOOK/'papers.index.json',BOOK/'recent.index.json']+[BOOK/'management'/f['path'] for f in manifest['files'] if f['sourceType']=='journal']
for i,path in enumerate(files):
    source_hashes[str(path.relative_to(BOOK))]=hashlib.sha256(path.read_bytes()).hexdigest()
    for p in read(path):
        scanned+=1
        if p.get('sourceType') not in (None,'journal') or p.get('type') not in ('article','review','journal-article'):continue
        jid=journal_id(p)
        if not jid:continue
        key=(p.get('doi') or p.get('openalexId') or p.get('id') or '').lower().removeprefix('https://doi.org/')
        if not key or key in seen:continue
        seen.add(key); y=p.get('year')
        if not isinstance(y,int) or not 1800<=y<=2026:continue
        years[jid][y]+=1
        if key in expected:
            for sample_jid,sample in expected[key]:
                if sample_jid!=jid or any(sample.get(f)!=p.get(f) for f in ['title','doi','year','openalexId']):sample_errors.append({'key':key,'journal':sample_jid})
            verified.add(key)
        if y>=2018:
            # Each lens searches independently, so overlapping phrases are not swallowed.
            for t,rx in patterns.items():
                if rx.search(p.get('title') or ''):topics[jid][t][y]+=1
    if i%75==0:print('Audited source files',i,'/',len(files),flush=True)
count_errors=[]; topic_errors=[]
for k,j in published.items():
    if dict(years[k])!={int(y):n for y,n in j['years'].items()}:count_errors.append(k)
    for t in set(topics[k])|set(j['topics']):
        old={int(y):n for y,n in j['topics'].get(t,{}).get('years',{}).items()}
        if dict(topics[k][t])!=old:topic_errors.append({'journal':k,'topic':t,'published':old,'recomputed':dict(topics[k][t])})
report={'checkedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'All Explorer aggregates and displayed paper examples replayed against saved Research Book inputs. This establishes derivation, not independent confirmation that provider metadata is error-free.','journals':len(published),'sourceRowsScanned':scanned,'records':sum(sum(c.values()) for c in years.values()),'paperExampleOccurrences':examples,'uniquePaperExamples':len(expected),'verifiedUniquePaperExamples':len(verified),'metadataErrors':metadata_errors,'annualCountErrors':count_errors,'topicCountErrors':topic_errors,'paperExampleErrors':sample_errors,'missingPaperExamples':list(set(expected)-verified),'sourceFileHashes':source_hashes}
report['status']='PASS' if not any(report[k] for k in ['metadataErrors','annualCountErrors','topicCountErrors','paperExampleErrors','missingPaperExamples']) else 'FAIL'
(OUT/'corpus-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k not in ['sourceFileHashes','topicCountErrors']} | {'topicCountErrors':len(topic_errors)}),flush=True)

if '--skip-crossref' in sys.argv:
    raise SystemExit(0 if report['status']=='PASS' else 1)

saved=read(DATA/'job-crossref.json')
def verify_doi(p):
    url='https://api.crossref.org/works/'+p['DOI']
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'ScholarScope-EvidenceAudit/1.0'})
            with urllib.request.urlopen(req,timeout=45) as r:raw=r.read();live=json.loads(raw)['message']
            # Crossref list and individual endpoints serialize absent title/relation
            # as null vs []/{}. Treat only these documented empty shapes as equivalent.
            empty_shapes={'title':[], 'relation':{}}
            equivalent=[k for k,empty in empty_shapes.items() if p.get(k)!=live.get(k) and p.get(k) in (None,empty) and live.get(k) in (None,empty)]
            mismatches=[k for k,v in p.items() if live.get(k)!=v and k not in equivalent]
            return {'doi':p['DOI'],'issnVerified':bool(set(live.get('ISSN',[]))&{'0894-3796','1099-1379'}),'mismatchedFields':mismatches,'equivalentEmptyFields':equivalent,'source':url,'responseSha256':hashlib.sha256(raw).hexdigest()}
        except Exception as e:
            if attempt==2:return {'doi':p['DOI'],'error':str(e)}
            time.sleep(attempt+1)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:checks=list(pool.map(verify_doi,saved['papers']))
live_report={'checkedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'records':checks,'status':'PASS' if all(x.get('issnVerified') and not x.get('mismatchedFields') and not x.get('error') for x in checks) else 'REVIEW'}
(OUT/'crossref-audit.json').write_text(json.dumps(live_report,indent=2),encoding='utf8')
print('Crossref audit:',live_report['status'],len(checks),'DOIs',flush=True)
if report['status']!='PASS' or live_report['status']!='PASS':raise SystemExit(1)

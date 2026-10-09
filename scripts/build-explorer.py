"""Derive Journal Explorer from the existing provider-backed Research Book. No AI data."""
import collections, gzip, hashlib, json, re, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT.parent / 'syeds-research-book' / 'data'
OUT = ROOT / 'explorer' / 'data'
OUT.mkdir(parents=True, exist_ok=True)
def read(p):
    return json.loads(gzip.decompress(p.read_bytes()) if p.suffix == '.gz' else p.read_text(encoding='utf-8-sig'))
def write(p, x):
    p.write_text(json.dumps(x, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
def norm(x):
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', x or '').lower())

# Transparent, overlapping title-only search lenses; these are NOT validated constructs.
TOPICS = {
 'ai': ('AI & algorithmic work', r'artificial intelligence|generative ai|human.ai|algorithmic|chatgpt|machine learning'),
 'change': ('Organizational change', r'organizational change|organisational change|change readiness|change process|change management|organizational transformation'),
 'health': ('Health, illness & disability', r'chronic illness|chronic disease|disabilit\w*|mental health|physical health|menopaus\w*|reproductive health'),
 'leadership': ('Leadership', r'leader\w*|supervisor\w*'),
 'wellbeing': ('Wellbeing & burnout', r'well.being|wellbeing|burnout|emotional exhaustion|occupational stress'),
 'identity': ('Identity & identification', r'identit\w*|identification'),
 'justice': ('Fairness & justice', r'fairness|unfair\w*|justice|injustice'),
 'inclusion': ('Diversity & inclusion', r'diversit\w*|inclusi\w*|discrimination|gender|racial|racism|stigma\w*'),
 'teams': ('Teams & collaboration', r'team\w*|collaborat\w*|cooperat\w*'),
 'remote': ('Remote & flexible work', r'remote work|hybrid work|telework\w*|work.from.home|flexible work|compressed workweek\w*'),
 'careers': ('Careers & employability', r'career\w*|employability|job search|retirement'),
 'motivation': ('Motivation & engagement', r'motivation|motivational|work engagement|employee engagement|self.determination'),
 'voice': ('Voice & psychological safety', r'employee voice|speaking up|psychological safety|employee silence|whistleblow\w*'),
 'ethics': ('Ethics & misconduct', r'ethic\w*|unethical|misconduct|moral\w*|deviance|corruption'),
 'innovation': ('Innovation & creativity', r'innovat\w*|creativ\w*|idea generation'),
 'knowledge': ('Knowledge & learning', r'knowledge\w*|learning|skill\w*'),
 'workfamily': ('Work–family boundaries', r'work.family|family.work|work.life|boundary management'),
 'sustainability': ('Sustainability & climate', r'sustainab\w*|climate change|green\w*|environmental performance'),
 'entrepreneurship': ('Entrepreneurship', r'entrepreneur\w*|start.up\w*|new venture\w*'),
 'consumer': ('Consumers & marketing', r'consumer\w*|customer\w*|brand\w*|marketing'),
 'strategy': ('Strategy & capabilities', r'strateg\w*|dynamic capabilit\w*|competitive advantage'),
 'trust': ('Trust & relationships', r'trust|distrust|social exchange|leader.member exchange|interpersonal relationship\w*'),
 'jobdesign': ('Job design & autonomy', r'job design|job crafting|job autonomy|work design|job demands|job resources'),
 'turnover': ('Turnover & retention', r'turnover|employee retention|quit\w*'),
 'power': ('Power & status', r'power|status|hierarch\w*'),
}
pattern = re.compile('|'.join(r'(?P<'+k+r'>\b(?:'+v[1]+r')\b)' for k,v in TOPICS.items()), re.I)
registry = read(BOOK/'management-journals.json')
manifest = read(BOOK/'management/manifest.json')
journals = {j['scopusSourceId']:j for j in registry['journals'] if j['sourceType']=='journal'}
source_candidates = collections.defaultdict(set)
for k,j in journals.items():
    if j.get('sourceId') and j.get('sourceMatch')=='exact-issn': source_candidates[j['sourceId']].add(k)
# Renamed journals sometimes share an OpenAlex source. Never assign these by last row.
by_source = {s:next(iter(ids)) for s,ids in source_candidates.items() if len(ids)==1}
names = collections.defaultdict(set)
for k,j in journals.items():
    for n in [j['name'], j.get('sourceName','')]:
        if n: names[norm(n)].add(k)
by_name = {n:next(iter(ids)) for n,ids in names.items() if len(ids)==1}
canonical_names = collections.defaultdict(set)
for k,j in journals.items(): canonical_names[norm(j['name'])].add(k)
by_name.update({n:next(iter(ids)) for n,ids in canonical_names.items() if len(ids)==1})
stats = {}
seen = set()
def brief(p):
    return {k:p.get(k) for k in ['title','doi','year','openalexId']}
def keep(rows,p,limit):
    rows.append(brief(p)); rows.sort(key=lambda x:(x['year'] or 0, x['doi'] or ''),reverse=True); del rows[limit:]
def ingest(p):
    if p.get('sourceType') not in (None,'journal') or p.get('type') not in ('article','review','journal-article'): return
    k=by_source.get(p.get('sourceId'))
    if not k: k=by_name.get(norm(p.get('journal')))
    if not k:return
    key=(p.get('doi') or p.get('openalexId') or p.get('id') or '').lower().removeprefix('https://doi.org/')
    if not key or key in seen:return
    seen.add(key)
    y=p.get('year')
    if not isinstance(y,int) or not 1800<=y<=2026:return
    s=stats.setdefault(k,{'years':collections.Counter(),'topics':{},'recent':[],'count':0,'doiCount':0,'titleCount':0,'identity':collections.Counter()})
    s['count']+=1; s['years'][y]+=1; s['doiCount']+=bool(p.get('doi')); s['titleCount']+=bool(p.get('title')); s['identity']['source-id' if by_source.get(p.get('sourceId')) else 'exact-normalized-title']+=1
    if y>=2023:keep(s['recent'],p,12)
    if y<2018:return
    for t in {m.lastgroup for m in pattern.finditer(p.get('title') or '')}:
        ts=s['topics'].setdefault(t,{'years':collections.Counter(),'examples':[]})
        ts['years'][y]+=1
        if y>=2022:keep(ts['examples'],p,5)
for f in ['papers.index.json','recent.index.json']:
    for p in read(BOOK/f):ingest(p)
files=[x for x in manifest['files'] if x['sourceType']=='journal']
for i,f in enumerate(files):
    for p in read(BOOK/'management'/f['path']):ingest(p)
    if i%75==0:print('shards',i,'/',len(files),flush=True)
catalog=[]
for k,j in journals.items():
    s=stats.get(k,{'count':0,'years':{},'topics':{},'recent':[],'doiCount':0,'titleCount':0,'identity':{}})
    meta={a:j.get(a) for a in ['name','publisher','issns','sourceId','quartile','rankingYear','status']}
    meta.update(id=k, count=s['count'])
    catalog.append(meta)
    write(OUT/(k+'.json'),{**meta,**s})
catalog.sort(key=lambda j:j['name'].casefold())
write(OUT/'catalog.json',{'generatedAt':'2026-10-10','corpusGeneratedAt':manifest['generatedAt'],'snapshotRelease':'2026-09-23','scope':'Existing Research Book management registry; article/review provider types only. Coverage varies by journal; not a complete publisher archive. Source identity uses exact ISSN-backed OpenAlex IDs or unique normalized registry titles.','topics':{k:{'label':v[0],'pattern':v[1]} for k,v in TOPICS.items()},'journals':catalog,'records':sum(j['count'] for j in catalog),'inputManifestSha256':hashlib.sha256((BOOK/'management/manifest.json').read_bytes()).hexdigest()})
print(json.dumps({'journals':len(catalog),'withRecords':sum(j['count']>0 for j in catalog),'records':sum(j['count'] for j in catalog),'JOB':stats.get('30020',{}).get('count')}))

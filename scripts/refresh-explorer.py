"""Refresh JOB Crossref metadata. Publisher calls require separate human review."""
import datetime, json, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'explorer/data'
URL='https://api.crossref.org/journals/0894-3796/works?rows=100&sort=published&order=desc'
def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'ScholarScope-JournalExplorer/1.0 (public scholarly metadata)'})
    with urllib.request.urlopen(req,timeout=90) as r:return json.load(r)['message']
data=get(URL)
early=['10.1002/job.70132','10.1002/job.70131','10.1002/job.70130','10.1002/job.70129']
items={p['DOI'].lower():p for p in data['items']}
for doi in early:
    if doi not in items:items[doi]=get('https://api.crossref.org/works/'+doi)
papers=[]
for p in items.values():
    if not set(p.get('ISSN',[])) & {'0894-3796','1099-1379'}:raise ValueError('Wrong journal')
    papers.append({k:p.get(k) for k in ['DOI','title','author','published','published-online','published-print','accepted','volume','issue','type','relation','URL']})
result={'retrievedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':URL,'totalResults':data['total-results'],'limit':100,'papers':papers,'publisherEarlyViewDois':early,'earlyViewCheckedAt':'2026-10-10','earlyViewSource':'https://onlinelibrary.wiley.com/toc/10991379/0/0'}
(ROOT/'job-crossref.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print(json.dumps({'verifiedPapers':len(papers),'earlyViewVerified':len(early)}))

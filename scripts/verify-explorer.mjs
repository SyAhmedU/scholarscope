import assert from 'node:assert/strict';
import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
import {topicSignals,schedule,calendar,callStatus,shiftDays} from '../explorer/model.mjs';
const data=fileURLToPath(new URL('../explorer/data/',import.meta.url));
const read=n=>JSON.parse(fs.readFileSync(data+n,'utf8'));
const catalog=read('catalog.json');let count=0;
for(const meta of catalog.journals){
 const j=read(meta.id+'.json');assert.equal(j.id,meta.id);assert.equal(j.count,meta.count);
 assert.equal(Object.values(j.years).reduce((a,b)=>a+b,0),j.count);count+=j.count;
 assert(j.doiCount<=j.count);assert(j.titleCount<=j.count);
 for(const t of Object.values(j.topics))for(const [year,n] of Object.entries(t.years))assert(n<=j.years[year]);
 for(const t of topicSignals(j,catalog)){assert(Number.isFinite(t.delta));if(t.enough)assert(t.n0>=40&&t.n1>=40&&t.b>=5);}
}
assert.equal(count,catalog.records);
const job=read('30020.json');assert.equal(job.name,'Journal of Organizational Behavior');assert(job.count>2000);
const ed=read('job-editorial.json'),cr=read('job-crossref.json');
for(const doi of cr.publisherEarlyViewDois)assert(cr.papers.some(p=>p.DOI.toLowerCase()===doi));
assert.equal(new Set(cr.papers.map(p=>p.DOI.toLowerCase())).size,cr.papers.length);
const chronic=ed.calls.find(c=>c.id==='illness');assert.equal(chronic.deadline,'2027-06-30');
assert.equal(callStatus(chronic,'2027-05-31'),'Upcoming');assert.equal(callStatus(chronic,'2027-06-30'),'Open');assert.equal(callStatus(chronic,'2027-07-01'),'Closed');
// Deliberately simulated boundary inputs; no fixtures are published as research evidence.
const sparse=topicSignals({years:{2022:1,2024:1},topics:{ai:{years:{2024:1}}}},catalog)[0];assert(!sparse.enough);
const large=topicSignals({years:{2022:100,2024:1000},topics:{ai:{years:{2022:10,2024:20}}}},catalog)[0];assert(large.delta<0,'More papers can still mean a smaller share');
const rows=schedule({target:'2027-06-30',route:'empirical'});assert.equal(rows.at(-1).end,'2027-06-30');
for(let i=1;i<rows.length;i++)assert.equal(rows[i-1].end,rows[i].start);
assert.equal(schedule({target:'2027-06-30',route:'empirical',stage:5}).length,2);
assert.equal(shiftDays('2028-02-28',1),'2028-02-29');
const ics=calendar(rows,'Journal, with; delimiters','test');assert(ics.includes('Journal\\, with\\; delimiters'));assert(ics.endsWith('END:VCALENDAR\r\n'));assert(!ics.includes('undefined'));
console.log(JSON.stringify({status:'PASS',journals:catalog.journals.length,records:count,JOB:job.count,crossref:cr.papers.length}));

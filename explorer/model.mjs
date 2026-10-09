export const AS_OF = '2026-10-10';
export const SUM = (o, years) => years.reduce((s,y)=>s+(o?.[y]||0),0);
export const shiftDays = (date, n) => new Date(Date.parse(date+'T12:00:00Z')+n*86400000).toISOString().slice(0,10);
export function topicSignals(journal, catalog) {
  const before=[2022,2023], after=[2024,2025];
  const n0=SUM(journal.years,before),n1=SUM(journal.years,after);
  return Object.entries(journal.topics||{}).map(([id,t])=>{
    const a=SUM(t.years,before),b=SUM(t.years,after),p0=n0?a/n0:0,p1=n1?b/n1:0;
    const enough=n0>=40&&n1>=40&&b>=5;
    const delta=(p1-p0)*100;
    return {id,...t,label:catalog.topics[id].label,a,b,n0,n1,p0,p1,delta,enough,
      direction:!enough?'Sparse evidence':delta>1?'Gaining share':delta< -1?'Losing share':'Broadly steady'};
  }).sort((a,b)=>Number(b.enough)-Number(a.enough)||b.delta-a.delta||b.b-a.b);
}
export function callStatus(call,today){return today>call.deadline?'Closed':today<call.open?'Upcoming':'Open';}
export const PHASES={
 empirical:[['Scope & contribution',3,'Read the nearest papers and specify the theoretical contribution.'],['Design, access & ethics',5,'Secure access and required ethics review; justify measures, sampling and analysis.'],['Pilot & refine',3,'Pilot instruments and procedures; resolve feasibility issues.'],['Collect evidence',12,'Run the approved design, document deviations and protect participants.'],['Analyze & stress-test',5,'Check assumptions, alternative explanations and reproducibility.'],['Write & coauthor review',6,'Develop the argument, report limitations and obtain coauthor feedback.'],['Submission checks',2,'Check fit, anonymity, reporting, declarations and current author instructions.']],
 review:[['Scope & theoretical tension',4,'Specify what the review explains beyond a summary.'],['Protocol & search design',4,'Set reproducible sources, inclusion rules and synthesis approach.'],['Screen & extract',10,'Record decisions and check extraction independently.'],['Synthesize & develop theory',8,'Evaluate competing explanations and substantiate the contribution.'],['Write & coauthor review',6,'Connect synthesis, theory and practical implications.'],['Submission checks',2,'Check current author instructions, references and transparency.']],
 proposal:[['Preliminary scoping',2,'Establish the problem without completing the proposed research.'],['Develop the contribution',3,'Explain the theoretical tension and intended advance.'],['Write the development plan',2,'Set out how the full paper will be developed if invited.'],['Proposal checks',1,'Check the current call, page limit, anonymity and key references.']],
 guest:[['Develop issue rationale',3,'Establish a distinctive topic and why a special issue is appropriate.'],['Assemble editorial proposal',4,'Check the current call for editorial team, scope and process requirements.'],['Proposal review',2,'Review the proposal against the guest-editor call.']]
};
export function schedule({target,route='empirical',durations,stage=0}){
  const phases=PHASES[route]||PHASES.empirical;
  const rows=phases.map((p,i)=>({name:p[0],detail:p[2],weeks:Math.max(1,Math.min(104,Number(durations?.[i])||p[1])),index:i})).slice(stage);
  let end=target;
  for(let i=rows.length-1;i>=0;i--){rows[i].end=end;rows[i].start=shiftDays(end,-rows[i].weeks*7);end=rows[i].start;}
  return rows;
}
export function icsEscape(s){return String(s).replaceAll('\\','\\\\').replaceAll('\n','\\n').replaceAll(',','\\,').replaceAll(';','\\;');}
export function calendar(rows,journal,id){
  const stamp=new Date().toISOString().replace(/[-:]/g,'').replace(/\.\d{3}Z/,'Z');
  const lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//ScholarScope//Journal Explorer//EN','CALSCALE:GREGORIAN'];
  for(const r of rows)lines.push('BEGIN:VEVENT',`UID:je-${id}-${r.index}-${r.end}@scholarscope`, `DTSTAMP:${stamp}`,`DTSTART;VALUE=DATE:${r.end.replaceAll('-','')}`,`DTEND;VALUE=DATE:${shiftDays(r.end,1).replaceAll('-','')}`,`SUMMARY:${icsEscape(r.name+' — '+journal)}`,`DESCRIPTION:${icsEscape(r.detail+' Planning milestone; not a publisher promise.')}`,'END:VEVENT');
  lines.push('END:VCALENDAR');
  return lines.map(line=>{let out='',bytes=0;for(const c of line){const n=new TextEncoder().encode(c).length;if(bytes+n>73){out+='\r\n ';bytes=1;}out+=c;bytes+=n;}return out;}).join('\r\n')+'\r\n';
}

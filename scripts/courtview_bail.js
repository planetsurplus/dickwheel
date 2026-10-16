// CourtView bail lookup. Run on https://records.courts.alaska.gov/robots.txt (a plain page Wicket can't redirect).
// Progress is kept in localStorage so a page reload loses nothing.
// Use: paste this file, cvStart([...case numbers]), then call `await cvRun(20000)` repeatedly until remaining is 0,
// then JSON.stringify(cvSummary(date, weekStart)). After a reload: eval(localStorage.getItem('cvSrc')) is NOT kept by this file; just paste it again.
window.cvLookup = async function(caseNo){
  const sleep=ms=>new Promise(r=>setTimeout(r,ms));
  let f=document.getElementById('cvf');
  if(!f){f=document.createElement('iframe');f.id='cvf';f.setAttribute('sandbox','allow-scripts allow-same-origin allow-forms');f.style.cssText='position:fixed;left:-9999px;width:1200px;height:900px';document.body.appendChild(f);}
  const waitFor=async(fn,ms=15000)=>{const t0=Date.now();while(Date.now()-t0<ms){try{const v=fn();if(v)return v;}catch(e){}await sleep(200);}return null;};
  const doc=()=>f.contentDocument;
  f.src='/eaccess/search.page?'+Date.now();
  let el=await waitFor(()=>doc().readyState==='complete'&&(doc().querySelector('#caseDscr')||doc().querySelector('input[name="linkFrag:beginButton"]')));
  if(!el) return {caseNo,err:'no page'};
  if(el.id!=='caseDscr'){ el.click(); el=await waitFor(()=>doc().readyState==='complete'&&doc().querySelector('#caseDscr')); if(!el) return {caseNo,err:'no search form'}; }
  const w=f.contentWindow;
  Object.getOwnPropertyDescriptor(w.HTMLInputElement.prototype,'value').set.call(el,caseNo);
  el.dispatchEvent(new w.Event('input',{bubbles:true}));el.dispatchEvent(new w.Event('change',{bubbles:true}));
  doc().querySelector('input[name="submitLink"]').click();
  await sleep(300);
  const a=await waitFor(()=>{const d=doc(); if(d.readyState!=='complete')return null; const t=d.body.innerText; if(/Docket Information/.test(t)&&t.includes(caseNo))return 'detail'; if(/No cases? (were )?found|no records/i.test(t))return 'none'; return [...d.querySelectorAll('a')].find(x=>x.textContent.trim()===caseNo);});
  if(!a) return {caseNo,err:'no result'};
  if(a==='none') return {caseNo,err:'not found'};
  if(a!=='detail'){ a.click(); await sleep(300); const ok=await waitFor(()=>doc().readyState==='complete'&&/Docket Information/.test(doc().body.innerText)); if(!ok) return {caseNo,err:'no detail'}; }
  const t=doc().body.innerText;
  const iso=(m,d,y)=>`${y}-${m}-${d}`;
  const dk=(t.split('Docket Information')[1]||'').split('Financial Summary')[0];
  const fin=t.split('Financial Docket Information')[1]||'';
  // posted bonds: the financial docket carries the amount even when the docket line doesn't
  let bail=[...fin.matchAll(/(\d\d)\/(\d\d)\/(\d{4})\tBail Info:\t\$([\d,]+\.\d\d)/g)].map(m=>({date:iso(m[1],m[2],m[3]),amount:+m[4].replace(/,/g,'')}));
  if(!bail.length) bail=[...dk.matchAll(/(\d\d)\/(\d\d)\/(\d{4})\tBail Info: \$([\d,]+\.\d\d)/g)].map(m=>({date:iso(m[1],m[2],m[3]),amount:+m[4].replace(/,/g,'')}));
  const status=[...t.matchAll(/Bond Status: ([^\n]*)/g)].map(m=>m[1].trim());
  // warrants: "Bail Amount (Warrants Only): $5000 Performance ... issued on: 10/14/2026"
  const warrants=[...dk.matchAll(/Bail Amount \(Warrants Only\): \$([\d,]+(?:\.\d\d)?)\s*([A-Za-z]*)[\s\S]{0,300}?issued on: (\d\d)\/(\d\d)\/(\d{4})/g)].map(m=>({date:iso(m[3],m[4],m[5]),amount:+m[1].replace(/,/g,''),type:m[2]||null}));
  return {caseNo,bail,status,warrants,recalled:/Warrant (Recalled|Quashed)|Recall(ed)? Warrant|Quash/i.test(dk),
    schedule:/Release per Schedule/i.test(dk),
    conditions:/Conditions of Release|Bail Order|Release Order/i.test(dk)&&!/Release per Schedule/i.test(dk),
    summons:/Summons/i.test(dk), warrant:/Warrant/i.test(dk)};
};
window.cvLoad=()=>JSON.parse(localStorage.getItem('cvBail')||'{"queue":[],"results":{}}');
window.cvSave=s=>localStorage.setItem('cvBail',JSON.stringify(s));
window.cvStart=queue=>{cvSave({queue,results:{}});return queue.length;};
window.cvRun=async function(budgetMs=20000){
  // keep each call under ~20s; a guard stops two loops sharing the iframe
  if(window.cvBusy) return {busy:true}; window.cvBusy=true;
  try{
  const t0=Date.now(), s=cvLoad();
  while(Date.now()-t0<budgetMs){
    const c=s.queue.find(x=>!s.results[x]||(s.results[x].err&&!s.results[x].retried&&s.results[x].err!=='not found'));
    if(!c)break;
    const prev=s.results[c]; const r=await cvLookup(c); if(r.err&&prev)r.retried=true;
    s.results[c]=r; cvSave(s);
    await new Promise(r=>setTimeout(r,1500)); // be gentle with the court's server
  }
  const R=Object.values(s.results);
  return {done:R.filter(r=>!r.err).length,total:s.queue.length,errors:R.filter(r=>r.err&&r.err!=='not found').map(r=>r.caseNo+':'+r.err),
          remaining:s.queue.filter(x=>!s.results[x]||(s.results[x].err&&!s.results[x].retried&&s.results[x].err!=='not found')).length};
  } finally { window.cvBusy=false; }
};
// Build the bail file for the site. date = last edition day covered, weekStart = that week's Monday (YYYY-MM-DD).
window.cvSummary=function(date,weekStart){
  const s=cvLoad(), R=Object.values(s.results), ok=R.filter(r=>!r.err);
  const p=Object.fromEntries(new Intl.DateTimeFormat('en-CA',{timeZone:'America/Anchorage',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(new Date()).map(x=>[x.type,x.value]));
  const inWeek=d=>d>=weekStart&&d<=date;
  const bonds=[], warrants=[];
  ok.forEach(r=>{ r.bail.forEach(b=>{ if(b.amount>0&&inWeek(b.date)) bonds.push({case:r.caseNo,date:b.date,amount:b.amount}); });
                 (r.warrants||[]).forEach(w=>{ if(w.amount>0&&inWeek(w.date)) warrants.push({case:r.caseNo,date:w.date,amount:w.amount,type:w.type,recalled:!!r.recalled}); }); });
  // one bucket per case, first match wins
  const bucket=r=>r.bail.some(b=>b.amount>0)?'posted':(r.warrants&&r.warrants.length&&!r.recalled)?'warrant':r.schedule?'schedule':r.conditions?'judge':r.summons?'summons':'none';
  const counts={posted:0,warrant:0,schedule:0,judge:0,summons:0,none:0}; ok.forEach(r=>counts[bucket(r)]++);
  counts.sealed=R.filter(r=>r.err==='not found').length;
  const posted=bonds.reduce((a,b)=>a+b.amount,0), onWarrants=warrants.filter(w=>!w.recalled).reduce((a,b)=>a+b.amount,0);
  return {date,week_start:weekStart,checked_at:`${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}`,
    cases_checked:ok.length,unread:R.filter(r=>r.err&&r.err!=='not found').map(r=>r.caseNo),
    counts,posted,on_warrants:onWarrants,total:posted+onWarrants,bonds,warrants};
};
'cv ready'

import {test} from 'node:test';import assert from 'node:assert/strict';
const base=process.env.QA_URL||'http://127.0.0.1:8769';
if(!/^http:\/\/127\.0\.0\.1:8769$/.test(base))throw Error('This test is restricted to the isolated QA service.');
async function post(path,body){const res=await fetch(base+path,{method:'POST',headers:{'Content-Type':'application/json',Origin:base},body:JSON.stringify(body)});return {status:res.status,body:await res.json()};}
test('Reading session saves notes, resumes pause and submits with source-backed review',async()=>{
 const list=await (await fetch(base+'/api/reading-list')).json();const content=list.items||list.published||list;assert.ok(content);
 const d=await post('/api/reading-content',{id:'reading-1'});assert.equal(d.status,200);
 const start=await post('/api/reading-start',{id:d.body.id,contentVersion:d.body.version,mode:'guided'});assert.equal(start.status,200);let e=start.body;
 if(e.paused){const r=await post('/api/reading-pause',{session:e.id,version:e.version,paused:false});assert.equal(r.status,200);e=r.body;}
 const q=d.body.questions[0],pid=d.body.passages[0].id;
 const draft={session:e.id,contentVersion:e.contentVersion,version:e.version,answers:{[q.id]:q.options[0].id},flags:[q.id],focus:q.id,highlights:[],notes:{[pid]:'QA integration evidence note'},preferences:{fontSize:18,split:60}};
 let save=await post('/api/reading-draft',draft);assert.equal(save.status,200);e=save.body;
 assert.equal((await post('/api/reading-draft',draft)).status,400);
 const bad=await post('/api/reading-draft',{...draft,version:e.version,highlights:[null]});assert.equal(bad.status,400);
 const paused=await post('/api/reading-pause',{session:e.id,version:e.version,paused:true});assert.equal(paused.status,200);e=paused.body;
 assert.equal((await post('/api/reading-draft',{...draft,version:e.version})).status,400);
 const restored=await post('/api/reading-session',{session:e.id});assert.equal(restored.body.session.notes[pid],draft.notes[pid]);assert.equal(restored.body.session.paused,true);assert.equal(restored.body.session.preferences.split,60);
 e=(await post('/api/reading-pause',{session:e.id,version:e.version,paused:false})).body;
 const submitted=await post('/api/reading-submit',{session:e.id,version:e.version});assert.equal(submitted.status,200);assert.equal(submitted.body.rows.length,40);assert.ok(submitted.body.rows.every(r=>r.type));
 const repeat=await post('/api/reading-submit',{session:e.id,version:e.version});assert.deepEqual(repeat.body,submitted.body);
});
test('Listening draft and deterministic result survive a separate state request',async()=>{
 const state=await (await fetch(base+'/api/state')).json();let version=state.listeningDraft?.version||0;
 const payload={version,reference:'The library opens at nine.',answer:'The library opens at ten.',sourceKind:'sample',sourceName:'QA original sentence',sample:0};
 const saved=await post('/api/listening-draft',payload);assert.equal(saved.status,200);assert.equal(saved.body.version,version+1);
 assert.equal((await post('/api/listening-draft',payload)).status,400);
 const attempt=await post('/api/listening-attempt',payload);assert.equal(attempt.status,200);assert.equal(attempt.body.result.accuracy,80);
 const after=await (await fetch(base+'/api/state')).json();assert.equal(after.listeningDraft.answer,payload.answer);assert.equal(after.listeningAttempts.at(-1).id,attempt.body.id);
});

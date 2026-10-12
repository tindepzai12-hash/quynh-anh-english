'use strict';
const beforeMaterialsLesson=lesson;
lesson=function(id){
 beforeMaterialsLesson(id);const l=lessonById(id);if(!l)return;
 const files=[...new Set([...l.resources,...(l.related||[])])].map(r=>catalog.resources[r]).filter(r=>r&&r.kind!=='MP4'&&r.cloudAvailable!==false);
 const pdfs=files.filter(r=>r.kind==='PDF').sort((a,b)=>(b.purpose==='exercise')-(a.purpose==='exercise')),audio=files.filter(r=>['MP3','M4A'].includes(r.kind));
 const oldCleanup=cleanup,v=$('#video');let disposed=false,timer,dirty=false,draft=state.lessonWorkbooks?.[id]?.text||'',chain=Promise.resolve();
 const syncKey='/lesson-workbook:'+id;
 function status(text){if(!disposed&&$('#workbook-save'))$('#workbook-save').textContent=text;}
 function save(){clearTimeout(timer);if(!dirty)return chain;const text=draft;dirty=false;chain=chain.catch(()=>{}).then(async()=>{try{const r=await api('/api/lesson-workbook',{id,text,_fieldVersion:state._syncVersions?.[syncKey]||0});(state._syncVersions||={})[syncKey]=r._syncVersion;(state.lessonWorkbooks||={})[id]={text:draft,updated:r.updated};status(draft===text?'Đã lưu bài làm':'Đang lưu…');}catch(e){dirty=true;status('Chưa lưu: '+e.message);}});return chain;}
 const banner=document.createElement('section');banner.className='lesson-practice-callout';banner.innerHTML=`<div><h3 id="after-video-title">${v?'Xem bài giảng, rồi thử sức.':'Đọc tài liệu, rồi thử sức.'}</h3><p>${pdfs.length} PDF · ${audio.length} audio đi kèm${catalog.quizzes[id]?' · có câu hỏi tương tác':''}</p></div><button class="button secondary" id="open-lesson-workbook">Làm bài tập →</button>`;$('.tabs').before(banner);
 function ended(){banner.classList.add('video-finished');$('#after-video-title').textContent='Video đã xong. Mình làm bài tập nhé!';}
 v?.addEventListener('ended',ended);
 function workbook(){
  const panel=$('#lesson-content');if(!panel||$('#lesson-workbook'))return;
  const area=document.createElement('section');area.id='lesson-workbook';area.className='lesson-workbook';
  area.innerHTML=`<h3>Bài tập & tài liệu gốc</h3><p>Đọc câu hỏi trong PDF, ghi số câu và câu trả lời vào ô bài làm.${l.related?.length?' Có tài liệu cùng dạng bài từ khóa tổng hợp để luyện thêm.':''}</p>${files.length?`<div class="workbook-files">${files.map(r=>`<a class="button secondary small" href="/media/${r.id}" target="_blank" rel="noopener">${r.purpose==='slide'?'Slide':r.purpose==='exercise'?'Bài tập':r.kind==='PDF'?'Tài liệu':r.kind} · ${esc(r.title)} ↗</a>`).join('')}</div>`:'<p class="small-note">Nguồn bài này không kèm PDF hoặc audio. Bạn có thể ghi bài thực hành của mình bên dưới.</p>'}${pdfs.length?`<label class="field">Chọn slide / bài tập<select id="workbook-pdf-select">${pdfs.map(r=>`<option value="${esc(r.id)}">${r.purpose==='slide'?'Slide':r.purpose==='exercise'?'Bài tập':'Tài liệu'} · ${esc(r.title)}</option>`).join('')}</select></label><iframe id="workbook-pdf" class="pdf" title="PDF bài tập gốc" src="/pdf-viewer.html?id=${pdfs[0].id}"></iframe>`:''}${audio.map(r=>`<label class="workbook-audio">${esc(r.title)}<audio controls preload="none" src="/media/${r.id}"></audio></label>`).join('')}<label class="field">Bài làm của mình<textarea id="workbook-draft" rows="7" maxlength="30000" placeholder="Ví dụ: 1. A · 2. C · 3. …">${esc(draft)}</textarea></label><div class="workbook-save-row"><span id="workbook-save" role="status">${draft?'Bài làm đã lưu':'Tự lưu bài làm theo bài học'}</span><button class="button secondary" id="workbook-save-now">Lưu bài làm</button></div><p class="small-note">Ô bài làm lưu câu trả lời để ôn lại. Chỉ câu hỏi tương tác đã đối chiếu nguồn bên dưới mới được tự chấm; hệ thống không đoán đáp án cho PDF.</p>`;
  panel.prepend(area);$('#workbook-pdf-select')?.addEventListener('change',e=>$('#workbook-pdf').src='/pdf-viewer.html?id='+e.target.value);
  $('#workbook-draft').oninput=e=>{draft=e.target.value;dirty=true;(state.lessonWorkbooks||={})[id]={text:draft};status('Đang lưu…');clearTimeout(timer);timer=setTimeout(save,600);};$('#workbook-save-now').onclick=()=>{dirty=true;save();};
 }
 document.querySelectorAll('[data-tab]').forEach(b=>{b.addEventListener('click',save,true);b.addEventListener('click',()=>{if(b.dataset.tab==='quiz')workbook();});});
 $('#open-lesson-workbook').onclick=()=>{document.querySelector('[data-tab="quiz"]').click();$('#lesson-workbook').scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});};
 cleanup=()=>{save();disposed=true;v?.removeEventListener('ended',ended);oldCleanup();};
};

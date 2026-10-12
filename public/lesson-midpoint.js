'use strict';
const beforeMidpointLesson=lesson;
lesson=function(id){
 beforeMidpointLesson(id);const l=lessonById(id),v=$('#video'),q=catalog.midpointQuestions?.[id];if(!v||!q)return;
 const oldCleanup=cleanup;let disposed=false,presented=false,busy=false,resumeTimer;
 const saved=state.midpointAnswers?.[id];presented=saved?.version===q.version;
 const strip=document.createElement('div');strip.className='midpoint-strip';strip.innerHTML=`<span>${icon('courses')}<span>Halfway check<small>1 câu hỏi tiếng Anh về ${esc(l.skill)}</small></span></span><button class="text-link" id="midpoint-review">${presented?'Xem lại câu hỏi':'Thử câu hỏi'}</button>`;$('.player-tools').after(strip);
 const dialog=document.createElement('dialog');dialog.className='midpoint-dialog';dialog.setAttribute('aria-labelledby','midpoint-title');document.body.append(dialog);
 function resume(){clearTimeout(resumeTimer);if(disposed)return;dialog.close();v.play().catch(()=>{});}
 function show(auto=false){if(disposed||dialog.open)return;presented=true;v.pause();
  dialog.innerHTML=`<div class="midpoint-title"><img src="assets/expressions/thinking.png" alt="Justin cùng bạn ôn bài"><div><small>HALFWAY CHECK · ${clock((Number.isFinite(v.duration)?v.duration:l.duration)/2)}</small><h2 id="midpoint-title">A quick check.</h2></div></div><p class="midpoint-question" lang="en">${esc(q.prompt)}</p><form id="midpoint-form"><fieldset><legend class="sr-only">Choose one answer</legend>${q.options.map((o,i)=>`<label><input type="radio" name="midpoint-choice" value="${i}" required><b class="midpoint-letter">${'ABCD'[i]}</b><span lang="en">${esc(o)}</span></label>`).join('')}</fieldset><div id="midpoint-feedback" role="status" aria-live="polite"></div><div class="dialog-actions"><button class="button" id="midpoint-submit">Kiểm tra đáp án</button></div></form><p class="small-note">Ôn khái niệm của bài học · không tính band hoặc cộng tiến độ xem.</p>`;
  dialog.showModal();
  $('#midpoint-form').onsubmit=async ev=>{ev.preventDefault();if(busy)return;busy=true;$('#midpoint-submit').disabled=true;const selected=dialog.querySelector('input:checked');
   try{const r=await api('/api/midpoint-answer',{id,version:q.version,choice:Number(selected.value)});(state.midpointAnswers||={})[id]=r;if(disposed)return;$('#midpoint-feedback').innerHTML=`<div class="midpoint-result ${r.correct?'is-correct':'is-review'}"><strong>${r.correct?'Đúng rồi! Video tiếp tục ngay.':'Cùng hiểu rõ trước khi học tiếp nhé.'}</strong>${r.correct?'':`<p lang="en">${esc(r.whyWrong||r.explanation)}</p><p><b>Đáp án đúng:</b> <span lang="en">${esc(r.key)}</span></p>`}</div>`;dialog.querySelectorAll('input').forEach(i=>i.disabled=true);$('#midpoint-submit').type='button';$('#midpoint-submit').textContent=r.correct?'Phát tiếp ngay':'Đã hiểu · học tiếp';$('#midpoint-submit').onclick=resume;$('#midpoint-review').textContent='Xem lại câu hỏi';if(r.correct)resumeTimer=setTimeout(resume,1000);}
   catch(error){if(!disposed)$('#midpoint-feedback').textContent=error.message;}finally{busy=false;if(!disposed)$('#midpoint-submit').disabled=false;}
  };
 }
 const tick=()=>{const midpoint=(Number.isFinite(v.duration)&&v.duration>0?v.duration:l.duration)/2;if(!presented&&!v.paused&&!v.seeking&&v.currentTime>=midpoint&&!document.querySelector('dialog[open]'))show(true);};
 v.addEventListener('timeupdate',tick);v.addEventListener('play',tick);$('#midpoint-review').onclick=()=>show();
 v.addEventListener('error',()=>{if(!disposed)$('#video-error').innerHTML='<div class="error"><p>Chưa tải được bài giảng. Kiểm tra kết nối và đăng nhập rồi thử lại.</p><button class="button secondary" id="retry-video">Tải lại video</button></div>';$('#retry-video')?.addEventListener('click',()=>{v.load();});});
 cleanup=()=>{disposed=true;clearTimeout(resumeTimer);v.removeEventListener('timeupdate',tick);v.removeEventListener('play',tick);dialog.remove();oldCleanup();};
};

/* Stable composer and honest, opt-in coaching. Replies arrive as whole messages. */
function tutorText(text){return esc(text).replace(/\*\*([^*\n]+)\*\*/g,'<strong>$1</strong>');}
const tutorForm=$('#global-chat-form'),tutorMessages=$('#global-chat-messages'),tutorQuery=$('#global-chat-query');
chatWindow.setAttribute('aria-label','Trò chuyện cùng gia sư Justin Mini');
tutorMessages.setAttribute('role','log');tutorMessages.setAttribute('aria-live','polite');tutorMessages.setAttribute('aria-relevant','additions');
tutorMessages.innerHTML='<div class="tutor-welcome"><img src="assets/expressions/encouraging.png" alt=""><h3>Mình học tiếp từ đâu?</h3><p>Hỏi một điều khó hiểu, sửa một câu, hoặc cùng nhìn lại tiến trình của bạn.</p></div>';
tutorForm.querySelector('label').firstChild.textContent='Nhắn cho Justin';
tutorQuery.rows=2;tutorQuery.placeholder='Mình chưa hiểu…';
const tutorTools=document.createElement('div');tutorTools.className='tutor-tools';
tutorTools.innerHTML='<div class="tutor-prompts"><button type="button" data-tutor-question="Hãy phân tích điểm mạnh, điểm cần luyện của mình dựa trên dữ liệu đã lưu và đề xuất một việc tiếp theo." data-personal="true">Nhìn lại tiến trình</button><button type="button" data-tutor-question="Giúp mình chọn một buổi học 15 phút phù hợp với tiến trình hiện tại." data-personal="true">Học gì hôm nay?</button><button type="button" data-tutor-question="Giải thích cách phát triển một ý trong Writing Task 2 bằng một ví dụ ngắn.">Gỡ một chỗ khó</button></div><label class="tutor-consent"><input type="checkbox" id="tutor-personal"> Cho AI dùng số liệu học và nhận xét AI gần đây</label><small>Không gửi tên, email hay bài viết gốc. Có thể tắt bất cứ lúc nào.</small>';
tutorForm.before(tutorTools);
tutorTools.querySelectorAll('[data-tutor-question]').forEach(b=>b.onclick=()=>{tutorQuery.value=b.dataset.tutorQuestion;if(b.dataset.personal)$('#global-ai-status').textContent='Bật tùy chọn dùng số liệu học nếu bạn muốn Justin phân tích tiến trình.';tutorQuery.focus();});
const tutorStop=document.createElement('button');tutorStop.type='button';tutorStop.className='text-link';tutorStop.textContent='Ngừng chờ';tutorStop.hidden=true;tutorForm.append(tutorStop);
let tutorGeneration=0,tutorTurns=[];
let tutorOwner;
const tutorPaintAccount=paintAccount;
paintAccount=function(){const owner=accountInfo.user?.id||'guest';if(tutorOwner!==undefined&&owner!==tutorOwner){tutorGeneration++;tutorTurns=[];tutorQuery.value='';$('#tutor-personal').checked=false;tutorMessages.innerHTML='<p>Hội thoại mới cho tài khoản hiện tại.</p>';tutorIdle();if(chatWindow.open)chatWindow.close();}tutorOwner=owner;tutorPaintAccount();};
function tutorScroll(force=false){if(force||tutorMessages.scrollHeight-tutorMessages.scrollTop-tutorMessages.clientHeight<120)tutorMessages.scrollTop=tutorMessages.scrollHeight;}
function tutorIdle(){chatBusy=false;tutorForm.querySelectorAll('[data-chat-mode]').forEach(b=>b.disabled=false);tutorStop.hidden=true;tutorMessages.removeAttribute('aria-busy');}
tutorStop.onclick=()=>{tutorGeneration++;tutorIdle();const pending=tutorMessages.querySelector('[data-pending]');if(pending){pending.textContent='Đã ngừng chờ. Yêu cầu đã gửi có thể vẫn được xử lý và lưu vào lịch sử.';delete pending.dataset.pending;}emotion('listening',2);};
tutorQuery.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();tutorForm.requestSubmit($('#global-ai-send'));}});
tutorForm.onsubmit=async e=>{
 e.preventDefault();if(chatBusy)return;const question=tutorQuery.value.trim();if(!question)return;
 const mode=e.submitter?.dataset.chatMode||'ai',personal=$('#tutor-personal').checked,lessonId=location.hash.startsWith('#lesson/')?location.hash.split('/')[1]:null,token=++tutorGeneration;
 const history=tutorTurns.slice(-6),payload=mode==='ai'?{id:lessonId,question,history,personal,consent:personal}:{query:question,lesson:lessonId};
 chatBusy=true;tutorStop.hidden=false;tutorMessages.setAttribute('aria-busy','true');tutorForm.querySelectorAll('[data-chat-mode]').forEach(b=>b.disabled=true);
 const user=document.createElement('p');user.className='chat-user';user.textContent=question;tutorMessages.append(user);
 const reply=document.createElement('div');reply.className='chat-reply';reply.dataset.pending='true';reply.innerHTML='<span class="tutor-wait">'+(mode==='search'?'Đang tìm nguồn…':personal?'Justin đang xem tiến trình của bạn…':'Justin đang suy nghĩ…')+'</span>';tutorMessages.append(reply);
 tutorQuery.value='';tutorScroll(true);emotion('thinking',3,65000);
 try{const r=await api(mode==='ai'?'/api/tutor':'/api/knowledge',payload);if(token!==tutorGeneration)return;
   const nearBottom=tutorMessages.scrollHeight-tutorMessages.scrollTop-tutorMessages.clientHeight<140;
   reply.innerHTML=mode==='ai'?'<div class="ai-answer">'+tutorText(r.text)+'</div>':'';
   if(mode==='ai'&&!r.requiresPersonal){tutorTurns.push({role:'user',content:question},{role:'assistant',content:r.text.slice(0,12000)});tutorTurns=tutorTurns.slice(-6);}
   if(r.requiresPersonal){const enable=document.createElement('button');enable.type='button';enable.className='button small';enable.textContent='Phân tích bằng số liệu của mình';enable.onclick=()=>{if(chatBusy)return;$('#tutor-personal').checked=true;tutorQuery.value=question;tutorForm.requestSubmit($('#global-ai-send'));};reply.append(enable);}
   if(mode==='search'&&!r.sources?.length)reply.textContent='Chưa tìm thấy nguồn. Thử từ khóa tiếng Anh ngắn hơn nhé.';
   if(r.sources?.length){const sources=document.createElement('details');sources.className='tutor-sources';sources.innerHTML='<summary>Nguồn tham khảo · '+r.sources.length+'</summary>'+r.sources.map(s=>s.text?sourceMarkup(s):'<a target="_blank" rel="noopener" href="'+(s.href?.startsWith('/tutor-guide.html#')?esc(s.href):'/media/'+esc(s.id)+'#page='+(s.page||1))+'">'+esc(s.title)+' · trang '+(s.page||'?')+'</a>').join('');reply.append(sources);}
   if(nearBottom)tutorScroll(true);emotion('encouraging',3);
 }catch(error){if(token!==tutorGeneration)return;reply.textContent=error.message;const retry=document.createElement('button');retry.type='button';retry.className='text-link';retry.textContent='Sửa và thử lại';retry.onclick=()=>{tutorQuery.value=question;tutorQuery.focus();};reply.append(retry);if(!tutorQuery.value)tutorQuery.value=question;emotion('encouraging',3);
 }finally{if(token===tutorGeneration){delete reply.dataset.pending;tutorIdle();}}
};
historyButton.onclick=async()=>{if(chatBusy)return;try{await refresh();const recent=(state.chatHistory||[]).slice(-5);tutorTurns=[];tutorMessages.innerHTML=recent.map(h=>'<div class="chat-history"><p class="chat-user">'+esc(h.query)+'</p><small>'+new Date(h.date*1000).toLocaleString('vi-VN')+'</small>'+(h.result?.text?'<div class="ai-answer">'+tutorText(h.result.text)+'</div>':'<p>Lượt tra cứu nguồn</p>')+'</div>').join('')||'<p>Chưa có hội thoại được lưu. Hỏi Justin một câu nhé.</p>';for(const h of recent.filter(h=>h.mode==='ai'&&h.result?.text).slice(-3))tutorTurns.push({role:'user',content:h.query},{role:'assistant',content:h.result.text.slice(0,12000)});tutorScroll(true);}catch(err){toast(err.message);}};

const speakingBeforeTutor=speakingView;
speakingView=function(){
 speakingBeforeTutor();const earlierCleanup=cleanup;let disposed=false,busy=false,recording=null,version=0;
 const disclosure=$('.studio-disclosure');if(disclosure)disclosure.textContent='Tự luyện trên thiết bị · AI nhận xét khi bạn chọn gửi · không cho band IELTS';
 const section=document.createElement('section');section.className='panel speaking-ai';
 section.innerHTML='<h2>Cùng Justin sửa bài nói</h2><p>Chọn bản chép lời để sửa ý và câu, hoặc gửi đoạn ghi âm để Gemini nghe. Nhận xét AI có thể sai; đây không phải điểm thi IELTS.</p><label class="field">Cách nhận xét<select id="speaking-ai-mode"><option value="text">Bản chép lời · nội dung và câu</option><option value="audio">Ghi âm · nghe và nhận xét</option></select></label><label class="field" id="speaking-transcript-field">Bản chép lời của bạn<textarea id="speaking-transcript" rows="5" maxlength="12000" placeholder="Nhập lại điều bạn vừa nói…"></textarea></label><label class="tutor-consent"><input type="checkbox" id="speaking-ai-consent"> Đồng ý gửi đề và bản chép lời / ghi âm đã chọn tới AI</label><p class="small-note">Audio tối đa 6 MB. Ghi âm vẫn ở thiết bị cho tới khi bạn bấm Nhận xét. Máy chủ chỉ lưu nhận xét, không lưu audio gửi lên.</p><button class="button" id="speaking-ai-send">Nhờ Justin nhận xét</button><p id="speaking-ai-status" role="status"></p><div id="speaking-ai-result" class="ai-answer"></div><details><summary>Nhận xét trước đây</summary><div>'+((state.speakingFeedback||[]).slice(-5).reverse().map(r=>'<article><small>'+new Date(r.date*1000).toLocaleString('vi-VN')+' · '+(r.inputMode==='audio'?'Ghi âm':'Bản chép lời')+'</small><div class="ai-answer">'+tutorText(r.text)+'</div></article>').join('')||'<p>Chưa có nhận xét AI.</p>')+'</div></details>';
 $('.speaking-layout').after(section);
 const mode=$('#speaking-ai-mode'),status=$('#speaking-ai-status'),button=$('#speaking-ai-send');
 mode.onchange=()=>{$('#speaking-transcript-field').hidden=mode.value==='audio';};
 function ready(e){version++;recording=e.detail;status.textContent=recording?'Đã có ghi âm để nhận xét.':'Đang ghi âm mới. Dừng ghi âm trước khi gửi.';}
 document.addEventListener('speaking-record-ready',ready);
 button.onclick=async()=>{if(busy)return;if(!$('#speaking-ai-consent').checked){status.textContent='Chọn đồng ý trước khi gửi bài nói tới AI.';return;}
   const inputMode=mode.value,token=version,body={prompt:recording?.prompt||$('#speaking-custom').value.trim()||$('#speaking-topic').value,consent:true};
   if(inputMode==='audio'&&!recording){status.textContent='Hãy ghi âm và dừng trước khi gửi.';return;}
   if(inputMode==='audio'&&recording.blob.size>6291456){status.textContent='Audio vượt 6 MB. Thử ghi một đoạn ngắn hơn hoặc nhập bản chép lời.';return;}
   if(inputMode==='text')body.transcript=$('#speaking-transcript').value.trim();
   busy=true;button.disabled=true;mode.disabled=true;$('#speaking-start').disabled=true;status.textContent=inputMode==='audio'?'Gemini đang nghe bài nói…':'Justin đang đọc bài nói…';$('#speaking-ai-result').textContent='';
   try{if(inputMode==='audio'){const data=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]);reader.onerror=()=>reject(Error('Không đọc được bản ghi.'));reader.readAsDataURL(recording.blob);});body.audio={mime:recording.blob.type.split(';')[0],data};}
     if(disposed||token!==version)return;const result=await api('/api/speaking-feedback',body);if(disposed||token!==version)return;
     $('#speaking-ai-result').innerHTML=tutorText(result.text);status.textContent=result.inputMode==='audio'?'Đã nhận xét ghi âm · không phải điểm thi.':'Đã nhận xét văn bản · không đánh giá phát âm.';
     (state.speakingFeedback||=[]).push({...result,date:Date.now()/1000});
   }catch(error){if(!disposed)status.textContent=error.message;}finally{busy=false;if(!disposed){button.disabled=false;mode.disabled=false;$('#speaking-start').disabled=false;}}
 };
 api('/api/ai-status').then(s=>{if(disposed)return;if(s.provider!=='gemini')mode.options[1].disabled=true;if(!s.configured)status.textContent='AI chưa được cấu hình; vẫn có thể tự luyện và lưu ghi âm.';}).catch(()=>{});
 cleanup=()=>{disposed=true;version++;document.removeEventListener('speaking-record-ready',ready);earlierCleanup();};
};

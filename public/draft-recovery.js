'use strict';
const recoverable=new Set(['/api/notes','/api/writing','/api/writing-exam-draft','/api/reading-draft','/api/listening-draft']);
const recoverKey=()=>`qa-unsynced-v1:${accountInfo.user?.id||'local-guest'}`;
function recoveryRead(key=recoverKey()){try{return JSON.parse(localStorage.getItem(key)||'[]')}catch{return []}}
function recoveryWrite(key,rows){try{localStorage.setItem(key,JSON.stringify(rows.slice(-10)));recoveryPaint()}catch{toast('Chưa lưu được bản nháp dự phòng trên trình duyệt. Giữ trang mở hoặc tải bản .txt.')}}
function recoveryPaint(){const rows=recoveryRead();let control=$('#recover-drafts');if(!control){control=document.createElement('button');control.id='recover-drafts';control.className='text-link';control.onclick=recoveryOpen;$('.topbar').append(control)}control.hidden=!rows.length;control.textContent=rows.length+' bản chưa đồng bộ'}
function recoveryOpen(){
 const key=recoverKey(),rows=recoveryRead(key);let dialog=$('#recovery-dialog');if(dialog)dialog.remove();dialog=document.createElement('dialog');dialog.id='recovery-dialog';dialog.className='recovery-dialog';dialog.innerHTML=`<form method="dialog"><button class="icon-button" aria-label="Đóng bản nháp">×</button></form><h2>Bản nháp chưa đồng bộ</h2><p>Những bản này ở trình duyệt hiện tại. Thử gửi lại có kiểm tra phiên bản; nếu thiết bị khác đã sửa, bạn có thể tải bản của mình để so sánh.</p><div class="recovery-list">${rows.map((r,i)=>`<section><h3>${esc(r.url==='/api/notes'?'Ghi chú bài học':r.url==='/api/listening-draft'?'Bài nghe chép':r.url==='/api/reading-draft'?'Bài Reading':'Bài Writing')}</h3><small>${new Date(r.at).toLocaleString('vi-VN')}</small><p>${esc((r.body.text||r.body.answer||r.body.texts?.task2||r.body.texts?.task1||JSON.stringify(r.body.answers||{})).slice(0,180))}</p><button class="button secondary" data-retry-draft="${i}">Thử đồng bộ</button><button class="text-link" data-download-draft="${i}">Tải bản nháp</button><p role="status" id="draft-status-${i}"></p></section>`).join('')}</div>`;document.body.append(dialog);dialog.showModal();
 dialog.querySelectorAll('[data-retry-draft]').forEach(b=>b.onclick=async()=>{const r=rows[+b.dataset.retryDraft],status=$('#draft-status-'+b.dataset.retryDraft);b.disabled=true;try{await originalRecoveryApi(r.url,r.body);recoveryWrite(key,recoveryRead(key).filter(x=>x.token!==r.token));await refresh();status.textContent='Đã đồng bộ. Bản trên máy chủ đã được tải lại.'}catch(e){status.textContent=e.message;b.disabled=false}});
 dialog.querySelectorAll('[data-download-draft]').forEach(b=>b.onclick=()=>{const r=rows[+b.dataset.downloadDraft];const url=URL.createObjectURL(new Blob([r.body.text||JSON.stringify(r.body,null,2)],{type:'text/plain;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='ban-nhap-chua-dong-bo.txt';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)});
}
const originalRecoveryApi=api;
api=async function(url,body){
 const key=recoverKey(),shouldKeep=recoverable.has(url)&&body&&!(accountInfo.mode==='cloud'&&!accountInfo.user);
 const snapshot=shouldKeep?structuredClone(body):null;
 if(snapshot&&url==='/api/notes')snapshot._fieldVersion=state?._syncVersions?.['/notes:'+body.id]||0;
 const token=shouldKeep?url+':'+(body.id||body.task||body.session):null;
 try{const r=await originalRecoveryApi(url,body);if(shouldKeep)recoveryWrite(key,recoveryRead(key).filter(x=>x.token!==token));return r}
 catch(e){if(shouldKeep)recoveryWrite(key,[...recoveryRead(key).filter(x=>x.token!==token),{token,url,body:snapshot,at:Date.now()}]);throw e}
};
document.addEventListener('DOMContentLoaded',()=>loadAccount().then(recoveryPaint));
window.addEventListener('online',()=>{if(recoveryRead().length)toast('Có bản nháp chưa đồng bộ. Mở nút bản nháp để gửi lại an toàn.')});

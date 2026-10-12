import {getDocument,GlobalWorkerOptions} from './vendor/pdfjs/pdf.mjs';
GlobalWorkerOptions.workerSrc='/vendor/pdfjs/pdf.worker.mjs';
const id=new URLSearchParams(location.search).get('id'),message=document.querySelector('#message'),label=document.querySelector('#page'),canvas=document.querySelector('canvas'),prev=document.querySelector('#prev'),next=document.querySelector('#next'),jump=document.querySelector('#jump'),zoom=document.querySelector('#zoom');
let pdf,page=1,rendering=false,queued=false;
try{page=Math.max(1,Number(sessionStorage.getItem('pdf-page:'+id))||1);}catch{}
async function render(){
 if(!pdf)return;if(rendering){queued=true;return;}rendering=true;prev.disabled=next.disabled=jump.disabled=zoom.disabled=true;canvas.setAttribute('aria-busy','true');
 try{const p=await pdf.getPage(page),raw=p.getViewport({scale:1}),scale=Math.max(.2,(document.documentElement.clientWidth-16)/raw.width)*Number(zoom.value),viewport=p.getViewport({scale}),dpr=Math.min(devicePixelRatio||1,2);canvas.width=Math.floor(viewport.width*dpr);canvas.height=Math.floor(viewport.height*dpr);canvas.style.width=viewport.width+'px';await p.render({canvasContext:canvas.getContext('2d'),viewport,transform:dpr===1?null:[dpr,0,0,dpr,0,0]}).promise;message.hidden=true;label.textContent=`/ ${pdf.numPages}`;jump.max=pdf.numPages;jump.value=page;try{sessionStorage.setItem('pdf-page:'+id,page);}catch{}}
 catch{message.hidden=false;message.textContent='Chưa hiển thị được trang. Thử Bản gốc ở phía trên.';}
 finally{rendering=false;canvas.setAttribute('aria-busy','false');prev.disabled=page<=1;next.disabled=page>=pdf.numPages;jump.disabled=zoom.disabled=false;if(queued){queued=false;render();}}
}
jump.onchange=()=>{if(!pdf||rendering)return;page=Math.max(1,Math.min(pdf.numPages,Math.floor(Number(jump.value)||1)));render();};prev.onclick=()=>{if(page>1&&!rendering){page--;render();}};next.onclick=()=>{if(pdf&&page<pdf.numPages&&!rendering){page++;render();}};zoom.onchange=render;
let resize;addEventListener('resize',()=>{clearTimeout(resize);resize=setTimeout(render,180);});
if(!/^r\d+$/.test(id||'')){message.textContent='Tài liệu không hợp lệ.';}else{document.querySelector('#download').href='/media/'+id;try{pdf=await getDocument({url:'/media/'+id,isEvalSupported:false}).promise;page=Math.min(page,pdf.numPages);await render();}catch{label.textContent='Lỗi tải';message.textContent='Chưa mở được PDF. Kiểm tra đăng nhập và thử Bản gốc.';}}

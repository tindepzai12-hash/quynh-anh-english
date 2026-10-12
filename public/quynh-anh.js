/* A quiet, dedicated viewing space beside Account. */
icons.quynhanh='<path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z"/>';
worldNav.quynhanh='Quỳnh Anh';
document.addEventListener('DOMContentLoaded',()=>{
 const account=$('#account-nav');if(!account||$('#quynh-anh-nav'))return;
 const a=document.createElement('a');a.id='quynh-anh-nav';a.href='#quynhanh';a.dataset.nav='quynhanh';a.setAttribute('aria-label','Quỳnh Anh');a.innerHTML=icon('quynhanh')+'<span>Quỳnh Anh</span>';account.after(a);
 document.querySelector('.rail-bottom a[href="#profile"]')?.remove();
});
function quynhAnhView(){
 $('#app').innerHTML='<section class="qa-cinema"><header class="qa-cinema-heading"><div><h1>anh yêu em</h1><p>Dành riêng cho Quỳnh Anh.</p></div><button class="button secondary" id="qa-fullscreen">'+icon('quynhanh')+' Xem toàn màn hình</button></header><div class="qa-cinema-stage" id="qa-cinema-stage"><video id="qa-love-video" controls playsinline preload="metadata" poster="/quynh-anh-media/poster.jpg" aria-label="anh yêu em — video dành cho Quỳnh Anh"><source src="/quynh-anh-media/anh-yeu-em-2k.mp4?v=65s" type="video/mp4">Trình duyệt chưa hỗ trợ video. Hãy dùng Chrome, Edge hoặc Safari.</video></div><div class="qa-cinema-footer"><span>Quỳnh Anh</span><button class="text-link" id="qa-replay">Xem lại từ đầu</button></div><p class="qa-video-status" id="qa-video-status" role="status"></p></section>';
 const video=$('#qa-love-video'),stage=$('#qa-cinema-stage'),status=$('#qa-video-status');
 $('#qa-fullscreen').onclick=async()=>{try{if(stage.requestFullscreen)await stage.requestFullscreen();else if(video.webkitEnterFullscreen)video.webkitEnterFullscreen();else status.textContent='Dùng nút toàn màn hình trên thanh điều khiển video.';}catch{status.textContent='Dùng nút toàn màn hình trên thanh điều khiển video.';}};
 $('#qa-replay').onclick=()=>{video.currentTime=0;video.play().catch(()=>status.textContent='Bấm nút Phát trên video để xem.');};
 video.addEventListener('error',()=>{status.innerHTML='Chưa tải được video. <a href="#account">Kiểm tra đăng nhập</a> rồi mở lại Quỳnh Anh.';});
 cleanup=()=>{video.pause();video.removeAttribute('src');video.querySelector('source')?.remove();video.load();if(document.fullscreenElement===stage)document.exitFullscreen().catch(()=>{});};
}
const beforeQuynhAnhRoute=route;
route=function(){if(location.hash==='#quynhanh'){
 cleanup();cleanup=()=>{};if(chatWindow.open)chatWindow.close();document.body.dataset.screen='quynhanh';document.body.classList.remove('exam-mode');$('.rail').classList.remove('open');document.querySelectorAll('[data-nav]').forEach(a=>a.classList.toggle('active',a.dataset.nav==='quynhanh'));$('#page-label').textContent='Quỳnh Anh';quynhAnhView();window.scrollTo(0,0);
 }else if(location.hash==='#profile'){location.hash='#settings';}else beforeQuynhAnhRoute();};

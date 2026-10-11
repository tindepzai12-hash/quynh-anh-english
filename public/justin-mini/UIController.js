export function bindJustinUI(controller,root,settings,onSave){
 const status=root.querySelector('#justin-status'),start=root.querySelector('#justin-record'),stop=root.querySelector('#justin-stop'),replay=root.querySelector('#justin-replay'),speak=root.querySelector('#justin-speak'),recognize=root.querySelector('#justin-recognize');
 let catches=0;
 const ball=root.querySelector('#justin-ball'),score=root.querySelector('#justin-game-score');
 function placeBall(){ball.style.left=(18+Math.random()*60)+'%';ball.style.top=(30+Math.random()*28)+'%';}
 controller.options.onStatus=(text,state)=>{root.querySelector('.justin-corner').dataset.state=state;
 root.querySelector('#justin-wake').hidden=state!=='Sleeping';root.querySelector('#justin-sleep').hidden=state==='Sleeping';
 root.querySelector('#justin-end-play').hidden=state!=='Playing';root.querySelector('#justin-play').hidden=state==='Playing';
 ball.hidden=state!=='Playing';score.hidden=state!=='Playing';
 root.querySelectorAll('[data-react]').forEach(b=>b.disabled=['Sleeping','Playing','Listening','Processing','Talking'].includes(state));
status.textContent=text;root.dataset.voiceState=state;start.disabled=!['Idle','Interacting'].includes(state);stop.disabled=!['Listening','Processing','Talking'].includes(state);replay.disabled=!controller.voice.lastBuffer||['Listening','Sleeping','Playing'].includes(state);speak.disabled=['Listening','Processing','Sleeping','Playing'].includes(state);recognize.disabled=!(window.SpeechRecognition||window.webkitSpeechRecognition)||['Listening','Processing','Talking','Sleeping','Playing'].includes(state);root.querySelector('#justin-demo').disabled=['Sleeping','Playing'].includes(state);root.querySelector('#justin-status-dot').classList.toggle('active',state==='Listening'||state==='Talking');};
 start.onclick=()=>controller.voice.startRaw(settings);stop.onclick=()=>{if(controller.state.current==='Listening'&&controller.voice.recorder?.state==='recording')controller.voice.stopRecording();else controller.voice.cancel();};replay.onclick=()=>controller.voice.replay(settings);
 root.querySelector('#justin-demo').onclick=()=>controller.voice.synthetic(settings).catch(e=>{controller.state.reset();status.textContent=e.message;});
 speak.onclick=()=>controller.voice.speak(root.querySelector('#justin-text').value,settings);
 const Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;
 recognize.disabled=!Recognition;recognize.onclick=()=>{if(!root.querySelector('#justin-stt-consent').checked){status.textContent='Tích chọn đồng ý dùng dịch vụ nhận dạng của trình duyệt trước.';return;}controller.voice.recognize(text=>{root.querySelector('#justin-text').value=text;controller.voice.speak(text,settings);});};
 for(let id of ['speed','volume'])root.querySelector('#justin-'+id).oninput=e=>{settings[id]=Number(e.target.value);root.querySelector('#justin-'+id+'-value').textContent=id==='speed'?settings[id].toFixed(2)+'×':Math.round(settings[id]*100)+'%';};
 root.querySelector('#justin-mode').onchange=e=>{settings.mode=e.target.value;controller.voice.cancel();updateMode();};
 function updateMode(){root.querySelector('#justin-raw-panel').hidden=settings.mode!=='raw';root.querySelector('#justin-text-panel').hidden=settings.mode!=='text';}
 updateMode();root.querySelector('#justin-settings-save').onclick=async()=>{try{await onSave(settings);status.textContent='Đã lưu chế độ và thiết lập giọng nói.';}catch(e){status.textContent=e.message;}};
 controller.options.onLevel=level=>root.querySelector('#justin-level').style.setProperty('--voice-level',Math.min(1,level*5));
 root.querySelectorAll('[data-react]').forEach(b=>b.onclick=()=>controller.react(b.dataset.react,b.dataset.clip));root.querySelector('#justin-sleep').onclick=()=>controller.sleep();
 root.querySelector('#justin-wake').onclick=()=>controller.wake();
 root.querySelector('#justin-play').onclick=()=>{catches=0;score.textContent='Bắt bóng · 0/5';controller.play();placeBall();};
 root.querySelector('#justin-end-play').onclick=()=>controller.wake();
 ball.onclick=()=>{if(controller.state.current!=='Playing')return;catches++;score.textContent='Bắt bóng · '+catches+'/5';
 if(catches>=5){controller.wake();controller.react('head','Celebrate');status.textContent='Bắt đủ 5 quả rồi! Giỏi quá, mình chơi lại nhé.';}else {controller.animation?.play('Play');placeBall();}};

}

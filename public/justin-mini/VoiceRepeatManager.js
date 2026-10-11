import {MAX_RECORD_SECONDS} from './DataDefinitions.js';
export class JustinMiniVoiceRepeatManager {
 constructor(state,audio,notify){this.state=state;this.audio=audio;this.notify=notify;this.generation=0;this.disposed=false;this.stream=null;this.recorder=null;this.recognition=null;this.timeout=null;this.started=0;this.synthLevel=0;this.lastBuffer=null;this.pending=false;}
 async startRaw(settings){
  if(this.pending||this.disposed||!['Idle','Sleeping','Interacting'].includes(this.state.current))return;
  if(!navigator.mediaDevices?.getUserMedia||!window.MediaRecorder){this.notify('Ghi âm cần Chrome hoặc Edge và địa chỉ localhost/HTTPS.');return;}
  this.cancel();const token=this.generation;this.pending=true;this.notify('Đang mở micro…');
  try{await this.audio.ready();const stream=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true}});if(token!==this.generation||this.disposed){stream.getTracks().forEach(t=>t.stop());return;}
   this.stream=stream;this.audio.listen(stream);let parts=[];const recorder=new MediaRecorder(stream);this.recorder=recorder;this.pending=false;recorder.ondataavailable=e=>{if(e.data.size)parts.push(e.data);};
   recorder.onstop=async()=>{stream.getTracks().forEach(t=>t.stop());this.stream=null;this.audio.stop();if(token!==this.generation||this.disposed)return;this.state.transition('Processing');try{let buffer=await this.audio.decode(new Blob(parts,{type:recorder.mimeType}));if(token!==this.generation||this.disposed)return;this.lastBuffer=buffer;this.state.transition('Talking');await this.audio.play(buffer,settings,()=>{if(token===this.generation)this.state.reset();});}catch(e){if(token===this.generation){this.state.reset();this.notify(e.message);}}};
   recorder.start();this.started=performance.now();this.state.transition('Listening');this.timeout=setTimeout(()=>this.stopRecording(),MAX_RECORD_SECONDS*1000);
  }catch(e){if(token===this.generation){this.state.reset();this.notify(e.name==='NotAllowedError'?'Micro chưa được cấp quyền. Bạn có thể dùng mục Đọc câu nhập.':'Không mở được micro: '+e.message);}}finally{if(token===this.generation)this.pending=false;}
 }
 stopRecording(){clearTimeout(this.timeout);if(this.recorder?.state==='recording')this.recorder.stop();}
 speak(text,settings){
  if(this.disposed)return;this.cancel();if(!text.trim())return this.notify('Nhập một câu để Justin đọc lại.');if(!window.speechSynthesis)return this.notify('Trình duyệt chưa hỗ trợ đọc văn bản.');
  const token=this.generation;this.state.transition('Talking');let u=new SpeechSynthesisUtterance(text.slice(0,1000));u.lang='en-US';u.rate=settings.speed;u.pitch=1.35;u.volume=settings.volume;let voices=speechSynthesis.getVoices();u.voice=voices.find(v=>v.lang.startsWith('en')&&v.localService)||voices.find(v=>v.lang.startsWith('en'))||null;
  u.onboundary=()=>{this.synthLevel=.2;};u.onstart=()=>{this.synthLevel=.12;};u.onend=u.onerror=()=>{if(token!==this.generation)return;this.synthLevel=0;this.state.reset();};speechSynthesis.speak(u);
 }
 recognize(onText){
  const Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;if(!Recognition)return this.notify('Trình duyệt chưa hỗ trợ nhận dạng. Nhập câu rồi bấm Đọc câu.');
  this.cancel();const token=this.generation;let rec=new Recognition();this.recognition=rec;rec.lang='en-US';rec.interimResults=false;rec.continuous=false;this.state.transition('Listening');this.notify('Đang nhận dạng tiếng Anh qua dịch vụ của trình duyệt…');
  rec.onresult=e=>{if(token!==this.generation||this.disposed)return;onText(e.results[0][0].transcript);};rec.onerror=e=>{if(token===this.generation){this.state.reset();this.notify('Nhận dạng chưa thành công: '+e.error+'. Bạn có thể nhập câu.');}};rec.onend=()=>{if(token===this.generation&&this.state.current==='Listening')this.state.reset();};rec.start();this.timeout=setTimeout(()=>rec.stop(),MAX_RECORD_SECONDS*1000);
 }
 async replay(settings){if(!this.lastBuffer)return this.notify('Hãy ghi một câu trước.');this.cancel();const token=this.generation;this.state.transition('Talking');try{await this.audio.play(this.lastBuffer,settings,()=>{if(token===this.generation)this.state.reset();});}catch(e){this.state.reset();this.notify(e.message);}}
 async synthetic(settings){this.cancel();const token=this.generation;let context=await this.audio.ready();if(token!==this.generation||this.disposed)return;let b=context.createBuffer(1,context.sampleRate*.9,context.sampleRate),d=b.getChannelData(0);for(let i=0;i<d.length;i++){let t=i/context.sampleRate;d[i]=Math.sin(2*Math.PI*280*t)*Math.sin(Math.PI*t/.9)**2*.24;}this.lastBuffer=b;this.state.transition('Talking');await this.audio.play(b,settings,()=>{if(token===this.generation)this.state.reset();});}
 level(){this.synthLevel*=.96;return Math.max(this.audio.level(),this.synthLevel);}
 cancel(){this.generation++;this.pending=false;clearTimeout(this.timeout);if(this.recorder){this.recorder.onstop=null;if(this.recorder.state==='recording')this.recorder.stop();}this.stream?.getTracks().forEach(t=>t.stop());this.stream=null;this.recognition?.abort();this.recognition=null;this.audio.stop();if(window.speechSynthesis)speechSynthesis.cancel();this.synthLevel=0;this.state.reset();}
 dispose(){this.cancel();this.disposed=true;this.audio.dispose();}
}

export function trimSilence(buffer,context){
 let first=0,last=buffer.length-1;const data=buffer.getChannelData(0),threshold=.008;
 while(first<last&&Math.abs(data[first])<threshold)first++;while(last>first&&Math.abs(data[last])<threshold)last--;
 if(last-first<buffer.sampleRate*.12)throw new Error('Chưa nghe thấy âm thanh. Thử nói gần micro hơn.');
 first=Math.max(0,first-Math.round(buffer.sampleRate*.08));last=Math.min(buffer.length-1,last+Math.round(buffer.sampleRate*.12));
 const out=context.createBuffer(buffer.numberOfChannels,last-first+1,buffer.sampleRate);for(let c=0;c<buffer.numberOfChannels;c++)out.copyToChannel(buffer.getChannelData(c).subarray(first,last+1),c);return out;
}
export class JustinMiniAudioController {
 constructor(){this.context=null;this.source=null;this.monitor=null;this.analyser=null;this.data=null;this.disposed=false;this.generation=0;}
 listen(stream){this.stop();this.monitor=this.context.createMediaStreamSource(stream);this.analyser=this.context.createAnalyser();this.analyser.fftSize=256;this.data=new Uint8Array(256);this.monitor.connect(this.analyser);}
 async ready(){if(this.disposed)throw new Error('Phiên âm thanh đã đóng.');const Audio=window.AudioContext||window.webkitAudioContext;if(!Audio)throw new Error('Trình duyệt chưa hỗ trợ Web Audio.');this.context ||= new Audio();await this.context.resume();return this.context;}
 async decode(blob){const context=await this.ready();return context.decodeAudioData(await blob.arrayBuffer());}
 async play(buffer,{speed=1.22,volume=.8}={},onEnd=()=>{}){
  this.stop();const generation=this.generation,context=await this.ready();if(this.disposed||generation!==this.generation)return;
  const source=context.createBufferSource();source.buffer=trimSilence(buffer,context);source.playbackRate.value=speed;
  const gain=context.createGain();gain.gain.value=volume;const analyser=context.createAnalyser();analyser.fftSize=256;
  source.connect(gain);gain.connect(analyser);analyser.connect(context.destination);this.source=source;this.analyser=analyser;this.data=new Uint8Array(256);
  source.onended=()=>{source.disconnect();gain.disconnect();analyser.disconnect();if(generation===this.generation){this.source=null;this.analyser=null;onEnd();}};source.start();
 }
 level(){if(!this.analyser)return 0;this.analyser.getByteTimeDomainData(this.data);let energy=0;for(let n of this.data)energy+=((n-128)/128)**2;return Math.sqrt(energy/this.data.length);}
 stop(){this.generation++;if(this.source){this.source.onended=null;try{this.source.stop();}catch{}this.source.disconnect();this.source=null;}this.monitor?.disconnect();this.monitor=null;this.analyser?.disconnect();this.analyser=null;}
 dispose(){this.disposed=true;this.stop();this.context?.close().catch(()=>{});}
}

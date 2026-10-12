export class ReactionSound {
 constructor(){this.muted=true;this.context=null;this.last=0;}
 async play(kind){if(this.muted||Date.now()-this.last<220)return;this.last=Date.now();try{this.context||=new (window.AudioContext||window.webkitAudioContext)();await this.context.resume();if(this.muted)return;const now=this.context.currentTime,o=this.context.createOscillator(),g=this.context.createGain();o.type='sine';o.frequency.setValueAtTime(kind==='pet'?660:kind==='feed'?380:180,now);o.frequency.exponentialRampToValueAtTime(kind==='pet'?880:100,now+.14);g.gain.setValueAtTime(.035,now);g.gain.exponentialRampToValueAtTime(.001,now+.18);o.connect(g).connect(this.context.destination);o.start(now);o.stop(now+.19);o.onended=()=>{o.disconnect();g.disconnect();};}catch{}}
 dispose(){this.muted=true;this.context?.close().catch(()=>{});}
}

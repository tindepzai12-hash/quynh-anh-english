export const MOODS={Neutral:'Thư giãn',Happy:'Vui vẻ',Loved:'Được yêu thương',Surprised:'Bất ngờ',Hurt:'Ối, nhẹ tay thôi',Annoyed:'Hơi phụng phịu',Hungry:'Hơi đói',Full:'No bụng',Dizzy:'Hơi choáng',Recovering:'Đang nghỉ một chút'};
export class EmotionEngine {
 constructor(onChange=()=>{}){this.onChange=onChange;this.time=0;this.until=0;this.current='Neutral';this.memory=[];this.meals=[];this.priority=0;this.cooldown=0;}
 set(mood,seconds=2,priority=1){if(!MOODS[mood]||priority<this.priority&&this.time<this.until)return false;this.current=mood;this.until=this.time+seconds;this.priority=priority;this.onChange(mood,MOODS[mood]);return true;}
 remember(type,region){this.memory.push({type,region,at:this.time});this.memory=this.memory.filter(e=>this.time-e.at<18).slice(-12);}
 canAct(){return this.time>=this.cooldown;}
 contact(type,region){this.remember(type,region);this.cooldown=this.time+(type==='pet'?.15:1.1);if(type==='feed'){this.meals.push(this.time);this.meals=this.meals.filter(t=>this.time-t<90);this.set(this.meals.length>=3?'Full':'Happy',4,2);}else this.set(type==='pet'?'Loved':this.memory.filter(e=>e.type==='ball').length>=3?'Annoyed':'Hurt',2.4,2);}
 update(dt){this.time+=dt;if(this.time>=this.until&&this.current!=='Neutral'){if(['Hurt','Annoyed','Dizzy'].includes(this.current))this.set('Recovering',1,0);else this.set('Neutral',Infinity,0);}this.memory=this.memory.filter(e=>this.time-e.at<18);}
}

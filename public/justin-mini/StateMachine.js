export const STATES=['Idle','Interacting','Listening','Processing','Talking','SwitchingSkin','Sleeping'];
const graph={Idle:STATES,Interacting:['Idle','Interacting','Sleeping','Listening','Talking','SwitchingSkin'],Listening:['Processing','Idle'],Processing:['Talking','Idle'],Talking:['Idle','Talking'],SwitchingSkin:['Idle','SwitchingSkin'],Sleeping:['Idle','Interacting','Listening','SwitchingSkin','Talking']};
export class JustinMiniStateMachine extends EventTarget {
 constructor(){super();this.current='Idle';this.version=0;}
 transition(next){if(!graph[this.current]?.includes(next))return false;this.current=next;this.version++;this.dispatchEvent(new CustomEvent('change',{detail:next}));return true;}
 reset(){this.current='Idle';this.version++;this.dispatchEvent(new CustomEvent('change',{detail:'Idle'}));}
}

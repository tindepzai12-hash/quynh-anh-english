import {timingSafeEqual} from 'node:crypto';
// Email confirmation/recovery has no OAuth state. A started social flow must have one.
export function validOAuthCallback(session,state,now=Date.now()){
 if(!session.oauthState && state===undefined)return true;
 if(typeof state!=='string'||typeof session.oauthState!=='string'||!state||!Number.isFinite(session.oauthAt))return false;
 const age=now-session.oauthAt;if(age<0||age>600000)return false;
 const a=Buffer.from(state),b=Buffer.from(session.oauthState);
 return a.length===b.length&&timingSafeEqual(a,b);
}

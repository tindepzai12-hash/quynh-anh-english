import {DatabaseSync} from 'node:sqlite';
import {createHash} from 'node:crypto';
export const freshState=()=>({progress:{},notes:{},attempts:[],plan:null,testDrafts:{},known:[]});
export class LocalState {
  constructor(path){this.db=new DatabaseSync(path);this.db.exec('CREATE TABLE IF NOT EXISTS state(id INTEGER PRIMARY KEY CHECK(id=1),body TEXT NOT NULL)');this.db.prepare('INSERT OR IGNORE INTO state VALUES(1,?)').run(JSON.stringify(freshState()))}
  async read(){return {body:JSON.parse(this.db.prepare('SELECT body FROM state WHERE id=1').get().body)}}
  async write(body){this.db.prepare('UPDATE state SET body=? WHERE id=1').run(JSON.stringify(body))}
  close(){this.db.close()}
}
export class CloudState {
  constructor(client){this.client=client}
  async read(id){
    let {data,error}=await this.client.from('learning_states').select('body,version').eq('user_id',id).maybeSingle();if(error)throw Error('Chưa kết nối được kho tiến trình.');
    if(!data){const inserted=await this.client.from('learning_states').insert({user_id:id,body:freshState()}).select('body,version').single();if(inserted.error){({data,error}=await this.client.from('learning_states').select('body,version').eq('user_id',id).single());if(error)throw Error('Chưa tạo được kho tiến trình.')}else data=inserted.data}
    return data;
  }
  async write(id,body,version){const {data,error}=await this.client.from('learning_states').update({body,version:version+1,updated_at:new Date().toISOString()}).eq('user_id',id).eq('version',version).select('version').maybeSingle();if(error)throw Error('Chưa lưu được tiến trình.');if(!data){const e=Error('Tiến trình vừa đổi ở thiết bị khác. Tải lại trước khi tiếp tục.');e.status=409;throw e}}
}
const digest=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
export function mergeGuest(target,guest){
  const token=digest(guest);if(target.guestImports?.includes(token))return target;
  const occupied=['progress','notes','readingSessions','writingDrafts','vocabReviews','exams','writingExams','timestampNotes','listeningDraft'].some(k=>Object.keys(target[k]||{}).length)||['attempts','known','vocabFavorites','writingSubmissions','speakingSessions','listeningAttempts'].some(k=>target[k]?.length)||target.plan||target.ecosystem?.ledger?.length;
  if(!occupied)return {...structuredClone(guest),guestImports:[...(target.guestImports||[]),token]};
  const out=structuredClone(target);
  out.guestBackups=[...(out.guestBackups||[]),{token,body:guest}].slice(-3);
  out.progress||={};for(const [id,p] of Object.entries(guest.progress||{})){const old=out.progress[id];out.progress[id]=old?{...old,complete:!!(old.complete||p.complete),watched:Math.max(old.watched||0,p.watched||0)}:p}
  out.notes||={};for(const [id,n]of Object.entries(guest.notes||{}))if(!out.notes[id])out.notes[id]=n;
  out.known=[...new Set([...(out.known||[]),...(guest.known||[])])];out.vocabFavorites=[...new Set([...(out.vocabFavorites||[]),...(guest.vocabFavorites||[])])];
  out.vocabReviews||={};for(const [id,r]of Object.entries(guest.vocabReviews||{}))if(!out.vocabReviews[id])out.vocabReviews[id]=r;
  out.attempts||=[];const seen=new Set(out.attempts.map(digest));for(const a of guest.attempts||[])if(!seen.has(digest(a))){out.attempts.push(a);seen.add(digest(a))}
  // Preserve both reward ledgers in backup; never add two balances or duplicate exam credits.
  out.guestImports=[...(out.guestImports||[]),token];return out;
}

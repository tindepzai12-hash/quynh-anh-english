import {spawn} from 'node:child_process';
import {createInterface} from 'node:readline';
import {randomUUID} from 'node:crypto';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));
export class Engine {
  constructor(python=process.env.PYTHON_BIN||'python3') {
    this.child=spawn(python,['-X','utf8',root+'node/bridge.py'],{cwd:root,stdio:['pipe','pipe','pipe']});
    this.pending=new Map(); this.queue=Promise.resolve();
    this.ready=new Promise((resolve,reject)=>{this.resolveReady=resolve;this.rejectReady=reject});
    createInterface({input:this.child.stdout}).on('line',line=>{
      try {const r=JSON.parse(line);if(r.ready)return this.resolveReady();const p=this.pending.get(r.id);if(p){clearTimeout(p.timer);this.pending.delete(r.id);p.resolve(r)}}catch{this.fail()}
    });
    this.child.stderr.on('data',()=>{});
    this.child.on('error',()=>this.fail());this.child.on('exit',()=>this.fail());
  }
  fail(){const error=Error('Máy xử lý bài học chưa sẵn sàng.');this.rejectReady(error);for(const p of this.pending.values()){clearTimeout(p.timer);p.reject(error)}this.pending.clear()}
  async call(path,method,state,body){
    const execute=async()=>{await this.ready;const id=randomUUID();return new Promise((resolve,reject)=>{
      const timer=setTimeout(()=>{this.pending.delete(id);reject(Error('Yêu cầu chưa hoàn tất; tiến trình cũ vẫn được giữ.'));this.child.kill()},90000);
      this.pending.set(id,{resolve,reject,timer});this.child.stdin.write(JSON.stringify({id,path,method,state,body})+'\n');
    })};
    const result=this.queue.then(execute);this.queue=result.catch(()=>{});return result;
  }
  close(){this.child.kill()}
}

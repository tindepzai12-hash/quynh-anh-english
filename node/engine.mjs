import {spawn} from 'node:child_process';
import {createInterface} from 'node:readline';
import {randomUUID} from 'node:crypto';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));
export class Engine {
  constructor(python=process.env.PYTHON_BIN||'python3',options={}) {
    this.python=python;this.bridge=options.bridge||root+'node/bridge.py';this.timeout=options.timeout||90000;
    this.pending=new Map(); this.queue=Promise.resolve();this.closing=false;
    this.launch();
  }
  launch(){
    const child=this.child=spawn(this.python,['-X','utf8',this.bridge],{cwd:root,stdio:['pipe','pipe','pipe']});this.dead=false;
    this.ready=new Promise((resolve,reject)=>{this.resolveReady=resolve;this.rejectReady=reject});
    // A worker may fail before the first request starts awaiting readiness.
    this.ready.catch(()=>{});
    this.startup=setTimeout(()=>this.fail(Error('Máy xử lý khởi động quá lâu.'),child),this.timeout);
    createInterface({input:child.stdout}).on('line',line=>{
      if(child!==this.child||this.dead)return;
      try {const r=JSON.parse(line);if(r.ready){clearTimeout(this.startup);return this.resolveReady()}const p=this.pending.get(r.id);if(p){clearTimeout(p.timer);this.pending.delete(r.id);p.resolve(r)}}catch{this.fail()}
    });
    child.stderr.on('data',()=>{});
    child.stdin.on('error',()=>this.fail(undefined,child));
    child.on('error',()=>this.fail(undefined,child));child.on('exit',()=>this.fail(undefined,child));
  }
  fail(error=Error('Máy xử lý bài học chưa sẵn sàng. Hãy thử lưu lại.'),child=this.child){if(child!==this.child)return;clearTimeout(this.startup);this.dead=true;this.rejectReady(error);for(const p of this.pending.values()){clearTimeout(p.timer);p.reject(error)}this.pending.clear();child.kill()}
  async call(path,method,state,body,authorization){
    const execute=async()=>{if(this.closing)throw Error('Máy xử lý đã đóng.');if(this.dead)this.launch();await this.ready;const child=this.child,id=randomUUID();return new Promise((resolve,reject)=>{
      const timer=setTimeout(()=>{this.fail(Error('Yêu cầu chưa được xác nhận; hãy kiểm tra bản đã lưu trước khi thử lại.'),child);child.kill()},this.timeout);
      this.pending.set(id,{resolve,reject,timer});this.child.stdin.write(JSON.stringify({id,path,method,state,body,authorization})+'\n');
    })};
    const result=this.queue.then(execute);this.queue=result.catch(()=>{});return result;
  }
  close(){this.closing=true;this.fail(Error('Máy xử lý đã đóng.'));this.child.kill()}
}

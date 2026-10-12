import {test} from 'node:test';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {Engine} from '../node/engine.mjs';
const bridge=fileURLToPath(new URL('./engine-fixture.py',import.meta.url));
test('worker failure rejects uncertain request; next request recovers without replay',async()=>{
 const e=new Engine(process.env.PYTHON_BIN,{bridge,timeout:3000});
 try{const first=await e.call('/ok','GET',{},{});const crashed=e.call('/crash','POST',{},{});const next=e.call('/next','GET',{},{});await assert.rejects(crashed);const recovered=await next;assert.equal(recovered.data.path,'/next');assert.notEqual(first.data.pid,recovered.data.pid);}finally{e.close();}
 await assert.rejects(e.call('/after-close','GET',{},{}),/đã đóng/);
});
test('timeout frees queue and restarts worker on the next request',async()=>{
 const e=new Engine(process.env.PYTHON_BIN,{bridge,timeout:500});
 try{await e.call('/ok','GET',{},{});await assert.rejects(e.call('/timeout','POST',{},{}),/chưa được xác nhận/);assert.equal((await e.call('/next','GET',{},{})).status,200);}finally{e.close();}
});

import express from 'express';
import helmet from 'helmet';
import {rateLimit} from 'express-rate-limit';
import {getIronSession} from 'iron-session';
import {createClient} from '@supabase/supabase-js';
import {randomBytes,timingSafeEqual} from 'node:crypto';
import {mkdirSync,existsSync,readFileSync,writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {Engine} from './engine.mjs';
import {LocalState,CloudState,freshState,mergeGuest} from './state.mjs';

const root=fileURLToPath(new URL('../',import.meta.url));
const cloud=!!process.env.RENDER||process.env.APP_MODE==='cloud';
const port=Number(process.env.PORT||8765);
const origin=process.env.APP_ORIGIN||process.env.RENDER_EXTERNAL_URL||`http://127.0.0.1:${port}`;
const configured=!!(process.env.SUPABASE_URL&&process.env.SUPABASE_ANON_KEY&&process.env.SUPABASE_SERVICE_ROLE_KEY);
mkdirSync(root+'state',{recursive:true});
let secret=process.env.SESSION_SECRET;
if(!secret&&!cloud){const path=root+'state/node-session.private.txt';if(!existsSync(path))writeFileSync(path,randomBytes(48).toString('base64'),{mode:0o600});secret=readFileSync(path,'utf8').trim()}
if(!secret||secret.length<32)throw Error('SESSION_SECRET needs at least 32 characters.');
const admin=configured?createClient(process.env.SUPABASE_URL,process.env.SUPABASE_SERVICE_ROLE_KEY,{auth:{persistSession:false,autoRefreshToken:false}}):null;
const local=cloud?null:new LocalState(process.env.OCEAN_LOCAL_DB||root+'state/learning.sqlite3');
const persistent=admin?new CloudState(admin):null;
if(!cloud&&!process.env.OCEAN_READING_DB)process.env.OCEAN_READING_DB=root+'state/learning-reading-content.sqlite3';
if(cloud&&!process.env.OCEAN_CATALOG)process.env.OCEAN_CATALOG=root+'deploy/catalog.json';
const engine=new Engine();await engine.ready;
const app=express();if(cloud)app.set('trust proxy',1);
app.disable('x-powered-by');
app.use(helmet({contentSecurityPolicy:false,crossOriginEmbedderPolicy:false}));
app.use(express.json({limit:'1mb',type:['application/json','text/plain']}));
app.use((req,res,next)=>{if(req.path.startsWith('/api/')||req.path.startsWith('/auth/'))res.set('Cache-Control','no-store');next()});
app.get('/api/health',(req,res)=>res.json({ok:true,runtime:'node',accounts:configured,mode:cloud?'cloud':'local'}));
app.use((req,res,next)=>{if(['POST','PUT','PATCH','DELETE'].includes(req.method)){
  const sent=req.get('origin');if(sent!==origin&&!( !cloud&&sent===`http://localhost:${port}`))return res.status(403).json({error:'Yêu cầu không đến từ không gian học này.'});
}next()});
app.use('/auth',rateLimit({windowMs:15*60*1000,limit:40,standardHeaders:'draft-8',legacyHeaders:false,message:{error:'Bạn đã thử nhiều lần. Hãy chờ một chút rồi thử lại.'}}));
const options={password:secret,cookieName:cloud?'__Host-qa-session':'qa-session',ttl:60*60*24*7,cookieOptions:{secure:cloud,httpOnly:true,sameSite:'lax',path:'/'}};
app.use(async(req,res,next)=>{try{req.session=await getIronSession(req,res,options);next()}catch{next(Error('Không mở được phiên đăng nhập.'))}});

function authClient(session,token){
  return createClient(process.env.SUPABASE_URL,process.env.SUPABASE_ANON_KEY,{global:token?{headers:{Authorization:`Bearer ${token}`}}:{},auth:{flowType:'pkce',persistSession:false,autoRefreshToken:false,detectSessionInUrl:false,storage:{getItem:key=>session.oauthStorage?.[key]||null,setItem:(key,value)=>{session.oauthStorage||={};session.oauthStorage[key]=value},removeItem:key=>{delete session.oauthStorage?.[key]}}}});
}
async function saveAuth(session,auth){session.access=auth.access_token;session.refresh=auth.refresh_token;session.expires=auth.expires_at;session.authAt=Date.now();delete session.oauthStorage;await session.save()}
async function identify(req){
  if(!configured||!req.session.access)return null;
  let access=req.session.access;
  if((req.session.expires||0)*1000<Date.now()+30000){const {data,error}=await authClient({}).auth.refreshSession({refresh_token:req.session.refresh});if(error||!data.session){req.session.destroy();return null}await saveAuth(req.session,data.session);access=data.session.access_token}
  const {data,error}=await authClient({}).auth.getUser(access);if(error||!data.user){req.session.destroy();return null}return data.user;
}
const publicUser=u=>u?{id:u.id,email:u.email,name:u.user_metadata?.display_name||u.user_metadata?.full_name||'',verified:!!u.email_confirmed_at,providers:(u.identities||[]).map(i=>i.provider)}:null;
function requireConfigured(req,res,next){if(!configured)return res.status(503).json({error:'Tài khoản chưa kết nối Supabase. Bản học trên máy vẫn được giữ.'});next()}
const providerEnabled=p=>['google','facebook'].includes(p)&&process.env[`${p.toUpperCase()}_OAUTH_ENABLED`]==='true';
const badAuth=()=>{const e=Error('Email, mật khẩu hoặc trạng thái xác minh chưa hợp lệ.');e.status=400;return e};
const validatePassword=password=>typeof password==='string'&&password.length>=12&&password.length<=128;
const validateEmail=email=>typeof email==='string'&&email.length<=254&&/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
app.get('/auth/session',async(req,res)=>{const user=await identify(req);res.json({user:publicUser(user),configured,providers:['google','facebook'].filter(providerEnabled),mode:cloud?'cloud':'local',persistent:configured,localProgress:!!local})});
app.post('/auth/signup',requireConfigured,async(req,res)=>{const {email,password,name}=req.body;if(!validateEmail(email)||!validatePassword(password))return res.status(400).json({error:'Nhập email hợp lệ và mật khẩu từ 12 đến 128 ký tự.'});const {data,error}=await authClient(req.session).auth.signUp({email,password,options:{data:{display_name:String(name||'').slice(0,60)},emailRedirectTo:origin+'/auth/callback'}});if(error)throw badAuth();if(data.session)await saveAuth(req.session,data.session);else await req.session.save();res.json({user:publicUser(data.user),verificationRequired:!data.session,message:'Kiểm tra email để xác nhận tài khoản nếu có yêu cầu.'})});
app.post('/auth/login',requireConfigured,async(req,res)=>{const {email,password}=req.body;if(!validateEmail(email)||typeof password!=='string'||password.length>128)throw badAuth();const {data,error}=await authClient({}).auth.signInWithPassword({email,password});if(error||!data.session)throw badAuth();await saveAuth(req.session,data.session);res.json({user:publicUser(data.user)})});
app.post('/auth/logout',async(req,res)=>{if(configured&&req.session.access){const client=authClient({});await client.auth.setSession({access_token:req.session.access,refresh_token:req.session.refresh});await client.auth.signOut({scope:'local'})}req.session.destroy();res.json({ok:true})});
app.post('/auth/forgot',requireConfigured,async(req,res)=>{if(!validateEmail(req.body.email))throw badAuth();await authClient(req.session).auth.resetPasswordForEmail(req.body.email,{redirectTo:origin+'/auth/callback?recovery=1'});req.session.recoveryRequested=Date.now();await req.session.save();res.json({message:'Nếu email có tài khoản, hướng dẫn khôi phục sẽ được gửi.'})});
app.post('/auth/password',requireConfigured,async(req,res)=>{const user=await identify(req);if(!user)return res.status(401).json({error:'Hãy mở liên kết khôi phục từ email trước.'});if(!validatePassword(req.body.password))return res.status(400).json({error:'Mật khẩu cần từ 12 đến 128 ký tự.'});if(!req.session.recoveryAt||Date.now()-req.session.recoveryAt>15*60*1000)return res.status(403).json({error:'Cần liên kết khôi phục mới từ email để đặt mật khẩu.'});const client=authClient({});await client.auth.setSession({access_token:req.session.access,refresh_token:req.session.refresh});const {error}=await client.auth.updateUser({password:req.body.password});if(error)throw badAuth();delete req.session.recoveryAt;await req.session.save();res.json({ok:true})});
app.get('/auth/oauth/:provider',requireConfigured,async(req,res)=>{const provider=req.params.provider;if(!providerEnabled(provider))return res.status(503).send('Nhà cung cấp này chưa được cấu hình.');const state=randomBytes(24).toString('hex');req.session.oauthState=state;req.session.oauthAt=Date.now();const linking=req.query.link==='1';let client=authClient(req.session);if(linking){if(!await identify(req))return res.status(401).send('Hãy đăng nhập trước khi liên kết.');await client.auth.setSession({access_token:req.session.access,refresh_token:req.session.refresh})}const options={redirectTo:origin+'/auth/callback?state='+state,skipBrowserRedirect:true};const {data,error}=linking?await client.auth.linkIdentity({provider,options}):await client.auth.signInWithOAuth({provider,options});if(error||!data.url)throw badAuth();await req.session.save();res.redirect(data.url)});
app.get('/auth/callback',requireConfigured,async(req,res)=>{const state=req.query.state;if(state){const a=Buffer.from(String(state)),b=Buffer.from(req.session.oauthState||'');if(a.length!==b.length||!timingSafeEqual(a,b)||Date.now()-req.session.oauthAt>10*60*1000)return res.status(403).send('Liên kết đăng nhập hết hạn.')}if(typeof req.query.code!=='string')return res.redirect('/#account');const {data,error}=await authClient(req.session).auth.exchangeCodeForSession(req.query.code);if(error||!data.session)throw badAuth();await saveAuth(req.session,data.session);if(req.query.recovery==='1'){req.session.recoveryAt=Date.now();await req.session.save()}delete req.session.oauthState;res.redirect('/#account'+(req.query.recovery==='1'?'/password':''))});

const queues=new Map();
async function ownerQueue(id,fn){const previous=queues.get(id)||Promise.resolve();const task=previous.then(fn);const tail=task.catch(()=>{});queues.set(id,tail);try{return await task}finally{if(queues.get(id)===tail)queues.delete(id)}}
app.post('/auth/guest-summary',async(req,res)=>{if(!local||!await identify(req))return res.status(403).json({error:'Chỉ chuyển dữ liệu tại máy cá nhân sau khi đăng nhập.'});const {body}=await local.read();res.json({lessons:Object.keys(body.progress||{}).length,attempts:body.attempts?.length||0,words:Object.keys(body.vocabReviews||{}).length})});
app.post('/auth/import-guest',async(req,res)=>{const user=await identify(req);if(!local||!user||req.body.confirm!==true)return res.status(403).json({error:'Cần xác nhận chuyển dữ liệu trên máy này.'});await ownerQueue(user.id,async()=>{const old=await persistent.read(user.id),guest=await local.read();const merged=mergeGuest(old.body,guest.body);await persistent.write(user.id,merged,old.version)});res.json({ok:true,message:'Đã chuyển tiến trình. Dữ liệu gốc trên máy được giữ nguyên; lịch sử trùng không cộng xu hai lần.'})});
app.post('/auth/export',async(req,res)=>{const user=await identify(req);const row=user?await persistent.read(user.id):!cloud?await local.read():null;if(!row)return res.status(401).json({error:'Đăng nhập để xuất dữ liệu.'});const active=[...Object.values(row.body.exams||{}),...Object.values(row.body.writingExams||{}),...Object.values(row.body.readingSessions||{})].some(e=>e.mode==='exam'&&!e.submitted&&e.deadline>Date.now()/1000);if(active)return res.status(403).json({error:'Kết thúc bài thi trước khi xuất lịch sử.'});const body=structuredClone(row.body);delete body.guestBackups;res.json({schema:1,exportedAt:new Date().toISOString(),learning:body})});
app.post('/auth/delete-account',requireConfigured,async(req,res)=>{const user=await identify(req);if(!user||req.body.confirm!=='DELETE'||Date.now()-req.session.authAt>5*60*1000)return res.status(403).json({error:'Đăng nhập lại và xác nhận xóa tài khoản trước.'});const {error}=await admin.auth.admin.deleteUser(user.id);if(error)throw Error('Chưa xóa được tài khoản.');req.session.destroy();res.json({ok:true})});

app.use('/api',async(req,res)=>{
  if(req.path.startsWith('/reading-admin/'))return res.status(403).json({error:'Studio nguồn chỉ mở trên máy cá nhân có khóa quản trị.'});
  const user=await identify(req);
  const readonly=['/catalog','/state','/ai-status','/knowledge-status','/reading-list'].includes(req.path)&&req.method==='GET';
  if(cloud&&!user&&!readonly)return res.status(configured?401:503).json({error:configured?'Đăng nhập để lưu và học tiếp.':'Đồng bộ tài khoản chưa kết nối. Bản online chỉ xem trước; tiến trình trên máy vẫn được giữ.'});
  const id=user?.id||'local-guest';
  await ownerQueue(id,async()=>{
    const row=user?await persistent.read(user.id):local?await local.read():{body:freshState()};
    const result=await engine.call(req.originalUrl,req.method,row.body,req.body);
    if(result.state&&result.status<500){if(user)await persistent.write(user.id,result.state,row.version);else if(local)await local.write(result.state)}
    if(cloud&&!user&&req.path==='/catalog'){result.data.readingContent=[];result.data.quizzes={}}
    if(req.path==='/state'&&result.data){delete result.data.guestBackups;delete result.data.guestImports}
    res.status(result.status).json(result.data);
  });
});
app.get('/media/:id',async(req,res)=>{
  if(cloud)return res.status(404).json({error:'Video và PDF gốc vẫn nằm trên laptop, chưa được đưa lên cloud.'});
  const data=JSON.parse(readFileSync(process.env.OCEAN_CATALOG||root+'catalog.private.json','utf8'));const resource=data.resources[req.params.id];
  if(!resource||data.tests.some(t=>t.answer===req.params.id)||/ANSWER/i.test(resource.original||''))return res.status(403).end();
  if(!existsSync(resource.path))return res.status(404).end();
  const user=await identify(req);const current=user?await persistent.read(user.id):await local.read();const active=[...Object.values(current.body.exams||{}),...Object.values(current.body.writingExams||{}),...Object.values(current.body.readingSessions||{})].some(e=>e.mode==='exam'&&!e.submitted&&e.deadline>Date.now()/1000);
  if(active)return res.status(403).json({error:'Học liệu hỗ trợ được ẩn khi đang thi.'});
  res.sendFile(resource.path);
});
app.use(express.static(root+'public',{dotfiles:'deny',setHeaders:(res,path)=>{if(/\.(glb|png|webp|woff2)$/.test(path))res.set('Cache-Control','public, max-age=86400')}}));
app.use((error,req,res,next)=>{res.status(error.status||500).json({error:error.status?error.message:'Kết nối chưa hoàn tất. Tiến trình đã lưu vẫn được giữ; hãy thử lại.'})});
const listener=app.listen(port,cloud?'0.0.0.0':'127.0.0.1',()=>console.log(`Quynh Anh English Node.js: ${origin}`));
for(const event of ['SIGTERM','SIGINT'])process.on(event,()=>listener.close(()=>{engine.close();local?.close();process.exit(0)}));

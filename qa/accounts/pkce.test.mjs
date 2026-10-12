import test from 'node:test';
import assert from 'node:assert/strict';
import {authClient} from '../../node/auth-client.mjs';
process.env.SUPABASE_URL='https://qa-fixture.supabase.co';
process.env.SUPABASE_ANON_KEY='qa-placeholder';

for(const provider of ['google','facebook'])test(provider+' PKCE verifier survives separate HTTP clients without storing full SDK sessions',async()=>{
 const cookie={};
 const start=await authClient(cookie).auth.signInWithOAuth({provider,options:{redirectTo:'http://127.0.0.1/auth/callback',skipBrowserRedirect:true}});
 assert.equal(start.error,null);
 assert.ok(new URL(start.data.url).searchParams.get('code_challenge'));
 const entries=Object.entries(cookie.oauthStorage||{});
 assert.equal(entries.length,1);assert.ok(entries[0][0].endsWith('-code-verifier'));
 const saved=JSON.parse(JSON.stringify(cookie));
 const originalFetch=globalThis.fetch;let seen;
 globalThis.fetch=async(url,options)=>{
   seen={url:String(url),body:JSON.parse(options.body)};
   return new Response(JSON.stringify({access_token:'fixture-access',refresh_token:'fixture-refresh',token_type:'bearer',expires_in:3600,user:{id:'qa-fixture',aud:'authenticated',app_metadata:{},user_metadata:{},created_at:new Date().toISOString()}}),{status:200,headers:{'Content-Type':'application/json'}});
 };
 try{
   const finish=await authClient(saved).auth.exchangeCodeForSession('fixture-code');
   assert.equal(finish.error,null);assert.equal(finish.data.session.access_token,'fixture-access');
   assert.ok(seen.url.includes('grant_type=pkce'));assert.equal(seen.body.auth_code,'fixture-code');
   assert.equal(seen.body.code_verifier,JSON.parse(entries[0][1]).split('/')[0]);
   assert.equal(Object.keys(saved.oauthStorage).length,0);
   assert.ok(!JSON.stringify(saved).includes('fixture-access'));
 }finally{globalThis.fetch=originalFetch}
});

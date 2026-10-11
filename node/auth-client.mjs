import {createClient} from '@supabase/supabase-js';

// Persist only the PKCE verifier between requests. Full SDK session payloads
// stay in this request's memory; the application seals its own compact cookie.
export function authClient(session,token){
  const memory=new Map();
  const verifier=key=>key.endsWith('-code-verifier');
  return createClient(process.env.SUPABASE_URL,process.env.SUPABASE_ANON_KEY,{
    global:token?{headers:{Authorization:`Bearer ${token}`}}:{},
    auth:{flowType:'pkce',persistSession:true,autoRefreshToken:false,detectSessionInUrl:false,
      storage:{
        getItem:key=>verifier(key)?session.oauthStorage?.[key]||null:memory.get(key)||null,
        setItem:(key,value)=>{if(verifier(key)){session.oauthStorage||={};session.oauthStorage[key]=value}else memory.set(key,value)},
        removeItem:key=>{if(verifier(key))delete session.oauthStorage?.[key];else memory.delete(key)}
      }
    }
  });
}

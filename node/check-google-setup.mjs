import {readFileSync} from 'node:fs';
const setup=JSON.parse(readFileSync(new URL('./google-setup.json',import.meta.url),'utf8'));
const origin=process.env.APP_ORIGIN||process.env.RENDER_EXTERNAL_URL||setup.siteUrl;
const supplied=process.env.SUPABASE_URL;
const validOrigin=setup.webOrigins.includes(origin);
let callback=null;try{if(supplied){const u=new URL(supplied);if(u.protocol==='https:'&&u.hostname.endsWith('.supabase.co'))callback=u.origin+'/auth/v1/callback'}}catch{}
console.log(JSON.stringify({appOrigin:origin,originMatchesPreparedSettings:validOrigin,appCallback:origin+'/auth/callback',supabaseCallback:callback||'Read the callback from Supabase provider settings',googleFlagEnabled:process.env.GOOGLE_OAUTH_ENABLED==='true',backendKeysPresent:!!(supplied&&process.env.SUPABASE_ANON_KEY&&process.env.SUPABASE_SERVICE_ROLE_KEY),providerCredentialsVerified:false,realGoogleLoginVerified:false},null,2));
if(!validOrigin)process.exitCode=1;

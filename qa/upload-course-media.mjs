import {createClient} from '@supabase/supabase-js';
import {readFileSync,writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url)),source=fileURLToPath(new URL('../../artifacts/course-media/',import.meta.url));
const prepared=JSON.parse(readFileSync(source+'prepared.json','utf8'));
if(prepared.count<1||prepared.count>52||prepared.bytes>900_000_000)throw Error('Free storage budget or coverage check failed.');
if(!process.env.SUPABASE_URL?.includes('clusiotackzurzqbhflj'))throw Error('Unexpected project');
const client=createClient(process.env.SUPABASE_URL,process.env.SUPABASE_SERVICE_ROLE_KEY,{auth:{persistSession:false}});
const bucket='course-videos';
const {data:buckets,error}=await client.storage.listBuckets();if(error)throw Error('Cannot inspect storage');
if(!buckets.some(b=>b.id===bucket)){const {error}=await client.storage.createBucket(bucket,{public:false,fileSizeLimit:50_000_000,allowedMimeTypes:['video/mp4']});if(error)throw Error('Cannot create private course bucket');}
const manifest={bucket,resources:{}};
for(const row of prepared.resources){
 const object='v1/'+row.file;
 const {data:existing}=await client.storage.from(bucket).list('v1',{search:row.file});
 if(!existing?.some(x=>x.name===row.file&&Number(x.metadata?.size)===row.size)){
  const {error}=await client.storage.from(bucket).upload(object,readFileSync(source+'videos/'+row.file),{contentType:'video/mp4',upsert:true,cacheControl:'3600'});if(error)throw Error('Upload failed for '+row.id);
 }
 const {data:signed,error:signError}=await client.storage.from(bucket).createSignedUrl(object,60);if(signError)throw Error('Cannot verify uploaded media');
 const response=await fetch(signed.signedUrl,{headers:{Range:'bytes=0-1023'}});
 if(response.status!==206||!response.headers.get('content-type')?.includes('video/mp4')||(await response.arrayBuffer()).byteLength!==1024)throw Error('Range playback verification failed '+row.id);
 manifest.resources[row.id]={object,size:row.size,duration:row.duration,sha256:row.sha256};
 console.log(JSON.stringify({uploaded:row.id,rangeVerified:true}));
}
writeFileSync(root+'deploy/course-media.json',JSON.stringify(manifest,null,2));
console.log(JSON.stringify({complete:Object.keys(manifest.resources).length,bytes:prepared.bytes,private:true}));

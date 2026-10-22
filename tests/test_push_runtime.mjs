// Exercise the actual Cloudflare local runtime and D1, without an account.
import assert from 'node:assert/strict';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {spawn} from 'node:child_process';
import {createECDH,randomBytes} from 'node:crypto';
import path from 'node:path';
const folder=path.resolve('build/push-smoke');await mkdir(folder,{recursive:true});
const config=JSON.parse(await readFile('push/wrangler.example.jsonc','utf8'));
config.main=path.resolve('push/worker.mjs');config.assets.directory=path.resolve('site');config.vars={SITE_ORIGIN:'https://kart.example',VAPID_SUBJECT:'mailto:test@example.com'};
config.d1_databases[0].database_id='00000000-0000-4000-8000-000000000001';config.d1_databases[0].migrations_dir=path.resolve('push/migrations');
const configPath=path.join(folder,'wrangler.json');await writeFile(configPath,JSON.stringify(config));
const key=createECDH('prime256v1');key.generateKeys();await writeFile(path.join(folder,'.dev.vars'),'VAPID_PUBLIC_KEY="'+key.getPublicKey().toString('base64url')+'"\nVAPID_PRIVATE_KEY="'+key.getPrivateKey().toString('base64url')+'"\n',{mode:0o600});
const env={...process.env,WRANGLER_SEND_METRICS:'false',CI:'true'};
function command(args){return new Promise((resolve,reject)=>{const child=spawn(process.execPath,['node_modules/wrangler/bin/wrangler.js',...args],{env,stdio:['ignore','pipe','pipe']});let output='';child.stdout.on('data',d=>{output+=d;});child.stderr.on('data',d=>{output+=d;});const timeout=setTimeout(()=>{child.kill();reject(Error('CLI timed out'));},45000);child.on('error',reject);child.on('close',code=>{clearTimeout(timeout);if(code)reject(Error(output.slice(-3000)));else resolve();});});}
await command(['d1','migrations','apply','DB','--local','--config',configPath]);
const child=spawn(process.execPath,['node_modules/wrangler/bin/wrangler.js','dev','--config',configPath,'--local','--ip','127.0.0.1','--port','8787','--inspector-port','9230'],{env,stdio:['ignore','pipe','pipe']});
try{
 await new Promise((resolve,reject)=>{let output='';const timeout=setTimeout(()=>reject(Error('Local runtime start timed out: '+output.slice(-1500))),45000);const receive=data=>{output+=data;if(output.includes('Ready on')){clearTimeout(timeout);resolve();}};child.stdout.on('data',receive);child.stderr.on('data',receive);child.once('exit',code=>{clearTimeout(timeout);reject(Error('Runtime exited '+code+': '+output.slice(-1500)));});});
 const base='http://127.0.0.1:8787',configResponse=await (await fetch(base+'/api/push/config')).json();assert.equal(configResponse.enabled,true);assert(!JSON.stringify(configResponse).includes('private'));
 const token=randomBytes(32).toString('base64url'),headers={Origin:'https://kart.example',Authorization:'Bearer '+token,'Content-Type':'application/json'};
 const subscription={endpoint:'https://fcm.googleapis.com/fcm/send/local-smoke',keys:{p256dh:key.getPublicKey().toString('base64url'),auth:randomBytes(16).toString('base64url')}};
 let response=await fetch(base+'/api/push/subscription',{method:'PUT',headers,body:JSON.stringify({subscription,preferences:{saved:['example'],hours:24}})});assert.equal(response.status,200,await response.text());
 response=await fetch(base+'/api/push/subscription',{headers});assert.equal((await response.json()).enabled,true);
 response=await fetch(base+'/api/push/subscription',{method:'DELETE',headers});assert.equal(response.status,200);
 response=await fetch(base+'/api/push/subscription',{headers});assert.equal((await response.json()).enabled,false);
 assert.equal((await fetch(base+'/coverage.html')).status,404);assert.equal((await fetch(base+'/')).status,200);assert.equal((await fetch(base+'/push-sw.js')).status,200);
 console.log('Cloudflare runtime smoke: authenticated subscription/deletion, actual local D1, private config and public assets passed.');
}finally{child.kill('SIGTERM');}

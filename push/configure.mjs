// Generates local deployment configuration and secrets. Nothing is published.
import {readFile,writeFile,mkdir,access} from 'node:fs/promises';
const args=Object.fromEntries(process.argv.slice(2).map(value=>{const at=value.indexOf('=');return [value.slice(0,at),value.slice(at+1)];}));
const {origin,contact,database}=args;
if(!origin||!contact||!database)throw Error('Usage: npm run push:configure -- origin=https://YOUR-SITE contact=you@example.com database=D1-UUID');
const url=new URL(origin);
if(url.protocol!=='https:'||url.origin!==origin||url.username||url.password)throw Error('Use the exact public HTTPS origin, without a trailing slash or path.');
if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(contact))throw Error('Use a real support/contact email for the push providers.');
if(!/^[a-f0-9-]{36}$/i.test(database))throw Error('Use the database UUID returned by Cloudflare.');
const config=JSON.parse(await readFile('push/wrangler.example.jsonc','utf8'));
config.vars={SITE_ORIGIN:origin,VAPID_SUBJECT:'mailto:'+contact};config.d1_databases[0].database_id=database;
await writeFile('push/wrangler.json',JSON.stringify(config,null,2)+'\n',{mode:0o600});
await mkdir('push/.keys',{recursive:true,mode:0o700});
try{await access('push/.keys/vapid.json');console.log('Kept existing notification identity. Do not rotate keys after people subscribe.');}
catch{
 const pair=await crypto.subtle.generateKey({name:'ECDSA',namedCurve:'P-256'},true,['sign','verify']);
 const publicBytes=await crypto.subtle.exportKey('raw',pair.publicKey),jwk=await crypto.subtle.exportKey('jwk',pair.privateKey);
 const keys={VAPID_PUBLIC_KEY:Buffer.from(publicBytes).toString('base64url'),VAPID_PRIVATE_KEY:jwk.d};
 await writeFile('push/.keys/vapid.json',JSON.stringify(keys)+'\n',{mode:0o600});
}
console.log('Prepared local configuration and private signing keys. Follow push/README.md to activate; no deployment was performed.');

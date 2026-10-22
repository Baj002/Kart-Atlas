import {cp,mkdir,readFile,writeFile,rm} from 'node:fs/promises';
import {build} from 'esbuild';
import release from './release.json' with {type:'json'};
const out='dist/mobile';await rm(out,{recursive:true,force:true});await mkdir(out,{recursive:true});
// Only public product assets are shipped; no research reports or source inventories.
for(const name of ['index.html','clubs.html','app.js','clubs.js','registration.js','reminders.js','styles.css','events.json','clubs.json','icon-192.png','icon-512.png'])await cp('site/'+name,out+'/'+name);
await mkdir(out+'/vendor',{recursive:true});
for(const name of ['leaflet.js','leaflet.css','images'])await cp('node_modules/leaflet/dist/'+name,out+'/vendor/'+name,{recursive:true});
for(const name of ['index.html','clubs.html']){
 let html=await readFile(out+'/'+name,'utf8');
 html=html.replaceAll('https://unpkg.com/leaflet@1.9.4/dist/','/vendor/');
 html=html.replace(/<script defer src="\/push.js[^"]*"><\/script>/g,'');
 html=html.replace('<head>','<head><meta http-equiv="Content-Security-Policy" content="default-src \'self\'; script-src \'self\'; style-src \'self\' \'unsafe-inline\'; img-src \'self\' data: blob: https://*.basemaps.cartocdn.com https://*.tile.openstreetmap.org; connect-src \'self\' https://raw.githubusercontent.com; object-src \'none\'; base-uri \'self\'; form-action \'none\'">');
 const at=html.indexOf('<script');html=html.slice(0,at)+'<script defer src="/native.js"></script>'+html.slice(at);
 html=html.replace(/<link rel="manifest"[^>]*>/g,'');
 await writeFile(out+'/'+name,html);
}
await build({entryPoints:['mobile/native.mjs'],bundle:true,format:'iife',outfile:out+'/native.js',target:['es2022'],minify:true});
await writeFile(out+'/build-info.json',JSON.stringify({version:release.version,buildNumber:release.buildNumber,dataBaseUrl:release.dataBaseUrl},null,2));
console.log('Prepared offline mobile assets for Kart Atlas '+release.version);

'use strict';
const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
class Element{constructor(tag){this.tag=tag;this.children=[];this.textContent='';}append(...nodes){this.children.push(...nodes);}}
async function render(ok){
  const elements={};const document={createElement:t=>new Element(t),querySelector:s=>elements[s]??=new Element('div')};
  const data={generated_at:'2026-10-19T00:00:00Z',sources_reached:1,sources_attempted:2,source_reach_percent:50,event_candidates:1,organizer_leads:2,deferred_links:3,
    adapters:{'pdf-text':{responses:2,race_observations:5}},excluded_asset_leads:4,
    by_country:{USA:{sources_reached:1,sources_attempted:2,future_races:5,regions_with_races:['CT']}},
    regional_gaps:[{name:'Connecticut',country:'USA',directory_leads:1,organizer_sources:1,organizer_sources_reached:0}],
    date_conflicts:[{name:'Club Race',published_start:'2026-10-23',published_end:'2026-10-25',observed_start:'2026-10-24',observed_end:'2026-10-25',observed_source:'https://club.example/'}],
    sources:[{club:'<script>alert(1)</script>',pages:[{events:5,parser:'pdf-text'}],attempted:1,trusted:true,url:'javascript:alert(1)',remaining_links:0,errors:[],documents:['https://club.example/schedule.pdf']}],unmonitored_clubs:[]};
  await vm.runInNewContext(fs.readFileSync('site/coverage.js','utf8'),{document,URL,fetch:async()=>({ok,json:async()=>data})});
  return elements;
}
(async()=>{
  const nodes=await render(true);
  assert.equal(nodes['#countries'].children.length,1);
  assert.equal(nodes['#regional-gaps'].children.length,1);
  assert.equal(nodes['#date-conflicts'].children.length,1);
  assert.match(nodes['#adapter-summary'].textContent,/2 PDF responses/);
  assert.equal(nodes['#sources'].children[0].children[1].tag,'span','Unsafe source URL must not become a link');
  assert.match(nodes['#sources'].children[0].children[0].textContent,/<script>/,'Untrusted label must remain text');
  const offline=await render(false);assert.match(offline['#coverage-status'].textContent,/unavailable/);
  process.stdout.write('Coverage UI checks passed: metrics, review gaps, unsafe URLs and failed fetches.\n');
})().catch(error=>{process.stderr.write(error.stack+'\n');process.exitCode=1;});

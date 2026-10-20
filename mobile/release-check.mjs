import {readFile} from 'node:fs/promises';
const config=JSON.parse(await readFile('mobile/release.json','utf8'));
const blockers=[];
for(const field of ['publisherName','supportEmail','privacyPolicyUrl'])if(!config[field])blockers.push(field+' must be confirmed');
for(const field of ['appIdConfirmed','physicalDeviceTestingConfirmed','privacyDisclosuresReviewed'])if(config[field]!==true)blockers.push(field+' must be confirmed');
if(config.supportEmail&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(config.supportEmail))blockers.push('Invalid support email');
if(config.privacyPolicyUrl&&!/^https:\/\//.test(config.privacyPolicyUrl))blockers.push('Privacy policy must have a public HTTPS URL');
if(blockers.length){console.error('Store submission blocked:\n- '+blockers.join('\n- '));process.exitCode=1;}else console.log('Owner-provided release metadata is complete. Signing and store review are still required.');

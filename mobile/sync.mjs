import {existsSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
const targets=process.argv.slice(2).length?process.argv.slice(2):['android','ios'];
for(const target of targets){if(!['android','ios'].includes(target))throw Error('Unknown platform');if(!existsSync(target))execFileSync('npx',['--no-install','cap','add',target],{stdio:'inherit'});}
execFileSync('python',['mobile/configure-platforms.py'],{stdio:'inherit'});
for(const target of targets)execFileSync('npx',['--no-install','cap','sync',target],{stdio:'inherit'});

import {existsSync,readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

export function validateApiBaseUrl(value) {
  const raw=String(value??'').trim();
  if(!raw) throw new Error('VITE_API_BASE_URL must be configured for deployment');
  if(raw==='/api/v1') return raw;
  let url;
  try {url=new URL(raw)} catch {
    throw new Error('VITE_API_BASE_URL must be /api/v1 or an absolute HTTPS API URL');
  }
  const host=url.hostname.toLowerCase();
  if(url.protocol!=='https:' || !host ||
      ['localhost','127.0.0.1','::1','[::1]'].includes(host) ||
      url.username || url.password || url.search || url.hash ||
      url.pathname.replace(/\/$/,'')!=='/api/v1'){
    throw new Error('VITE_API_BASE_URL must be /api/v1 or a public HTTPS URL ending in /api/v1');
  }
  return url.href.replace(/\/$/,'');
}

function readValue(file){
  if(!existsSync(file)) return null;
  for(const line of readFileSync(file,'utf8').split(/\r?\n/)){
    const match=line.match(/^\s*(?:export\s+)?VITE_API_BASE_URL\s*=\s*(.*?)\s*$/);
    if(!match) continue;
    const raw=match[1].trim();
    if((raw.startsWith('"')&&raw.endsWith('"'))||(raw.startsWith("'")&&raw.endsWith("'")))
      return raw.slice(1,-1);
    return raw.replace(/\s+#.*$/,'');
  }
  return null;
}

function configuredValue(){
  if(process.env.VITE_API_BASE_URL!==undefined) return process.env.VITE_API_BASE_URL;
  for(const name of ['.env.production.local','.env.production','.env.local','.env']){
    const v=readValue(resolve(process.cwd(),name));
    if(v!==null) return v;
  }
  return null;
}

if(process.argv[1] && resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  try {
    console.log('[OK] Deployment API URL:',validateApiBaseUrl(configuredValue()));
  }catch(err){
    console.error('[ERROR] Deployment build blocked:',err.message);
    console.error('Set VITE_API_BASE_URL=https://YOUR-API-HOST/api/v1 or /api/v1 behind a same-origin HTTPS proxy.');
    process.exitCode=1;
  }
}

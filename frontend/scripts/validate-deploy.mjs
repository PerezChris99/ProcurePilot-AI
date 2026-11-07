import {existsSync,readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

export function validateApiBaseUrl(value) {
  // ProcurePilot's Vercel Services host both FastAPI and Vite on one origin.
  // Reject absolute URLs here: a stale API hostname in a production bundle
  // makes fetch fail via DNS, CORS, or deployment protection.
  if (String(value ?? '').trim() !== '/api/v1') {
    throw new Error('VITE_API_BASE_URL must be exactly /api/v1 for Vercel Services production and preview deployments');
  }
  return '/api/v1';
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
    console.error('Set VITE_API_BASE_URL=/api/v1 in Vercel Production and Preview.');
    process.exitCode=1;
  }
}

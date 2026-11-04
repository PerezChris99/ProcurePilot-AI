const API_BASE_URL=import.meta.env.VITE_API_BASE_URL||'http://localhost:8000/api/v1';
let accessToken=null;
export function setAuthToken(token){accessToken=token||null}
export async function apiRequest(path,options={}){const response=await fetch(API_BASE_URL+path,{...options,headers:{Accept:'application/json',...(options.body?{'Content-Type':'application/json'}:{}),...(accessToken?{Authorization:'Bearer '+accessToken}:{}),...options.headers}});if(!response.ok){const payload=await response.json().catch(()=>({}));throw new Error(typeof payload.detail==='string'?payload.detail:Array.isArray(payload.detail)?payload.detail.map(error=>error.msg||'Invalid input').join('; '):'Request failed with status '+response.status)}return response.status===204?null:response.json()}
export function getHealth(){return apiRequest('/health')}
export function getIntegrationStatus(){return apiRequest('/integrations/status')}
export function getDashboardSummary(){return apiRequest('/dashboard/summary')}

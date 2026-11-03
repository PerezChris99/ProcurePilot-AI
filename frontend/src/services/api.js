const API_BASE_URL=import.meta.env.VITE_API_BASE_URL||'http://localhost:8000/api/v1';
export async function apiRequest(path,options={}){const response=await fetch(API_BASE_URL+path,{...options,headers:{Accept:'application/json',...(options.body?{'Content-Type':'application/json'}:{}),...options.headers}});if(!response.ok){const payload=await response.json().catch(()=>({}));throw new Error(payload.detail||'Request failed with status '+response.status)}return response.status===204?null:response.json()}
export function getHealth(){return apiRequest('/health')}

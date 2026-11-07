const API_BASE_URL=(import.meta.env.VITE_API_BASE_URL||'http://localhost:8000/api/v1').replace(/\/+$/,'');
function checkRemoteApiConfiguration(){
  if(typeof window==='undefined')return;
  const local=['localhost','127.0.0.1','::1','[::1]'];
  const apiHost=new URL(API_BASE_URL,window.location.href).hostname;
  if(!local.includes(window.location.hostname)&&local.includes(apiHost)){
    throw new Error('This deployment targets a localhost API. Set VITE_API_BASE_URL to a public HTTPS backend and rebuild.');
  }
}
const TOKEN_KEY='procurepilot_access_token';
export const SESSION_EXPIRED_EVENT='procurepilot:session-expired';
let accessToken=null;
export function setAuthToken(token){accessToken=token||null}
export async function apiRequest(path,options={}){
  checkRemoteApiConfiguration();
  let response;
  const tokenForRequest=accessToken;
  try{
    response=await fetch(API_BASE_URL+path,{
      ...options,
      headers:{
        Accept:'application/json',
        ...(options.body?{'Content-Type':'application/json'}:{}),
        ...(tokenForRequest?{Authorization:'Bearer '+tokenForRequest}:{}),
        ...options.headers,
      },
    });
  }catch(error){
    if(error instanceof TypeError){
      throw new Error('Cannot reach the ProcurePilot API. Check the backend and database connection; review existing orders before retrying any purchase action.',{cause:error});
    }
    throw error;
  }
  if(!response.ok){
    const payload=await response.json().catch(()=>({}));
    const error=new Error(typeof payload.detail==='string'?payload.detail:
      Array.isArray(payload.detail)?payload.detail.map(item=>item.msg||'Invalid input').join('; '):
      'Request failed with status '+response.status);
    error.status=response.status;
    // Only a protected request made with the CURRENT token can invalidate
    // the workspace session. An incorrect login must never sign out a user.
    const isAuthEntry=path==='/auth/login'||path==='/auth/register';
    if(response.status===401&&accessToken&&tokenForRequest===accessToken&&!isAuthEntry){
      setAuthToken(null);
      sessionStorage.removeItem(TOKEN_KEY);
      window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT));
    }
    throw error;
  }
  return response.status===204?null:response.json();
}
export function getHealth(){return apiRequest('/health')}
export function getIntegrationStatus(){return apiRequest('/integrations/status')}
export function getDashboardSummary(){return apiRequest('/dashboard/summary')}

/* Authenticated exports do not expose session tokens in query strings or URLs. */
export async function downloadAuthorizedFile(path,filename){
  checkRemoteApiConfiguration();
  const response=await fetch(API_BASE_URL+path,{
    headers:{Accept:'application/pdf, application/json',...(accessToken?{Authorization:'Bearer '+accessToken}:{})},
  });
  if(!response.ok)throw new Error('Could not download this decision record.');
  const blob=await response.blob();
  const objectUrl=URL.createObjectURL(blob);
  try{
    const anchor=document.createElement('a');
    anchor.href=objectUrl;
    anchor.download=filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
  }finally{
    URL.revokeObjectURL(objectUrl);
  }
}

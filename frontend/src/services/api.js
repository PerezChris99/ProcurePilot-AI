// This project deploys FastAPI and Vite under the same Vercel Services origin.
// A Vite build must never bake a localhost or unrelated API host into prod JS.
// The development server still supports a standalone backend on port 8000.
const API_BASE_URL=(import.meta.env.PROD
  ? '/api/v1'
  : (import.meta.env.VITE_API_BASE_URL||'http://localhost:8000/api/v1')
).replace(/\/+$/,'');
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
      const failure=new Error('ProcurePilot API connection failed before receiving an HTTP response. Check /api/v1/health and /api/v1/ready on this site; avoid retrying payments until an order is checked.',{cause:error});
      failure.code='API_NETWORK_FAILURE';
      failure.requestPath=path;
      throw failure;
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
  if(response.status===204)return null;
  const contentType=response.headers?.get?.('content-type');
  if(contentType && !contentType.toLowerCase().includes('application/json')){
    const error=new Error('The /api/v1 route returned a non-JSON response. Verify the Vercel Services backend route rather than signing in again.');
    error.code='API_ROUTE_MISMATCH';
    error.status=response.status;
    throw error;
  }
  return response.json();
}
export function getHealth({force=false}={}){return apiRequest('/health',force?{cache:'no-store'}:{})}
export function getIntegrationStatus({force=false}={}){return apiRequest('/integrations/status',force?{cache:'no-store'}:{})}
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

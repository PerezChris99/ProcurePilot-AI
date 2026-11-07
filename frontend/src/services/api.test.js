import {afterEach,beforeEach,describe,expect,it,vi} from 'vitest';
import {apiRequest,setAuthToken,SESSION_EXPIRED_EVENT} from './api.js';

describe('Authenticated API client',()=>{
  beforeEach(()=>setAuthToken(null));
  afterEach(()=>{
    setAuthToken(null);
    vi.unstubAllGlobals();
  });

  it('sends a saved bearer token and JSON request through API prefix',async()=>{
    const fetchMock=vi.fn().mockResolvedValue({
      ok:true,status:200,json:async()=>({status:'approved'}),
    });
    vi.stubGlobal('fetch',fetchMock);
    setAuthToken('qa-session-token');
    const result=await apiRequest('/purchase-orders/test/approve',{
      method:'POST',body:JSON.stringify({comment:'Reviewed'}),
    });
    expect(result).toEqual({status:'approved'});
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringMatching(/\/api\/v1\/purchase-orders\/test\/approve$/),
      expect.objectContaining({
        method:'POST',
        headers:expect.objectContaining({
          Authorization:'Bearer qa-session-token',
          'Content-Type':'application/json',
        }),
      }),
    );
  });

  it('fails visibly on an API rejection instead of assuming payment success',async()=>{
    vi.stubGlobal('fetch',vi.fn().mockResolvedValue({
      ok:false,status:409,json:async()=>({
        detail:'PayPal capture did not match approved amount',
      }),
    }));
    await expect(apiRequest('/purchase-orders/test/payments/paypal/capture',{
      method:'POST',
    })).rejects.toThrow('PayPal capture did not match approved amount');
  });

  it('explains a dropped API connection instead of displaying Failed to fetch',async()=>{
    vi.stubGlobal('fetch',vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));
    await expect(apiRequest('/procurement-requests/test/analyze',{
      method:'POST',
    })).rejects.toThrow(/Cannot reach the ProcurePilot API/);
  });

  it('does not send authorization after logout',async()=>{
    const fetchMock=vi.fn().mockResolvedValue({
      ok:true,status:200,json:async()=>({}),
    });
    vi.stubGlobal('fetch',fetchMock);
    setAuthToken('temporary-token');
    setAuthToken(null);
    await apiRequest('/health');
    const headers=fetchMock.mock.calls[0][1].headers;
    expect(headers).not.toHaveProperty('Authorization');
  });
});

const TOKEN_KEY='procurepilot_access_token';
function mockResponse(status,detail){
  return {ok:status>=200&&status<300,status,
    json:async()=>({detail}),headers:{get:()=>null}};
}
describe('Expired session handling',()=>{
  beforeEach(()=>{
    vi.stubGlobal('fetch',vi.fn());
    sessionStorage.clear();
    setAuthToken(null);
  });
  afterEach(()=>{
    vi.unstubAllGlobals();
    sessionStorage.clear();
    setAuthToken(null);
  });
  it('clears a stale bearer token and informs the auth provider on protected 401',async()=>{
    sessionStorage.setItem(TOKEN_KEY,'stale');
    setAuthToken('stale');
    fetch.mockResolvedValue(mockResponse(401,'Invalid or expired authentication token'));
    const onExpired=vi.fn();
    window.addEventListener(SESSION_EXPIRED_EVENT,onExpired);
    try{
      await expect(apiRequest('/trust-lab/scenarios')).rejects.toMatchObject({
        status:401,message:'Invalid or expired authentication token'
      });
      expect(sessionStorage.getItem(TOKEN_KEY)).toBeNull();
      expect(onExpired).toHaveBeenCalledTimes(1);
    }finally{window.removeEventListener(SESSION_EXPIRED_EVENT,onExpired)}
  });
  it('does not treat invalid login credentials as an expired active session',async()=>{
    sessionStorage.setItem(TOKEN_KEY,'still-present');
    setAuthToken('still-present');
    fetch.mockResolvedValue(mockResponse(401,'Invalid email or password'));
    const onExpired=vi.fn();
    window.addEventListener(SESSION_EXPIRED_EVENT,onExpired);
    try{
      await expect(apiRequest('/auth/login',{method:'POST',body:'{}'}))
        .rejects.toMatchObject({status:401});
      expect(sessionStorage.getItem(TOKEN_KEY)).toBe('still-present');
      expect(onExpired).not.toHaveBeenCalled();
    }finally{window.removeEventListener(SESSION_EXPIRED_EVENT,onExpired)}
  });
  it('does not sign out an authenticated user on server failure',async()=>{
    sessionStorage.setItem(TOKEN_KEY,'valid');
    setAuthToken('valid');
    fetch.mockResolvedValue(mockResponse(503,'Temporary failure'));
    await expect(apiRequest('/trust-lab/scenarios')).rejects.toMatchObject({status:503});
    expect(sessionStorage.getItem(TOKEN_KEY)).toBe('valid');
  });
});

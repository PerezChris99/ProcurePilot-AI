import {beforeEach,afterEach,describe,expect,it,vi} from 'vitest';
import {apiRequest,setAuthToken,SESSION_EXPIRED_EVENT} from './api.js';

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

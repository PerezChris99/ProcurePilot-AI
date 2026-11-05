import {afterEach,beforeEach,describe,expect,it,vi} from 'vitest';
import {apiRequest,setAuthToken} from './api.js';

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

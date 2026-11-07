import {useCallback,useEffect,useState} from 'react';
import {useQueryClient} from '@tanstack/react-query';
import {AuthContext} from './auth-context.js';
import {apiRequest,setAuthToken,SESSION_EXPIRED_EVENT} from '../services/api.js';

const TOKEN_KEY='procurepilot_access_token';

export function AuthProvider({children}){
  const queryClient=useQueryClient();
  const [user,setUser]=useState(null);
  const [busy,setBusy]=useState(false);
  const [initializing,setInitializing]=useState(()=>Boolean(sessionStorage.getItem(TOKEN_KEY)));
  const [sessionExpired,setSessionExpired]=useState(false);

  const clearSession=useCallback((expired=false)=>{
    sessionStorage.removeItem(TOKEN_KEY);
    setAuthToken(null);
    setUser(null);
    setSessionExpired(expired);
    // Prevent data from a previous identity remaining in the query cache.
    queryClient.clear();
  },[queryClient]);

  useEffect(()=>{
    const onExpired=()=>clearSession(true);
    window.addEventListener(SESSION_EXPIRED_EVENT,onExpired);
    const token=sessionStorage.getItem(TOKEN_KEY);
    if(!token){
      setInitializing(false);
      return ()=>window.removeEventListener(SESSION_EXPIRED_EVENT,onExpired);
    }
    setAuthToken(token);
    let active=true;
    apiRequest('/auth/me')
      .then(result=>{if(active)setUser(result)})
      .catch(error=>{
        if(active){
          if(error?.status===401)clearSession(true);
          else setUser(null);
        }
      })
      .finally(()=>{if(active)setInitializing(false)});
    return ()=>{
      active=false;
      window.removeEventListener(SESSION_EXPIRED_EVENT,onExpired);
    };
  },[clearSession]);

  async function authenticate(path,payload){
    setBusy(true);
    try{
      const result=await apiRequest(path,{method:'POST',body:JSON.stringify(payload)});
      queryClient.clear();
      sessionStorage.setItem(TOKEN_KEY,result.access_token);
      setAuthToken(result.access_token);
      setUser(result.user);
      setSessionExpired(false);
      return result.user;
    }finally{setBusy(false)}
  }
  const login=payload=>authenticate('/auth/login',payload);
  const register=payload=>authenticate('/auth/register',payload);
  const logout=()=>clearSession(false);
  return <AuthContext.Provider value={{
    user,busy,initializing,sessionExpired,login,register,logout
  }}>{children}</AuthContext.Provider>;
}

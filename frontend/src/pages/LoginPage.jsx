import {useState} from 'react';
import {Link,useLocation,useNavigate} from 'react-router-dom';
import {LockKeyhole,Mail} from 'lucide-react';
import {useAuth} from '../context/useAuth.js';
import AuthLayout from '../components/layout/AuthLayout.jsx';
import AsyncProgress from '../components/ui/AsyncProgress.jsx';
import {preloadWorkspace} from './preloadWorkspace.js';

export default function LoginPage(){
  const [email,setEmail]=useState('');
  const [password,setPassword]=useState('');
  const [error,setError]=useState('');
  const {login,busy,sessionExpired}=useAuth();
  const navigate=useNavigate();
  const location=useLocation();

  async function submit(event){
    event.preventDefault();
    if(busy)return;
    setError('');
    const from=location.state?.from;
    const destination=from
      ?from.pathname+(from.search||'')+(from.hash||'')
      :'/dashboard';
    // Begin fetching the destination while the server verifies credentials.
    preloadWorkspace(destination);
    try{
      await login({email,password});
      navigate(destination,{replace:true});
    }catch(err){setError(err.message)}
  }

  return <AuthLayout>
    <div className="auth-heading">
      <span className="auth-icon"><img src="/favicon.svg" alt="" className="auth-brand-icon"/></span>
      <p className="eyebrow">WELCOME BACK</p>
      <h1>Sign in to ProcurePilot</h1>
      <p>Access your procurement workspace and continue making smarter purchasing decisions.</p>
      {sessionExpired&&<p className="inline-notice" role="status">
        Your session expired. Sign in again to continue where you left off.
      </p>}
    </div>
    <form className="auth-form" onSubmit={submit} aria-busy={busy}>
      <label htmlFor="email">Email address</label>
      <div className="auth-input">
        <Mail size={17}/>
        <input id="email" type="email" autoComplete="email" value={email}
          onChange={event=>setEmail(event.target.value)} placeholder="you@company.com" required/>
      </div>
      <label htmlFor="password">Password</label>
      <div className="auth-input">
        <LockKeyhole size={17}/>
        <input id="password" type="password" autoComplete="current-password"
          value={password} onChange={event=>setPassword(event.target.value)}
          placeholder="Enter your password" required/>
      </div>
      {error&&<p className="auth-error" role="alert">{error}</p>}
      <button className="button button-primary auth-submit" type="submit" disabled={busy}>
        {busy?'Signing in…':'Sign in'}
      </button>
      {busy&&<AsyncProgress label="Verifying your account securely…"/>}
    </form>
    <p className="auth-switch">New to ProcurePilot? <Link to="/register">Create an account</Link></p>
  </AuthLayout>;
}

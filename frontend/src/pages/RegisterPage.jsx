import {useState} from 'react';
import {Link,useNavigate} from 'react-router-dom';
import {LockKeyhole,Mail,UserRound} from 'lucide-react';
import {useAuth} from '../context/useAuth.js';
import AuthLayout from '../components/layout/AuthLayout.jsx';
import AsyncProgress from '../components/ui/AsyncProgress.jsx';
import {preloadWorkspace} from './preloadWorkspace.js';

export default function RegisterPage(){
  const [fullName,setFullName]=useState('');
  const [email,setEmail]=useState('');
  const [password,setPassword]=useState('');
  const [error,setError]=useState('');
  const {register,busy}=useAuth();
  const navigate=useNavigate();

  async function submit(event){
    event.preventDefault();
    if(busy)return;
    setError('');
    // Load the dashboard while registration commits securely on the backend.
    preloadWorkspace('/dashboard');
    try{
      await register({full_name:fullName,email,password});
      navigate('/dashboard',{replace:true});
    }catch(err){setError(err.message)}
  }

  return <AuthLayout>
    <div className="auth-heading">
      <span className="auth-icon"><img src="/favicon.svg" alt="" className="auth-brand-icon"/></span>
      <p className="eyebrow">GET STARTED</p>
      <h1>Create your workspace</h1>
      <p>Set up your account to organize purchasing requests, product discovery, and approvals.</p>
    </div>
    <form className="auth-form" onSubmit={submit} aria-busy={busy}>
      <label htmlFor="fullName">Full name</label>
      <div className="auth-input">
        <UserRound size={17}/>
        <input id="fullName" autoComplete="name" value={fullName}
          onChange={event=>setFullName(event.target.value)}
          placeholder="Your name" minLength={2} maxLength={120} required/>
      </div>
      <label htmlFor="email">Work email</label>
      <div className="auth-input">
        <Mail size={17}/>
        <input id="email" type="email" autoComplete="email" value={email}
          onChange={event=>setEmail(event.target.value)}
          placeholder="you@company.com" required/>
      </div>
      <label htmlFor="password">Password</label>
      <div className="auth-input">
        <LockKeyhole size={17}/>
        <input id="password" type="password" autoComplete="new-password"
          value={password} onChange={event=>setPassword(event.target.value)}
          placeholder="At least 12 characters" minLength={12} maxLength={128} required/>
      </div>
      {error&&<p className="auth-error" role="alert">{error}</p>}
      <button className="button button-primary auth-submit" type="submit" disabled={busy}>
        {busy?'Creating workspace…':'Create account'}
      </button>
      {busy&&<AsyncProgress label="Creating your secure workspace…"/>}
    </form>
    <p className="auth-switch">Already have an account? <Link to="/login">Sign in</Link></p>
  </AuthLayout>;
}

import {Navigate,Outlet,useLocation} from 'react-router-dom';
import {useAuth} from '../../context/useAuth.js';
import AsyncProgress from '../ui/AsyncProgress.jsx';

export default function RequireAuth(){
  const {user,initializing}=useAuth();
  const location=useLocation();
  if(initializing)return <main className="auth-page">
    <AsyncProgress compact label="Restoring your secure session…"/>
  </main>;
  return user?<Outlet/>:<Navigate to="/login" replace state={{from:location}}/>;
}

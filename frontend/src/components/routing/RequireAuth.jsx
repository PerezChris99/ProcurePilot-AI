import {Navigate,Outlet,useLocation} from 'react-router-dom';
import {useAuth} from '../../context/useAuth.js';
export default function RequireAuth(){const {user,initializing}=useAuth();const location=useLocation();if(initializing)return <main className="auth-page"><p>Restoring your secure session…</p></main>;return user?<Outlet/>:<Navigate to="/login" replace state={{from:location}}/>}

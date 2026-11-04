import {Link,NavLink, Outlet, useLocation} from 'react-router-dom';
import {useQuery} from '@tanstack/react-query';
import {
  Activity, ClipboardList, LayoutDashboard, LogOut, Plus,
  Search, ShieldCheck, Sparkles,
} from 'lucide-react';
import {useAuth} from '../../context/useAuth.js';
import {getIntegrationStatus} from '../../services/api.js';

const navigation = [
  {label:'Overview', short:'Home', to:'/dashboard', icon:LayoutDashboard, end:true, group:'workspace'},
  {label:'New procurement', short:'New', to:'/procurement', icon:Plus, group:'workspace'},
  {label:'Purchase orders', short:'Orders', to:'/orders', icon:ClipboardList, group:'workspace'},
  {label:'Approvals', short:'Approve', to:'/approvals', icon:ShieldCheck, group:'workspace'},
  {label:'Activity', short:'Activity', to:'/activity', icon:Activity, group:'manage'},
  {label:'Product discovery', short:'Discover', to:'/discovery', icon:Search, group:'manage'},
];
const labels = Object.fromEntries(navigation.map(({to,label})=>[to,label]));

function NavigationLinks({items, mobile=false, detailSelected=false}){
  return items.map(({label,short,to,icon:Icon,end})=>(
    <NavLink
      key={to}
      to={to}
      end={end}
      aria-label={label}
      className={({isActive})=>(mobile?'mobile-dock-link':'nav-link')+((isActive||(detailSelected&&to==='/discovery'))?' active':'')}
    >
      <Icon size={mobile?19:18} strokeWidth={mobile?1.9:1.8} aria-hidden="true"/>
      <span>{mobile?short:label}</span>
    </NavLink>
  ));
}

export default function AppShell(){
  const {pathname}=useLocation();
  const {user,logout}=useAuth();
  const {data:integrations,isPending,isError}=useQuery({
    queryKey:['integration-status'],
    queryFn:getIntegrationStatus,
    staleTime:15000,
    refetchInterval:60000,
    refetchOnWindowFocus:true,
  });
  const initials=(user?.full_name||user?.email||'U').slice(0,1).toUpperCase();
  const onRequestDetail=pathname.startsWith('/requests/');
  const pageLabel=labels[pathname]||(onRequestDetail?'Product discovery':'Workspace');
  const aiConfigured=integrations?.ai?.configured===true;
  const aiState=isPending?'Checking settings':isError?'Status unavailable':aiConfigured?'Key configured':'Key not configured';
  const payMode=integrations?.paypal?.environment;
  const runtime=integrations?.runtime?.environment;
  const environmentLabel=isPending?'CHECKING ENVIRONMENT':
    isError?'ENVIRONMENT UNAVAILABLE':
    [runtime==='production'?'PRODUCTION':runtime==='staging'?'STAGING':runtime==='development'?'LOCAL DEMO':runtime==='testing'||runtime==='test'?'TEST ENVIRONMENT':'ENVIRONMENT UNKNOWN',
     payMode==='live'?'PAYPAL LIVE':payMode==='sandbox'?'PAYPAL SANDBOX':'PAYPAL UNKNOWN'].join(' · ');

  return <div className="app-frame">
    <aside className="sidebar">
      <NavLink className="brand" to="/dashboard" aria-label="ProcurePilot AI home">
        <span className="brand-mark"><img src="/favicon.svg" className="brand-logo" alt=""/></span>
        <span><strong>procurepilot</strong><small>INTELLIGENT PROCUREMENT</small></span>
      </NavLink>
      <div className="workspace-switcher" aria-label="Current workspace">
        <span className="workspace-avatar">{initials}</span>
        <span><strong>My workspace</strong><small>Personal workspace</small></span>
      </div>
      <p className="nav-label">WORKSPACE</p>
      <nav className="primary-nav" aria-label="Main navigation">
        <NavigationLinks items={navigation.filter(item=>item.group==='workspace')}/>
      </nav>
      <p className="nav-label nav-label-spaced">MANAGE</p>
      <nav className="primary-nav" aria-label="Management navigation">
        <NavigationLinks items={navigation.filter(item=>item.group==='manage')} detailSelected={onRequestDetail}/>
      </nav>
      <div className="sidebar-bottom">
        <div className="ai-status">
          <span className={'status-dot '+(aiConfigured?'':'status-dot-muted')}/>
          <span><strong>Gemini configuration</strong><small>{aiState}</small></span>
          <Sparkles size={16} aria-hidden="true"/>
        </div>
        <div className="profile-row">
          <span className="profile-avatar">{initials}</span>
          <span><strong>{user?.full_name||'Account'}</strong><small>{user?.email}</small></span>
          <button type="button" className="icon-button" aria-label="Sign out" onClick={logout}><LogOut size={17}/></button>
        </div>
      </div>
    </aside>
    <main className="main-panel">
      <header className="topbar">
        <div className="breadcrumb">
          <span>Workspace</span><span className="breadcrumb-separator">/</span>
          <strong>{pageLabel}</strong>
        </div>
        <div className="topbar-right">
          <span className="environment-pill" title="Server environment and PayPal mode are read from your backend">
            <span className={'status-dot '+(isError?'status-dot-muted':'')}/>
            {environmentLabel}
          </span>
          <span className="profile-avatar top-avatar" aria-hidden="true">{initials}</span>
          <button type="button" className="icon-button mobile-signout" aria-label="Sign out" onClick={logout}><LogOut size={18}/></button>
        </div>
      </header>
      <div className="page-content"><Outlet/></div>
      <footer className="app-legal-footer" aria-label="Workspace legal information">
        <span>© 2026 ProcurePilot AI</span>
        <nav aria-label="Legal links">
          <Link to="/privacy">Privacy</Link>
          <Link to="/terms">Terms</Link>
          <Link to="/security">Security</Link>
          <Link to="/contact">Contact</Link>
          <Link to="/">Public site</Link>
        </nav>
      </footer>
    </main>
    <nav className="mobile-dock" aria-label="Mobile workspace navigation">
      <NavigationLinks items={navigation} mobile detailSelected={onRequestDetail}/>
    </nav>
  </div>;
}

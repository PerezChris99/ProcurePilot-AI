import {ArrowDownRight,ArrowRight,ArrowUpRight,Clock3,PackageSearch,Plus,ReceiptText,ShieldCheck,Sparkles,Wallet} from 'lucide-react';
import {Link} from 'react-router-dom';
import {useQuery} from '@tanstack/react-query';
import {getHealth,getIntegrationStatus,getDashboardSummary} from '../services/api.js';
import {useAuth} from '../context/useAuth.js';
import IntegrationStatusPanel from '../components/ui/IntegrationStatusPanel.jsx';
const today=new Intl.DateTimeFormat('en-US',{weekday:'long',month:'long',day:'numeric',year:'numeric'}).format(new Date()).toUpperCase();

export default function DashboardPage(){
 const {user}=useAuth();
 const hour=new Date().getHours();
 const greeting=hour<12?'Good morning':hour<17?'Good afternoon':'Good evening';
 const name=(user?.full_name||'').trim().split(/\s+/)[0]?.slice(0,35)||'there';
 const health=useQuery({queryKey:['api-health'],queryFn:getHealth,retry:false,refetchInterval:30000,refetchOnWindowFocus:true});
 const integrations=useQuery({queryKey:['integration-status'],queryFn:getIntegrationStatus,retry:false,staleTime:15000,refetchInterval:60000,refetchOnWindowFocus:true});
 const summaryQuery=useQuery({queryKey:['dashboard-summary'],queryFn:getDashboardSummary,retry:false});
 const summary=summaryQuery.data;
 const value=key=>summary?String(summary[key]??0):'—';
 const metrics=[
  {label:'Completed purchases',value:value('completed_orders'),change:'Confirmed paid orders',icon:Wallet,tone:'blue'},
  {label:'Active purchase orders',value:value('active_orders'),change:'Open purchasing workflows',icon:ReceiptText,tone:'violet'},
  {label:'Awaiting approval',value:value('pending_approvals'),change:'Submitted for approval',icon:ShieldCheck,tone:'amber'},
  {label:'Requests with results',value:value('requests_with_results'),change:'Catalogue searches completed',icon:PackageSearch,tone:'cyan'}
 ];
 return <div className="dashboard-page"><section className="welcome-row"><div><p className="eyebrow">{today}</p><h1>{greeting}, {name}. <span>Let&apos;s buy smarter.</span></h1><p className="page-subtitle">Your procurement command centre. Discover, compare, approve, and purchase with confidence.</p></div><Link to="/procurement" className="button button-primary"><Plus size={17}/> New procurement</Link></section><section className="hero-card"><div className="hero-copy"><span className="hero-kicker"><Sparkles size={14}/> YOUR AI PROCUREMENT COPILOT</span><h2>From purchasing request<br/>to <span>approved purchase.</span></h2><p>Tell ProcurePilot what your business needs. Get evidence-based product recommendations, prepare a purchase order, and stay in control of every approval.</p><Link to="/procurement" className="button button-light">Start a procurement <ArrowRight size={16}/></Link></div><div className="hero-art" aria-hidden="true"><div className="orbit orbit-one"/><div className="orbit orbit-two"/><div className="orbit-core"><PackageSearch size={42}/></div><div className="orbit-chip chip-top"><PackageSearch size={17}/></div><div className="orbit-chip chip-right"><ShieldCheck size={17}/></div><div className="orbit-chip chip-bottom"><ReceiptText size={17}/></div></div></section><section className="section-heading"><div><h2>Procurement overview</h2><p>Your business purchasing activity at a glance.</p></div><span className="period-label">ALL TIME <ArrowDownRight size={14}/></span></section><section className="metrics-grid">{metrics.map(({label,value,change,icon:Icon,tone})=><article className="metric-card" key={label}><div className="metric-top"><span>{label}</span><span className={'metric-icon '+tone}><Icon size={18}/></span></div><strong className="metric-value">{value}</strong><span className="metric-note">{change}</span></article>)}</section><section className="dashboard-columns"><article className="panel activity-panel"><div className="panel-heading"><div><h3>Recent activity</h3><p>Updates from your procurement workspace</p></div><Link to="/orders" className="text-link">View all <ArrowRight size={14}/></Link></div>{summaryQuery.isPending?<div className="empty-state"><p>Loading activity…</p></div>:summaryQuery.isError?<div className="empty-state"><strong>Activity unavailable</strong><p>Could not load current workspace activity.</p></div>:summary?.recent_activity?.length?<ol className="dashboard-activity-list">{summary.recent_activity.map(event=><li key={event.id}><span>{event.action.replaceAll('.', ' · ').replaceAll('_',' ')}</span><time>{new Date(event.created_at).toLocaleString()}</time></li>)}</ol>:<div className="empty-state"><span className="empty-icon"><Clock3 size={23}/></span><strong>No activity yet</strong><p>Your procurement requests, approvals, and completed purchases will appear here.</p><Link to="/procurement" className="text-link">Create your first request <ArrowRight size={14}/></Link></div>}</article><IntegrationStatusPanel health={health} integrations={integrations}/></section><p className="dashboard-footnote"><ArrowUpRight size={13}/> ProcurePilot AI is in active development. Dashboard counts come from saved workspace records, without adding unlike currencies.</p></div>
}

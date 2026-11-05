import {ArrowRight,Plus} from 'lucide-react';
import {Link} from 'react-router-dom';
import {useQuery} from '@tanstack/react-query';
import {getHealth,getIntegrationStatus,getDashboardSummary} from '../services/api.js';
import {useAuth} from '../context/useAuth.js';
import IntegrationStatusPanel from '../components/ui/IntegrationStatusPanel.jsx';

export default function DashboardPage(){
  const {user}=useAuth();
  const hour=new Date().getHours();
  const greeting=hour<12?'Good morning':hour<17?'Good afternoon':'Good evening';
  const name=(user?.full_name||'').trim().split(/\s+/)[0]?.slice(0,35)||'there';
  const health=useQuery({
    queryKey:['api-health'],queryFn:getHealth,retry:false,
    refetchInterval:30000,refetchOnWindowFocus:true,
  });
  const integrations=useQuery({
    queryKey:['integration-status'],queryFn:getIntegrationStatus,retry:false,
    staleTime:15000,refetchInterval:60000,refetchOnWindowFocus:true,
  });
  const summaryQuery=useQuery({
    queryKey:['dashboard-summary'],queryFn:getDashboardSummary,retry:false,
  });
  const summary=summaryQuery.data;
  const value=key=>summary?String(summary[key]??0):'—';
  const metrics=[
    {label:'Completed purchases',value:value('completed_orders')},
    {label:'Active orders',value:value('active_orders')},
    {label:'Pending approval',value:value('pending_approvals')},
    {label:'Requests with results',value:value('requests_with_results')},
  ];

  return <div className="dashboard-page dashboard-refined">
    <header className="welcome-row">
      <div>
        <h1>{greeting}, {name}.</h1>
        <p className="dashboard-intro">Every purchasing decision has a record.</p>
      </div>
      <Link to="/procurement" className="button button-primary">
        <Plus size={17} aria-hidden="true"/> New procurement
      </Link>
    </header>

    <section className="section-heading" aria-label="Overview heading">
      <h2>Purchase overview</h2>
      <span className="period-label">All time</span>
    </section>
    <section className="metrics-grid" aria-label="Purchase metrics">
      {metrics.map(metric=><article className="metric-card" key={metric.label}>
        <span className="metric-label">{metric.label}</span>
        <strong className="metric-value">{metric.value}</strong>
      </article>)}
    </section>

    <section className="dashboard-columns" aria-label="Activity and system status">
      <article className="panel activity-panel">
        <div className="panel-heading">
          <h3>Recent activity</h3>
          <Link to="/activity" className="text-link">
            View all <ArrowRight size={14} aria-hidden="true"/>
          </Link>
        </div>
        {summaryQuery.isPending
          ? <div className="empty-state"><p>Loading activity…</p></div>
          : summaryQuery.isError
            ? <div className="empty-state"><strong>Activity unavailable</strong></div>
            : summary?.recent_activity?.length
              ? <ol className="dashboard-activity-list">
                {summary.recent_activity.map(event=><li key={event.id}>
                  <span>{event.action.replaceAll('.', ' · ').replaceAll('_',' ')}</span>
                  <time dateTime={event.created_at}>{new Date(event.created_at).toLocaleString()}</time>
                </li>)}
              </ol>
              : <div className="empty-state">
                <strong>No activity yet</strong>
                <p>Updates appear here as you work.</p>
              </div>
        }
      </article>
      <IntegrationStatusPanel health={health} integrations={integrations}/>
    </section>
  </div>;
}

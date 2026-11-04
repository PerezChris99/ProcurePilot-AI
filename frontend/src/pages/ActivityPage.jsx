import {useQuery} from '@tanstack/react-query';
import {Link} from 'react-router-dom';
import {Activity, ArrowRight, ClipboardList} from 'lucide-react';
import {getDashboardSummary} from '../services/api.js';

export default function ActivityPage(){
  const {data,isPending,isError,refetch}=useQuery({
    queryKey:['dashboard-summary'],queryFn:getDashboardSummary,
  });
  const events=data?.recent_activity||[];
  return <div className="form-page">
    <div className="page-title-block">
      <span className="eyebrow">WORKSPACE HISTORY</span>
      <h1>Recent activity</h1>
      <p>The eight latest saved purchasing events for your account. Full order-specific histories remain in Purchase orders.</p>
    </div>
    {isPending&&<div className="panel loading-panel" role="status">Loading activity…</div>}
    {isError&&<div className="panel error-panel" role="alert">
      <h2>Activity unavailable</h2>
      <p>Could not retrieve your activity. Your saved events have not been deleted.</p>
      <button type="button" className="button button-secondary" onClick={()=>refetch()}>Retry</button>
    </div>}
    {!isPending&&!isError&&<section className="panel">
      {events.length?<ol className="activity-event-list">
        {events.map(event=><li key={event.id}>
          <span className="activity-event-mark"><Activity size={17} aria-hidden="true"/></span>
          <span className="activity-event-copy">
            <strong>{event.action.replaceAll('.', ' · ').replaceAll('_',' ')}</strong>
            <time dateTime={event.created_at}>{new Date(event.created_at).toLocaleString()}</time>
          </span>
        </li>)}
      </ol>:<div className="empty-state">
        <Activity size={26} aria-hidden="true"/>
        <strong>No purchasing activity yet</strong>
        <p>Your recent purchase-order events will appear here once you start a request.</p>
      </div>}
    </section>}
    <Link className="text-link activity-continue" to="/orders">
      <ClipboardList size={16} aria-hidden="true"/> Open purchase-order audit trails <ArrowRight size={15} aria-hidden="true"/>
    </Link>
  </div>;
}

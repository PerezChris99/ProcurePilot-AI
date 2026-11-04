import {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {Link} from 'react-router-dom';
import {ArrowRight, PackageSearch, Plus, Search} from 'lucide-react';
import {apiRequest} from '../services/api.js';
import StatusBadge from '../components/ui/StatusBadge.jsx';

export default function DiscoveryPage(){
  const [filter,setFilter]=useState('');
  const {data,isPending,isError,refetch}=useQuery({
    queryKey:['procurement-requests'],
    queryFn:()=>apiRequest('/procurement-requests?limit=100'),
  });
  const requests=data||[];
  const found=requests.filter(req=>req.request_text.toLowerCase().includes(filter.trim().toLowerCase()));
  return <div className="form-page">
    <div className="page-title-block">
      <span className="eyebrow">PRODUCT DISCOVERY</span>
      <h1>Your procurement research</h1>
      <p>Continue saved catalogue searches, revisit ranked evidence or create a new request.</p>
    </div>
    <div className="discovery-toolbar">
      <label htmlFor="request-filter" className="discovery-filter">
        <Search size={18} aria-hidden="true"/>
        <span className="sr-only">Filter saved procurement requests</span>
        <input id="request-filter" value={filter} onChange={event=>setFilter(event.target.value)}
          placeholder="Search saved requests" type="search"/>
      </label>
      <Link className="button button-primary" to="/procurement"><Plus size={17} aria-hidden="true"/> New request</Link>
    </div>
    {isPending&&<div className="panel loading-panel" role="status">Loading saved requests…</div>}
    {isError&&<div className="panel error-panel" role="alert">
      <h2>Requests unavailable</h2>
      <p>Could not load your saved procurement requests.</p>
      <button type="button" className="button button-secondary" onClick={()=>refetch()}>Retry</button>
    </div>}
    {!isPending&&!isError&&(found.length?
      <div className="saved-requests">
        {found.map(req=><article className="saved-request" key={req.id}>
          <div className="saved-request-head">
            <span className="eyebrow">REQUEST · {req.currency}</span>
            <StatusBadge status={req.status}/>
          </div>
          <h2>{req.request_text}</h2>
          <p>Quantity {req.quantity} · {req.created_at?new Date(req.created_at).toLocaleDateString():'Saved request'}</p>
          <Link className="text-link" to={'/requests/'+req.id}>
            Open product discovery <ArrowRight size={16} aria-hidden="true"/>
          </Link>
        </article>)}
      </div>:
      <section className="panel discovery-empty">
        <PackageSearch size={30} aria-hidden="true"/>
        <h2>{requests.length?'No matching requests':'No saved requests yet'}</h2>
        <p>{requests.length?'Try a different search term.':'Start a procurement request to search real Channel3 products.'}</p>
        {!requests.length&&<Link to="/procurement" className="button button-primary">Create request <ArrowRight size={16}/></Link>}
      </section>)}
    <p className="discovery-disclaimer">Only the latest 100 saved requests are listed. Live catalogue results and AI assessments are available inside each request.</p>
  </div>;
}

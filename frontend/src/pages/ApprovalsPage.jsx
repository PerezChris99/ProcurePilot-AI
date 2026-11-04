import {useMutation,useQuery,useQueryClient} from '@tanstack/react-query';
import {Link} from 'react-router-dom';
import {Check,ClipboardCheck,ExternalLink,Plus,ShieldCheck,X} from 'lucide-react';
import {apiRequest} from '../services/api.js';
import StatusBadge from '../components/ui/StatusBadge.jsx';

function money(value,currency){
  try{return new Intl.NumberFormat(undefined,{style:'currency',currency}).format(Number(value))}
  catch{return String(value)+' '+currency}
}

export default function ApprovalsPage(){
  const queryClient=useQueryClient();
  const approvals=useQuery({
    queryKey:['purchase-orders','pending_approval'],
    queryFn:()=>apiRequest('/purchase-orders?status=pending_approval'),
  });
  const decide=useMutation({
    mutationFn:({id,decision})=>apiRequest('/purchase-orders/'+id+'/'+decision,{
      method:'POST',
      body:JSON.stringify({comment:decision==='reject'?'Declined during purchasing review':null}),
    }),
    onSuccess:async()=>{
      await Promise.all([
        queryClient.invalidateQueries({queryKey:['purchase-orders']}),
        queryClient.invalidateQueries({queryKey:['dashboard-summary']}),
      ]);
    },
  });
  const orders=approvals.data||[];
  return <div className="form-page orders-page">
    <div className="page-title-block">
      <span className="eyebrow">PURCHASE GOVERNANCE</span>
      <h1>Approvals</h1>
      <p>Review submitted purchase orders before they can enter PayPal Sandbox checkout.</p>
    </div>
    <div className="inline-notice approval-notice" role="note">
      <ShieldCheck size={17}/>
      <span><strong>Human-controlled approval.</strong> In this personal-workspace demo, the signed-in owner can approve their own order. Independent approver roles are not implemented.</span>
    </div>
    {decide.isError&&<p className="form-error" role="alert">{decide.error.message}</p>}
    {decide.isSuccess&&<p className="inline-notice" role="status">Decision recorded. The purchase-order status and audit trail have been updated.</p>}
    {approvals.isError&&<div className="panel error-panel" role="alert">
      <strong>Approval queue unavailable</strong>
      <p>{approvals.error.message}</p>
      <button type="button" className="button button-secondary" onClick={()=>approvals.refetch()}>Retry</button>
    </div>}
    {approvals.isPending&&<div className="panel loading-panel" role="status">Loading approvals…</div>}
    {approvals.isSuccess&&(orders.length?
      <div className="orders-list">{orders.map(order=><article className="order-card" key={order.id}>
        <div className="order-card-top">
          <div>
            <span className="eyebrow">{order.po_number}</span>
            <h2>{order.items?.[0]?.product_title||'Purchase order'}</h2>
            <p>{order.items?.[0]?.merchant||'Retailer not specified'} · Quantity {order.items?.[0]?.quantity||1}</p>
          </div>
          <StatusBadge status={order.status}/>
        </div>
        <div className="order-amount-row">
          <div><small>Amount requiring approval</small><strong>{money(order.total_amount,order.currency)}</strong></div>
          <div><small>Submitted</small><strong>{order.submitted_at?new Date(order.submitted_at).toLocaleDateString():'Pending'}</strong></div>
          {order.items?.[0]?.offer_url&&<a href={order.items[0].offer_url} target="_blank" rel="noopener noreferrer" className="text-link">Review retailer offer <ExternalLink size={14}/></a>}
        </div>
        <div className="order-actions">
          <button className="button button-primary" type="button" disabled={decide.isPending} onClick={()=>decide.mutate({id:order.id,decision:'approve'})}><Check size={16}/> Approve purchase</button>
          <button className="button button-danger" type="button" disabled={decide.isPending} onClick={()=>decide.mutate({id:order.id,decision:'reject'})}><X size={16}/> Reject</button>
        </div>
      </article>)}</div>:
      <section className="panel orders-empty">
        <span className="empty-icon"><ClipboardCheck size={27}/></span>
        <h2>Nothing awaiting approval</h2>
        <p>Submitted orders appear here automatically. Create a procurement request, choose an offer and submit its purchase order.</p>
        <Link to="/procurement" className="button button-primary"><Plus size={16}/> Start a procurement</Link>
      </section>
    )}
  </div>;
}

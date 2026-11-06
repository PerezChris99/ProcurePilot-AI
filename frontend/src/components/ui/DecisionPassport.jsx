import {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {Download,FileText,ShieldCheck} from 'lucide-react';
import {apiRequest,downloadAuthorizedFile} from '../../services/api.js';

function money(value,currency){
  if(value===null||value===undefined)return 'Not recorded';
  try{return new Intl.NumberFormat(undefined,{style:'currency',currency:currency||'USD'})
    .format(Number(value))}
  catch{return String(value)+' '+(currency||'')}
}
function evidenceAssessmentTitle(source){
  if(source==='gemini')return 'Gemini evidence assessment';
  if(source==='groq')return 'Groq evidence assessment';
  if(source==='openrouter')return 'OpenRouter evidence assessment';
  if(source==='catalogue_only')return 'Rule-based catalogue assessment (not AI)';
  if(source==='offline_example')return 'Offline example (not AI)';
  return 'Evidence assessment (source not verified)';
}
export default function DecisionPassport({orderId}){
  const [open,setOpen]=useState(false);
  const [downloadError,setDownloadError]=useState('');
  const report=useQuery({
    queryKey:['decision-passport',orderId],
    queryFn:()=>apiRequest('/purchase-orders/'+orderId+'/passport'),
    enabled:open,
    retry:false,
  });
  async function exportReport(extension){
    setDownloadError('');
    try{
      await downloadAuthorizedFile(
        '/purchase-orders/'+orderId+'/passport'+(extension==='pdf'?'.pdf':''),
        'ProcurePilot-Decision-Passport-'+orderId+'.'+extension,
      );
    }catch(error){
      setDownloadError(error.message);
    }
  }
  const data=report.data;
  const snapshot=data?.evidence||{};
  const proof=data?.payment_proof||{};
  const decision=data?.buyer_decision||{};
  const comparison=data?.comparison||{};
  const currentOffer=data?.offer_verification||{};
  return <section className="passport-section" aria-label="Procurement decision record">
    <button type="button" className="passport-toggle" aria-expanded={open}
      onClick={()=>setOpen(value=>!value)}>
      <FileText size={16} aria-hidden="true"/>
      {open?'Hide Decision Passport':'View Decision Passport'}
    </button>
    {open&&<>
      {report.isPending&&<p role="status" className="passport-help">Loading verified purchasing record…</p>}
      {report.isError&&<p role="alert" className="form-error">Decision Passport unavailable: {report.error.message} <button type="button" onClick={()=>report.refetch()}>Retry</button></p>}
      {data&&<div className="passport-paper">
        <div className="passport-head">
          <div><span className="eyebrow">ACCOUNTABLE PURCHASING</span><h3>Decision Passport</h3></div>
          <span className="passport-status"><ShieldCheck size={15}/> Saved evidence</span>
        </div>
        <p className="passport-help">A historical record, not a live inventory or delivery guarantee. PayPal Sandbox does not pay the retailer.</p>
        <dl className="passport-facts">
          <div><dt>Decision</dt><dd>{data.status}</dd></div>
          <div><dt>Catalogue captured</dt><dd>{snapshot.discovered_at?new Date(snapshot.discovered_at).toLocaleString():'Not recorded'}</dd></div>
          <div><dt>Selected offer</dt><dd>{snapshot.selected?.title||'Legacy order'}</dd></div>
          <div><dt>Selected total</dt><dd>{money(comparison.selected_total,snapshot.request?.currency)}</dd></div>
          <div><dt>Least-cost eligible</dt><dd>{money(comparison.least_cost_eligible_total,snapshot.request?.currency)}</dd></div>
          <div><dt>Price premium</dt><dd>{money(comparison.premium_vs_least_cost,snapshot.request?.currency)}</dd></div>
          <div><dt>Offers evaluated</dt><dd>{comparison.offers_evaluated_count??'Not recorded'}</dd></div>
          <div><dt>Rejected by policy</dt><dd>{comparison.policy_blocked_offer_count??'Not recorded'}</dd></div>
          <div><dt>Lowest rejected listing</dt><dd>{money(comparison.cheapest_rejected_total,snapshot.request?.currency)}</dd></div>
          <div><dt>Human approval</dt><dd>{decision.approved_at?'Recorded':'Pending'}</dd></div>
          <div><dt>Sandbox capture</dt><dd>{proof.capture_id||'Not captured'}</dd></div>
          <div><dt>Signed webhook</dt><dd>{proof.signed_webhook_correlated?'Correlated':'Not yet recorded'}</dd></div>
          <div><dt>Latest quote check</dt><dd>{currentOffer.status||'Not requested'}</dd></div>
        </dl>
        {comparison.cheapest_rejected_offer&&<p className="passport-help">
          The lowest priced rejected listing was <strong>{comparison.cheapest_rejected_offer.title||'Unnamed product'}</strong>
          {' '}({comparison.cheapest_rejected_offer.merchant||'Merchant unknown'}). It cannot be ordered:
          {' '}{(comparison.cheapest_rejected_offer.blocked_by||[]).join('; ')||'Purchasing policy not satisfied'}.
          This is a saved quotation comparison, not realized savings.
        </p>}
        <p className="passport-help">{comparison.note}</p>
        <h4>Why alternatives qualify or fail</h4>
        <div className="evidence-table-scroll"><table className="evidence-table">
          <thead><tr><th>Offer</th><th>Unit price</th><th>Evidence decision</th></tr></thead>
          <tbody>{(snapshot.compared_offers||[]).slice(0,8).map((row,index)=><tr key={row.product_id+'-'+index}>
            <td>{row.title} <small>{row.merchant}</small></td>
            <td>{money(row.unit_price,row.currency)}</td>
            <td>{row.eligible?'Eligible':(row.blocked_by||[]).join('; ')||'Not verified'}</td>
          </tr>)}</tbody>
        </table></div>
        {snapshot.ai?.explanation&&<div className="passport-analysis"><h4>{evidenceAssessmentTitle(snapshot.ai.source)}</h4><p>{snapshot.ai.explanation}</p></div>}
        <h4>Approval and payment events</h4>
        <ol className="passport-timeline">{(data.audit_timeline||[]).map((event,index)=><li key={event.action+'-'+index}>
          <span>{event.action.replaceAll('.', ' · ').replaceAll('_',' ')}</span>
          <time>{new Date(event.at).toLocaleString()}</time>
        </li>)}</ol>
        <p className="passport-help">Export checksum: {data.snapshot_sha256} — not an externally notarized record.</p>
        {downloadError&&<p role="alert" className="form-error">{downloadError}</p>}
        <div className="passport-downloads">
          <button className="button button-secondary" type="button" onClick={()=>exportReport('json')}><Download size={15}/> Export JSON</button>
          <button className="button button-secondary" type="button" onClick={()=>exportReport('pdf')}><Download size={15}/> Export PDF</button>
        </div>
      </div>}
    </>}
  </section>;
}

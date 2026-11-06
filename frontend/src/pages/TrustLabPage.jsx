import {useQuery} from '@tanstack/react-query';
import {ArrowLeft,RefreshCw,ShieldCheck,ShieldAlert} from 'lucide-react';
import {Link} from 'react-router-dom';
import {apiRequest} from '../services/api.js';

export default function TrustLabPage(){
  const check=useQuery({
    queryKey:['trust-lab-scenarios'],
    queryFn:()=>apiRequest('/trust-lab/scenarios'),
    retry:false,
    staleTime:0,
  });
  const data=check.data;
  const clean=data&&data.total===data.passed;
  return <div className="form-page trust-lab-page">
    <Link to="/dashboard" className="back-link"><ArrowLeft size={15}/> Back to overview</Link>
    <div className="page-title-block">
      <span className="eyebrow">EVIDENCE-BASED CONTROL DEMONSTRATION</span>
      <h1>Decision Trust Lab</h1>
      <p>Reproduce purchasing policy checks on synthetic offers. Each result is
        evaluated by the same server rule used to authorize real purchase orders.</p>
    </div>
    <section className="panel" aria-label="Policy lab summary">
      <div className="trust-lab-summary">
        <div>
          <span className="eyebrow">DETERMINISTIC SERVER VERIFICATION</span>
          <h2>{data?data.passed+' / '+data.total+' checks matched expectations':'Policy test run'}</h2>
          <p>Fixtures only · No Channel3, Gemini, or PayPal calls · No purchase orders.</p>
        </div>
        <button type="button" className="button button-primary"
          disabled={check.isFetching} onClick={()=>check.refetch()}>
          <RefreshCw size={15} className={check.isFetching?'spin':''}/>
          {check.isFetching?'Running…':'Run policy checks'}
        </button>
      </div>
      {data&&<p className="trust-lab-meta" role="status">
        {clean?<ShieldCheck size={16}/>:<ShieldAlert size={16}/>}
        {clean?'All configured scenarios matched policy expectations.':'One or more checks differed from expected policy results.'}
        {' '}Executed {new Date(data.executed_at).toLocaleString()}.
      </p>}
      {check.isError&&<p role="alert" className="form-error">
        Policy checks could not run: {check.error.message}
      </p>}
      {check.isPending&&<p role="status">Executing synthetic policy scenarios…</p>}
    </section>
    {data&&<section aria-label="Scenario results" className="trust-lab-results">
      {data.scenarios.map(scenario=><article className="panel trust-lab-case"
        key={scenario.id}>
        <div className="trust-lab-case-head">
          <div>
            <span className="eyebrow">POLICY CASE · {scenario.id.replaceAll('_',' ').toUpperCase()}</span>
            <h3>{scenario.name}</h3>
          </div>
          <strong className={scenario.passed?'trust-lab-success':'trust-lab-failure'}>
            {scenario.passed?'PASS':'FAIL'}
          </strong>
        </div>
        <p className="trust-lab-intent">Buyer request: {scenario.intent}</p>
        <p>{scenario.product_title} · {scenario.quantity} × {scenario.unit_price} {scenario.offer_currency}
          {' '}· Quoted total {scenario.quoted_total} {scenario.offer_currency}</p>
        <p>
          <strong>{scenario.allowed?'Offer allowed':'Offer blocked'}</strong>
          {' · '}Expected: {scenario.expected_allowed?'allow':'block'}
        </p>
        {scenario.violations.length>0&&<ul className="trust-lab-violations">
          {scenario.violations.map(reason=><li key={reason}>{reason}</li>)}
        </ul>}
        {!scenario.violations.length&&<p className="trust-lab-note">All current
          purchasing rules were satisfied for this labelled synthetic offer.</p>}
      </article>)}
    </section>}
    <p className="discovery-disclaimer">This read-only test verifies the production
      deterministic policy function against synthetic fixtures. It is not a live
      vendor result, real security penetration test, PayPal checkout, or claim
      that a provider is available. Payment and authorization protections are
      covered by separate API regression tests.</p>
  </div>;
}

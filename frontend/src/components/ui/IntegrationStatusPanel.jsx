import {Activity, Database, PackageSearch, RefreshCw, ShieldCheck, Sparkles, Wallet} from 'lucide-react';

function State({label,tone}){
  return <span className={'service-state '+tone}>{label}</span>;
}

function Row({icon:Icon,name,description,label,tone}){
  return <div className="service-row">
    <span className="service-icon"><Icon size={17} aria-hidden="true"/></span>
    <span><strong>{name}</strong><small>{description}</small></span>
    <State label={label} tone={tone}/>
  </div>;
}

function configurationState(query,configured,partial=false){
  if(query.isPending) return {label:'Checking',tone:'checking'};
  if(query.isError) return {label:'Unavailable',tone:'offline'};
  if(configured) return {label:'Configured',tone:'configured'};
  return partial?{label:'Incomplete',tone:'checking'}:{label:'Not configured',tone:'offline'};
}

export default function IntegrationStatusPanel({health,integrations}){
  const state=integrations.data;
  const ai=configurationState(integrations,state?.ai?.configured);
  const channel=configurationState(
    integrations,state?.channel3?.configured,
    state?.channel3?.api_key_set || state?.channel3?.base_url_configured,
  );
  const paypal=configurationState(
    integrations,state?.paypal?.credentials_configured,
    state?.paypal?.client_id_set || state?.paypal?.client_secret_set,
  );
  const webhook=configurationState(integrations,state?.paypal?.webhook_configured);
  const db=integrations.isPending?{label:'Checking',tone:'checking'}:
    integrations.isError?{label:'Unavailable',tone:'offline'}:
    !state?.database?.connected?{label:'Disconnected',tone:'offline'}:
    !state?.database?.schema_ready?{label:'Migration needed',tone:'checking'}:
    {label:'Ready',tone:'online'};
  const engine=state?.database?.engine==='postgresql'?'PostgreSQL':
    state?.database?.engine==='sqlite'?'SQLite':'Database';
  const mode=state?.paypal?.environment==='live'?'Live':
    state?.paypal?.environment==='sandbox'?'Sandbox':'Unspecified';
  const checking=integrations.isFetching || health.isFetching;
  const lastUpdated=integrations.dataUpdatedAt?
    new Date(integrations.dataUpdatedAt).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}):null;
  const refresh=()=>{void Promise.all([health.refetch(),integrations.refetch()]);};

  return <article className="panel readiness-panel" aria-label="System status">
    <div className="panel-heading">
      <div>
        <h3>System status</h3>
      </div>
      <button type="button" className="status-refresh button" aria-label="Refresh system status"
        onClick={refresh} disabled={checking}>
        <RefreshCw size={14} aria-hidden="true"/> Refresh
      </button>
    </div>
    <Row icon={Activity} name="ProcurePilot API" description="Process liveness"
      label={health.isSuccess?'Connected':health.isError?'Unavailable':'Checking'}
      tone={health.isSuccess?'online':health.isError?'offline':'checking'}/>
    <Row icon={Database} name={engine}
      description={state?.database?.connected?'Connection checked · schema '+(state?.database?.schema_ready?'ready':'not ready'):'Database connection'}
      {...db}/>
    <Row icon={Sparkles} name="Google Gemini"
      description={(state?.ai?.model||'Model not reported')+' · '+(state?.ai?.api_key_set?'Key set':'Key missing')}
      {...ai}/>
    <Row icon={PackageSearch} name="Channel3 catalogue"
      description={'API key '+(state?.channel3?.api_key_set?'set':'missing')+' · HTTPS URL '+(state?.channel3?.base_url_configured?'set':'missing')}
      {...channel}/>
    <Row icon={Wallet} name={'PayPal '+mode}
      description={'Client ID '+(state?.paypal?.client_id_set?'set':'missing')+' · secret '+(state?.paypal?.client_secret_set?'set':'missing')}
      {...paypal}/>
    <Row icon={ShieldCheck} name="PayPal webhook"
      description={state?.paypal?.webhook_configured?'Webhook ID set':'Webhook ID missing'}
      {...webhook}/>
    <p className="status-summary" role="note">
      <strong>{integrations.isError?'Could not check configuration.':'Configured means credentials are present, not verified.'}</strong>
      {lastUpdated&&!integrations.isError&&<span> · Checked {lastUpdated}</span>}
    </p>
  </article>;
}

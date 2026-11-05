import {useState} from 'react';
import {useMutation,useQueryClient} from '@tanstack/react-query';
import {useNavigate,Link} from 'react-router-dom';
import {ArrowLeft,ArrowRight,ShieldCheck} from 'lucide-react';
import {apiRequest} from '../services/api.js';

function attributePairs(text){
  const values={};
  for(const line of text.split('\n').map(value=>value.trim()).filter(Boolean)){
    const separator=line.indexOf('=');
    if(separator<1 || separator===line.length-1){
      throw new Error('Enter each specification as name=value, one per line.');
    }
    const key=line.slice(0,separator).trim();
    const value=line.slice(separator+1).trim();
    if(!/^[a-zA-Z0-9_ -]{1,48}$/.test(key)||value.length<1||value.length>100){
      throw new Error('Specification names and values must be short and plain text.');
    }
    values[key]=value;
  }
  if(Object.keys(values).length>8){
    throw new Error('Add at most eight specifications to each list.');
  }
  return values;
}

export default function ProcurementPage(){
  const queryClient=useQueryClient();
  const navigate=useNavigate();
  const [request,setRequest]=useState('');
  const [budget,setBudget]=useState('');
  const [quantity,setQuantity]=useState('1');
  const [currency,setCurrency]=useState('USD');
  const [showPolicy,setShowPolicy]=useState(false);
  const [mandatory,setMandatory]=useState('');
  const [preferred,setPreferred]=useState('');
  const [merchants,setMerchants]=useState('');
  const [unitPriceCap,setUnitPriceCap]=useState('');
  const [expiresAt,setExpiresAt]=useState('');
  const [validation,setValidation]=useState('');

  const createRequest=useMutation({
    mutationFn:payload=>apiRequest('/procurement-requests',{
      method:'POST',body:JSON.stringify(payload),
    }),
    onSuccess:data=>{
      queryClient.invalidateQueries({queryKey:['procurement-requests']});
      navigate('/requests/'+data.id);
    },
  });

  function handleSubmit(event){
    event.preventDefault();
    setValidation('');
    try{
      const domains=merchants.split(',').map(value=>value.trim().toLowerCase()).filter(Boolean);
      if(domains.length>12)throw new Error('Use at most twelve approved merchant domains.');
      const policy={
        mandatory_attributes:attributePairs(mandatory),
        preferred_attributes:attributePairs(preferred),
        allowed_merchants:domains,
      };
      if(unitPriceCap)policy.max_unit_price=unitPriceCap;
      if(expiresAt){
        const expiry=new Date(expiresAt);
        if(Number.isNaN(expiry.getTime())||expiry<=new Date()){
          throw new Error('Select a future expiry date and time.');
        }
        policy.expires_at=expiry.toISOString();
      }
      createRequest.mutate({
        request_text:request.trim(),
        quantity:Number(quantity),
        budget:budget||null,
        currency,
        policy_json:policy,
      });
    }catch(error){
      setValidation(error.message);
    }
  }

  return <div className="form-page">
    <Link to="/dashboard" className="back-link"><ArrowLeft size={15}/> Back to overview</Link>
    <div className="page-title-block">
      <span className="eyebrow">PURCHASING WORKSPACE</span>
      <h1>What does your business need?</h1>
      <p>Describe the purchase. We will compare actual catalogue evidence against your requirements before any approval or payment.</p>
    </div>
    <form className="request-card" onSubmit={handleSubmit}>
      <div className="form-section-title">
        <span className="form-step">01</span>
        <div><h2>Purchase request</h2><p>Define what qualifies. Your decision remains in human hands.</p></div>
      </div>
      <label className="field-label" htmlFor="request">What are you looking to purchase?</label>
      <textarea id="request" rows="5" value={request} onChange={event=>setRequest(event.target.value)}
        placeholder="Example: Two 27-inch IPS office monitors with HDMI connectivity." required minLength={12} maxLength={5000}/>
      <div className="form-grid three-fields">
        <div>
          <label className="field-label" htmlFor="quantity">Quantity</label>
          <input id="quantity" type="number" min="1" max="100000" step="1" value={quantity}
            onChange={event=>setQuantity(event.target.value)} required/>
        </div>
        <div>
          <label className="field-label" htmlFor="budget">Maximum total budget <span className="optional-label">OPTIONAL</span></label>
          <input id="budget" type="number" min="0.01" step="0.01" value={budget}
            onChange={event=>setBudget(event.target.value)} placeholder="500"/>
        </div>
        <div>
          <label className="field-label" htmlFor="currency">Currency</label>
          <select id="currency" value={currency} onChange={event=>setCurrency(event.target.value)}>
            <option value="USD">USD — US Dollar</option>
            <option value="EUR">EUR — Euro</option>
            <option value="GBP">GBP — Pound Sterling</option>
          </select>
        </div>
      </div>

      <details className="mandate-options" open={showPolicy} onToggle={event=>setShowPolicy(event.currentTarget.open)}>
        <summary><ShieldCheck size={17} aria-hidden="true"/> Buyer mandate <span>Optional, enforced before ordering</span></summary>
        <p className="mandate-help">Only catalogue evidence that exactly matches your mandatory specifications can qualify. Do not enter specifications the catalogue cannot verify.</p>
        <div className="mandate-grid">
          <div>
            <label className="field-label" htmlFor="mandatory">Required specifications</label>
            <textarea id="mandatory" rows="3" value={mandatory} onChange={event=>setMandatory(event.target.value)}
              placeholder={"screen_size=27 inch\npanel_type=IPS"} aria-describedby="mandatory-help"/>
            <small id="mandatory-help">One name=value per line, up to eight.</small>
          </div>
          <div>
            <label className="field-label" htmlFor="preferred">Preferred specifications</label>
            <textarea id="preferred" rows="3" value={preferred} onChange={event=>setPreferred(event.target.value)}
              placeholder="color=black"/>
            <small>Preferences affect ranking, not hard eligibility.</small>
          </div>
          <div>
            <label className="field-label" htmlFor="merchants">Approved merchant domains</label>
            <input id="merchants" value={merchants} onChange={event=>setMerchants(event.target.value)}
              placeholder="retailer.example, shop.example"/>
            <small>Comma-separated domain names only. Empty permits any HTTPS retailer.</small>
          </div>
          <div>
            <label className="field-label" htmlFor="unit-cap">Maximum price per item</label>
            <input id="unit-cap" type="number" min="0.01" step="0.01" value={unitPriceCap}
              onChange={event=>setUnitPriceCap(event.target.value)} placeholder="200"/>
          </div>
          <div>
            <label className="field-label" htmlFor="expires">Mandate expires</label>
            <input id="expires" type="datetime-local" value={expiresAt}
              onChange={event=>setExpiresAt(event.target.value)}/>
          </div>
        </div>
      </details>
      {validation&&<p className="form-error" role="alert">{validation}</p>}
      {createRequest.isError&&<p className="form-error" role="alert">{createRequest.error.message}</p>}
      <div className="form-actions">
        <span className="secure-note"><ShieldCheck size={16}/> Policy checks and human approval before Sandbox payment</span>
        <button className="button button-primary" type="submit"
          disabled={request.trim().length<12||Number(quantity)<1||createRequest.isPending}>
          {createRequest.isPending?'Saving request…':<>Save and discover products <ArrowRight size={16}/></>}
        </button>
      </div>
    </form>
    <p className="discovery-disclaimer">No order or payment is created by saving a request. Catalogue data may be incomplete. PayPal Sandbox does not pay external retailers.</p>
  </div>;
}

import {useEffect,useState} from 'react';
import {Link} from 'react-router-dom';
import {
  ArrowLeft,ArrowRight,ArrowUpRight,ChevronDown,ClipboardCheck,
  Pause,Play,SearchCheck,ShieldCheck,Sparkles,
} from 'lucide-react';
import {useAuth} from '../context/useAuth.js';

const photography=[
  {
    src:'https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?auto=format&fit=crop&w=1460&q=78',
    alt:'An organized warehouse with shelves of parcels and inventory.',
    title:'Less uncertainty in sourcing',
    detail:'Know what the catalogue actually shows.',
    eyebrow:'THE SOURCING PROBLEM',
  },
  {
    src:'https://images.unsplash.com/photo-1557804506-669a67965ba0?auto=format&fit=crop&w=1460&q=78',
    alt:'Professionals discussing plans and working from laptops in an office.',
    title:'Decisions people can stand behind',
    detail:'Review evidence before anyone approves.',
    eyebrow:'THE HUMAN DECISION',
  },
  {
    src:'https://images.unsplash.com/photo-1497366811353-6870744d04b2?auto=format&fit=crop&w=1460&q=78',
    alt:'A sunlit modern office meeting space behind glass walls.',
    title:'One clearer purchasing workspace',
    detail:'From initial request to an auditable trail.',
    eyebrow:'THE BETTER WORKFLOW',
  },
];

const faqs=[
  {
    question:'Does the AI place orders automatically?',
    answer:'No. Gemini helps explain catalogue evidence. The app enforces purchasing rules, and a signed-in person must approve each order before a payment flow begins.',
  },
  {
    question:'Where do prices and products come from?',
    answer:'From Channel3 catalogue responses, not invented AI listings. You can inspect the saved offer evidence before creating a purchase order.',
  },
  {
    question:'Is PayPal processing real purchases?',
    answer:'This prototype uses PayPal Sandbox only. Its simulated payment flow does not purchase goods from a Channel3 retailer or transfer live money.',
  },
  {
    question:'Can I try it without external API keys?',
    answer:'You can create an account and explore the local workspace. Live catalogue search, AI analysis, and Sandbox checkout need the relevant configured credentials.',
  },
];

function HeroSlideshow(){
  const [active,setActive]=useState(0);
  const [paused,setPaused]=useState(false);
  const [motionReduced,setMotionReduced]=useState(false);
  useEffect(()=>{
    if(typeof window.matchMedia!=='function')return;
    const media=window.matchMedia('(prefers-reduced-motion: reduce)');
    setMotionReduced(media.matches);
    const changed=event=>setMotionReduced(event.matches);
    media.addEventListener?.('change',changed);
    return ()=>media.removeEventListener?.('change',changed);
  },[]);
  useEffect(()=>{
    if(paused||motionReduced)return;
    const timer=window.setInterval(()=>setActive(index=>(index+1)%photography.length),7000);
    return ()=>window.clearInterval(timer);
  },[paused,motionReduced]);
  const change=amount=>setActive(index=>(index+amount+photography.length)%photography.length);
  return <section
    className="site-hero-visual"
    aria-roledescription="carousel"
    aria-label="Procurement photography"
    onMouseEnter={()=>setPaused(true)}
    onMouseLeave={()=>setPaused(false)}
    onFocusCapture={()=>setPaused(true)}
    onBlurCapture={event=>{if(!event.currentTarget.contains(event.relatedTarget))setPaused(false);}}
  >
    <div className="site-hero-images" aria-live="off">
      {photography.map((photo,index)=><img
        key={photo.src}
        src={photo.src}
        alt={index===active?photo.alt:''}
        className={'site-hero-image'+(index===active?' is-visible':'')}
        aria-hidden={index!==active}
        width="1000"
        height="800"
        loading={index===0?'eager':'lazy'}
        decoding="async"
        fetchPriority={index===0?'high':'auto'}
      />)}
    </div>
    <div className="site-hero-mist" aria-hidden="true"/>
    <div className="site-hero-topline">
      <span>PROCUREMENT / REIMAGINED</span>
      <span>01 — 03</span>
    </div>
    <div className="site-hero-caption" aria-live={paused?'polite':'off'}>
      <div>
        <span className="site-photo-eyebrow">{photography[active].eyebrow}</span>
        <h2>{photography[active].title}</h2>
        <p>{photography[active].detail}</p>
      </div>
      <span className="site-image-index">0{active+1}/0{photography.length}</span>
    </div>
    <div className="site-slide-controls">
      <div className="site-slide-dots" aria-label="Choose hero image">
        {photography.map((photo,index)=><button
          key={photo.src}
          type="button"
          aria-label={'Show slide '+(index+1)+': '+photo.title}
          aria-current={active===index?'true':undefined}
          className={'site-slide-dot'+(active===index?' is-active':'')}
          onClick={()=>setActive(index)}
        />)}
      </div>
      <div className="site-slide-arrows">
        <button type="button" aria-label="Previous image" onClick={()=>change(-1)}><ArrowLeft size={17}/></button>
        <button type="button" aria-label={paused?'Play slideshow':'Pause slideshow'} onClick={()=>setPaused(value=>!value)}>
          {paused?<Play size={15}/>:<Pause size={15}/>}
        </button>
        <button type="button" aria-label="Next image" onClick={()=>change(1)}><ArrowRight size={17}/></button>
      </div>
    </div>
  </section>;
}

function Point({index,title,copy}){
  return <article className="site-process-step">
    <span className="site-step-number">{index}</span>
    <h3>{title}</h3>
    <p>{copy}</p>
  </article>;
}

export default function LandingPage(){
  const {user}=useAuth();
  return <>
    <section className="site-hero site-container" aria-labelledby="landing-headline">
      <div className="site-hero-text">
        <span className="site-kicker"><span className="site-kicker-line"/> INTELLIGENT PROCUREMENT · HUMAN CONTROL</span>
        <h1 id="landing-headline">Purchase with <em>clarity.</em><br/>Not guesswork.</h1>
        <p>From a business need to a confident decision. Discover real product offers, compare the evidence, and approve every purchase on your terms.</p>
        <div className="site-hero-actions">
          <Link className="site-button site-button-dark" to={user?'/dashboard':'/register'}>
            {user?'Go to workspace':'Explore ProcurePilot'} <ArrowRight size={18} aria-hidden="true"/>
          </Link>
          <Link className="site-text-action" to="/#how">
            See how it works <ArrowUpRight size={17} aria-hidden="true"/>
          </Link>
        </div>
        <div className="site-trust-note"><ShieldCheck size={16} aria-hidden="true"/> Evidence-led AI. Human approvals. Sandbox payments.</div>
      </div>
      <HeroSlideshow/>
    </section>

    <section className="site-evidence-strip" aria-label="Technology foundation">
      <div className="site-container site-evidence-inner">
        <span className="site-evidence-title">BUILT WITH ACTUAL INTEGRATIONS</span>
        <div className="site-evidence-names">
          <span>Google Gemini <small>via ADK</small></span>
          <span>Channel3 <small>catalogue</small></span>
          <span>PayPal <small>Sandbox</small></span>
          <span>PostgreSQL <small>data</small></span>
        </div>
      </div>
    </section>

    <section className="site-container site-story-grid" id="why" aria-label="Problem and solution">
      <div className="site-story-left">
        <span className="site-section-index">01 / THE PROBLEM</span>
        <h2>Purchasing gets messy<br/>before anything is bought.</h2>
        <p>Scattered products, unclear pricing, decisions in chat threads, and no reliable approval history.</p>
        <div className="site-story-rule"><span>LESS SEARCHING.</span><span>MORE CERTAINTY.</span></div>
      </div>
      <div className="site-story-right">
        <span className="site-section-index">02 / OUR APPROACH</span>
        <h2>One connected path<br/>from need to approval.</h2>
        <div className="site-benefit-list">
          <div><SearchCheck size={20}/><span><strong>Evidence before opinions.</strong> Compare offers sourced from the catalogue.</span></div>
          <div><Sparkles size={20}/><span><strong>AI that explains.</strong> Short assessments based on available evidence.</span></div>
          <div><ClipboardCheck size={20}/><span><strong>People stay in control.</strong> Save the decision and its audit trail.</span></div>
        </div>
      </div>
    </section>

    <section className="site-process-wrap" id="how">
      <div className="site-container">
        <div className="site-section-header">
          <div><span className="site-section-index">03 / THE WORKFLOW</span><h2>Three steps. One clearer decision.</h2></div>
          <Link to="/how-it-works" className="site-text-action">View the full process <ArrowUpRight size={16}/></Link>
        </div>
        <div className="site-process-grid">
          <Point index="01" title="Describe the need" copy="Tell us what you're buying, how many, and your budget."/>
          <Point index="02" title="Review the evidence" copy="Compare real catalogue offers and a bounded AI assessment."/>
          <Point index="03" title="Approve with confidence" copy="Confirm the saved order, then try the PayPal Sandbox flow."/>
        </div>
      </div>
    </section>

    <section className="site-container site-faq-block" id="faq">
      <div className="site-faq-intro">
        <span className="site-section-index">04 / GOOD TO KNOW</span>
        <h2>The essentials,<br/>answered.</h2>
        <p>Clear boundaries, without the sales pitch.</p>
        <Link className="site-text-action" to="/responsible-use">Our operating principles <ArrowUpRight size={15}/></Link>
      </div>
      <div className="site-faq-grid">
        {faqs.map((item,index)=><details key={item.question} className="site-faq-item">
          <summary><span>{String(index+1).padStart(2,'0')}</span>{item.question}<ChevronDown size={16} aria-hidden="true"/></summary>
          <p>{item.answer}</p>
        </details>)}
      </div>
    </section>

    <section className="site-container site-final-cta" aria-label="Get started">
      <div><span className="site-section-index">YOUR NEXT PURCHASE, SIMPLIFIED</span>
        <h2>Good decisions start here.</h2>
        <p>See the workflow. Keep the final call.</p>
      </div>
      <Link to={user?'/dashboard':'/register'} className="site-button site-button-light">
        {user?'Open your workspace':'Start your workspace'} <ArrowRight size={17} aria-hidden="true"/>
      </Link>
    </section>
  </>;
}

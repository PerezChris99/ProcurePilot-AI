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
    answer:'No. AI explains catalogue evidence. A signed-in person must approve each order before payment.',
  },
  {
    question:'Where do prices and products come from?',
    answer:'Channel3 catalogue results, not AI-invented listings. Review saved offers before placing an order.',
  },
  {
    question:'Is PayPal processing real purchases?',
    answer:'PayPal Sandbox only. No live money moves and no supplier purchase is made.',
  },
  {
    question:'Can I try it without external API keys?',
    answer:'Yes. Explore the local workspace without keys. Search, AI and Sandbox checkout need credentials.',
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
        width="1600"
        height="800"
        loading="eager"
        decoding="async"
        fetchPriority={index===0?'high':'low'}
      />)}
    </div>
    <div className="site-hero-mist" aria-hidden="true"/>
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
        <span className="site-kicker">A BETTER WAY TO BUY FOR WORK</span>
        <h1 id="landing-headline">Purchase with <em>clarity.</em><br/>Not guesswork.</h1>
        <p>Compare real offers, review AI insights, and approve orders in one place.</p>
        <div className="site-hero-actions">
          <Link className="site-button site-button-dark" to={user?'/dashboard':'/register'}>
            {user?'Go to workspace':'Explore ProcurePilot'} <ArrowRight size={18} aria-hidden="true"/>
          </Link>
          <Link className="site-text-action" to="/#how">
            See how it works <ArrowUpRight size={17} aria-hidden="true"/>
          </Link>
        </div>
        <div className="site-trust-note"><ShieldCheck size={16} aria-hidden="true"/> AI insights · Human approvals · Sandbox payments.</div>
      </div>
      <HeroSlideshow/>
    </section>

    <section className="site-evidence-strip" aria-label="Technology foundation">
      <div className="site-container site-evidence-inner">
        <span className="site-evidence-title">INTEGRATIONS</span>
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
        <span className="site-section-index">THE CHALLENGE</span>
        <h2>Buying for work gets complicated.</h2>
        <p>Scattered offers. Unclear costs. Decisions without a trail.</p>
      </div>
      <div className="site-story-right">
        <span className="site-section-index">THE SOLUTION</span>
        <h2>One clear buying workflow.</h2>
        <div className="site-benefit-list">
          <div><SearchCheck size={20}/><span><strong>Catalogue evidence.</strong> See offers and prices.</span></div>
          <div><Sparkles size={20}/><span><strong>Useful AI guidance.</strong> Compare the options.</span></div>
          <div><ClipboardCheck size={20}/><span><strong>Human approval.</strong> Keep a record of every decision.</span></div>
        </div>
      </div>
    </section>

    <section className="site-process-wrap" id="how">
      <div className="site-container">
        <div className="site-section-header">
          <div><span className="site-section-index">HOW IT WORKS</span><h2>From request to approval.</h2></div>
          <Link to="/how-it-works" className="site-text-action">View the full process <ArrowUpRight size={16}/></Link>
        </div>
        <div className="site-process-grid">
          <Point index="01" title="Describe the need" copy="Enter the item, quantity, and budget."/>
          <Point index="02" title="Compare the offers" copy="Review catalogue results and AI analysis."/>
          <Point index="03" title="Approve the order" copy="Confirm the order and test PayPal Sandbox."/>
        </div>
      </div>
    </section>

    <section className="site-container site-faq-block" id="faq">
      <div className="site-faq-intro">
        <span className="site-section-index">COMMON QUESTIONS</span>
        <h2>Common questions.</h2>
      </div>
      <div className="site-faq-grid">
        {faqs.map((item,index)=><details key={item.question} className="site-faq-item">
          <summary><span>{String(index+1).padStart(2,'0')}</span>{item.question}<ChevronDown size={16} aria-hidden="true"/></summary>
          <p>{item.answer}</p>
        </details>)}
      </div>
    </section>

    <section className="site-container site-final-cta" aria-label="Get started">
      <div><span className="site-section-index">GET STARTED</span>
        <h2>Buy with clarity.</h2>
      </div>
      <Link to={user?'/dashboard':'/register'} className="site-button site-button-light">
        {user?'Open your workspace':'Start your workspace'} <ArrowRight size={17} aria-hidden="true"/>
      </Link>
    </section>
  </>;
}

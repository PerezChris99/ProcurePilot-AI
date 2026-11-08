import {useEffect} from 'react';
import {Link,Outlet,useLocation} from 'react-router-dom';
import {ArrowRight,ExternalLink} from 'lucide-react';
import {useAuth} from '../../context/useAuth.js';
import MobileDock from './MobileDock.jsx';

const siteLinks=[
  {name:'About',to:'/about'},
  {name:'How it works',to:'/how-it-works'},
  {name:'FAQ',to:'/#faq'},
];
const legalLinks=[
  {name:'Privacy',to:'/privacy'},
  {name:'Terms',to:'/terms'},
  {name:'Security',to:'/security'},
  {name:'Accessibility',to:'/accessibility'},
  {name:'Responsible use',to:'/responsible-use'},
  {name:'Contact',to:'/contact'},
];

export function PublicFooter(){
  return <footer className="site-footer">
    <div className="site-footer-top">
      <div className="site-footer-intro">
        <Link to="/" className="site-footer-brand" aria-label="ProcurePilot AI home">
          <img src="/favicon.svg" alt="" width="31" height="31"/>
          <span>procurepilot<span className="site-footer-brand-dot">.</span></span>
        </Link>
        <p>Procurement with clarity.</p>
      </div>
      <nav aria-label="Platform pages" className="site-footer-links">
        <strong>Explore</strong>
        {siteLinks.map(link=><Link key={link.to} to={link.to}>{link.name}</Link>)}
        <Link to="/dashboard">Workspace</Link>
      </nav>
      <nav aria-label="Legal and support pages" className="site-footer-links">
        <strong>Legal & support</strong>
        {legalLinks.map(link=><Link key={link.to} to={link.to}>{link.name}</Link>)}
      </nav>
      <div className="site-footer-brief">
        <p>Prototype. External services require configured credentials.</p>
        <a href="https://github.com/PerezChris99/ProcurePilot-AI" target="_blank" rel="noopener noreferrer">Project on GitHub <ExternalLink size={13} aria-hidden="true"/></a>
        <a href="https://github.com/PerezChris99/ProcurePilot-AI/blob/main/docs/JUDGES_START_HERE.md" target="_blank" rel="noopener noreferrer">Judge walkthrough <ExternalLink size={13} aria-hidden="true"/></a>
        <a href="https://unsplash.com/license" target="_blank" rel="noopener noreferrer">Photography: Unsplash <ExternalLink size={13} aria-hidden="true"/></a>
        <p className="site-footer-credit">Developed by <a href="https://kweeziperez.com" target="_blank" rel="noopener noreferrer">Kweezi Perez Christopher <ExternalLink size={13} aria-hidden="true"/></a></p>
      </div>
    </div>
    <div className="site-footer-bottom">
      <span>© 2026 ProcurePilot AI. Code and branding rights reserved.</span>
      <span>Independent prototype · PayPal Sandbox is not supplier settlement</span>
    </div>
  </footer>;
}

export default function PublicLayout(){
  const {user}=useAuth();
  const location=useLocation();
  const scrollHomeToTop=()=>{
    const reduced=window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    window.scrollTo({top:0,behavior:reduced?'auto':'smooth'});
  };
  useEffect(()=>{
    if(location.hash){
      let id=location.hash.slice(1);
      try{id=decodeURIComponent(id)}catch{ /* Ignore malformed URL escapes. */ }
      const reduced=window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
      document.getElementById(id)?.scrollIntoView({behavior:reduced?'auto':'smooth',block:'start'});
    }else{
      document.documentElement.scrollTop=0;
      document.body.scrollTop=0;
    }
  },[location.pathname,location.hash]);
  return <div className="site-shell">
    <a href="#site-main" className="site-skip-link">Skip to content</a>
    <header className="site-header">
      <div className="site-header-inner">
        <Link to="/" className="site-brand" aria-label="ProcurePilot AI home" onClick={scrollHomeToTop}>
          <img src="/favicon.svg" alt="" width="34" height="34"/>
          <span>procurepilot<span className="site-brand-period">.</span></span>
        </Link>
        <nav className="site-nav" aria-label="Website navigation">
          {siteLinks.map(link=><Link to={link.to} key={link.to}>{link.name}</Link>)}
        </nav>
        <div className="site-header-actions">
          {!user&&<Link to="/login" className="site-signin">Sign in</Link>}
          <Link to={user?'/dashboard':'/register'} className="site-top-cta">
            {user?'Open workspace':'Get started'} <ArrowRight size={15} aria-hidden="true"/>
          </Link>
        </div>
      </div>
    </header>
    <main id="site-main" className="site-main"><Outlet/></main>
    <PublicFooter/>
    <MobileDock/>
  </div>;
}

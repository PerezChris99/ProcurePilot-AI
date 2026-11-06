import {useEffect} from 'react';
import {useLocation} from 'react-router-dom';

const BASE='ProcurePilot AI';
const PUBLIC={
  '/': ['Purchase with clarity. Not guesswork.','From a business need to an evidence-based, human-approved purchase. Discover real catalogue offers with ProcurePilot AI.'],
  '/about': ['About','Why we built an evidence-first procurement workflow that keeps people in control.'],
  '/how-it-works': ['How it works','A simple path from purchasing requirements to catalogue evidence and human-approved decisions.'],
  '/privacy': ['Privacy','How the ProcurePilot AI prototype handles account, procurement and Sandbox information.'],
  '/terms': ['Terms of use','Responsible evaluation terms for the ProcurePilot AI hackathon prototype.'],
  '/security': ['Security','Implemented protections and transparent production security limitations.'],
  '/accessibility': ['Accessibility','Accessible navigation, responsive layouts and the current testing boundaries.'],
  '/responsible-use': ['Responsible use','What the AI can and cannot do, and why humans retain purchasing authority.'],
  '/contact': ['Contact','How to contact the ProcurePilot AI project maintainer and find help.'],
  '/login': ['Sign in','Sign in to your private procurement workspace.'],
  '/register': ['Create workspace','Create a workspace and start a procurement request.'],
  '/dashboard': ['Overview','Your authenticated procurement dashboard and integration configuration.'],
  '/trust-lab': ['Decision Trust Lab','Read-only execution of deterministic purchasing safeguards against labelled synthetic fixtures.'],
  '/procurement': ['New procurement','Describe a purchasing request and review real catalogue evidence.'],
  '/orders': ['Purchase orders','Review approvals, PayPal Sandbox status and order audit history.'],
  '/approvals': ['Approvals','Review pending purchasing decisions with explicit human approval.'],
  '/activity': ['Activity','Review recorded purchasing activity.'],
  '/discovery': ['Product discovery','Revisit saved catalogue research and procurement requests.'],
};

export default function PageMetadata(){
  const {pathname}=useLocation();
  useEffect(()=>{
    const [label,description]=PUBLIC[pathname]||
      (pathname.startsWith('/requests/')?
        ['Product discovery','Review saved purchasing evidence and qualifying offers.']:
        ['Page not found','Explore the ProcurePilot AI website.']);
    document.title=pathname==='/'?BASE+' — '+label:label+' — '+BASE;
    const meta=document.querySelector('meta[name="description"]');
    if(meta)meta.setAttribute('content',description);
    const ogTitle=document.querySelector('meta[property="og:title"]');
    if(ogTitle)ogTitle.setAttribute('content',document.title);
    const ogDescription=document.querySelector('meta[property="og:description"]');
    if(ogDescription)ogDescription.setAttribute('content',description);
  },[pathname]);
  return null;
}

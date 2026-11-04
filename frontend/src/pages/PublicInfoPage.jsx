import {Link} from 'react-router-dom';
import {ArrowRight,ExternalLink,ShieldCheck} from 'lucide-react';

const PAGES={
  about:{
    eyebrow:'THE PURPOSE',title:'A better way to buy for work.',
    intro:'ProcurePilot AI turns an informal purchasing need into a documented, evidence-based decision—without giving an AI system the authority to spend money.',
    accent:'Clarity first. Human control always.',
    sections:[
      {title:'Why it exists',copy:'Purchasing teams lose time switching between product listings, spreadsheets, messaging threads and approval chains. Important context gets lost before the order is even placed.'},
      {title:'What we built',copy:'A connected workflow for describing requirements, searching real catalogue offers, comparing the evidence, drafting purchase orders and recording decisions.'},
      {title:'How the intelligence works',copy:'Deterministic backend rules check the actual offer. Google Gemini, orchestrated by ADK, supplies a concise evidence-grounded explanation—not invented stock, prices or purchases.'},
      {title:'Where we are today',copy:'This is a working hackathon prototype with a PayPal Sandbox demonstration. It is not a live retailer checkout or an independently certified enterprise procurement product.'},
    ],
    action:{label:'Understand the workflow',to:'/how-it-works'},
  },
  'how-it-works':{
    eyebrow:'THE WORKFLOW',title:'From request to review, without the noise.',
    intro:'A short, traceable purchasing path that keeps people responsible for the final decision.',
    accent:'The assistant explains. Your team decides.',
    sections:[
      {title:'01 / Describe',copy:'Create a business purchasing request with the intended use, quantity, currency and optional budget. The request belongs to your signed-in workspace.'},
      {title:'02 / Discover',copy:'Channel3 returns catalogue data; the backend evaluates available offers, eligibility, prices and constraints. Unknown attributes are treated as unknown, not invented.'},
      {title:'03 / Assess',copy:'When configured, Gemini reviews a short evidence packet and gives a bounded explanation. The same assessment can be cached to conserve API usage.'},
      {title:'04 / Approve',copy:'Choose a qualifying saved offer to create a purchase order. Submit it for explicit human approval and retain an audit trail. The personal demo permits self-approval.'},
      {title:'05 / Sandbox checkout',copy:'An approved purchase order can enter PayPal Sandbox. The app checks the buyer-approved PayPal order and capture before marking the demo payment complete.'},
      {title:'06 / Revisit',copy:'Use the Activity, Discovery and Purchase orders screens to revisit saved evidence and decisions. A Sandbox payment does not buy from the Channel3 retailer.'},
    ],
    action:{label:'Explore the workspace',to:'/register'},
  },
  privacy:{
    eyebrow:'LEGAL / PRIVACY',title:'Privacy, in plain language.',
    intro:'The prototype uses information to run accounts and purchasing workflows. This notice describes the current implementation; review it with counsel before a commercial launch.',
    accent:'Last reviewed 4 November 2026 · Prototype notice',
    sections:[
      {title:'Information recorded',copy:'Account name and email, securely hashed password, purchasing requests, budgets, selected offers, decisions, audit history and PayPal Sandbox transaction identifiers or status. Passwords are not stored in plain text.'},
      {title:'Session and local storage',copy:'The browser keeps the short-lived access token in sessionStorage for the current tab session. This app has no first-party advertising or analytics-cookie integration in its current source. PayPal and external providers may operate under their own notices.'},
      {title:'Service providers',copy:'Product search requests may be sent to Channel3. Compact procurement evidence may be submitted to Google Gemini through ADK. Sandbox transaction details are shared with PayPal as part of the checkout flow. The public landing page fetches illustrative photos from the Unsplash image CDN, so the browser may contact that provider. Each external service operates under its own privacy terms.'},
      {title:'Storage and retention',copy:'Workspace data persist in the configured application database. The prototype does not yet include an automated deletion schedule, a self-service export, or a self-service account deletion flow. Data handling before public launch needs an operational retention and deletion policy.'},
      {title:'Security and access',copy:'The API uses authenticated user-scoped resources, Argon2id password hashing and server-side secrets. No website can promise absolute security; see the Security page for important limits.'},
      {title:'Questions and requests',copy:'Use the Contact page to reach the project maintainer about data practices or a deletion request. Requests are handled manually and are not yet automated in the application.'},
    ],
    action:{label:'Security posture',to:'/security'},
  },
  terms:{
    eyebrow:'LEGAL / TERMS',title:'Terms of use.',
    intro:'These terms describe appropriate evaluation of the ProcurePilot AI prototype. They are a project notice, not a replacement for jurisdiction-specific legal review.',
    accent:'Last reviewed 4 November 2026 · Prototype terms',
    sections:[
      {title:'Scope of the service',copy:'ProcurePilot AI is a hackathon demonstration for procurement research, human approval and simulated PayPal Sandbox transactions. It is provided for evaluation and authorized testing.'},
      {title:'Your responsibilities',copy:'Use your own authorized account, protect login credentials, verify offers and make purchasing decisions independently. Do not submit unlawful requests, exploit the service, or attempt unauthorized access.'},
      {title:'AI and product information',copy:'AI assessments may be incomplete or incorrect. Catalogue information, stock, prices and merchant details may change. Do not treat model output as a promise of availability, delivery, quality or legal compliance.'},
      {title:'Payments and third parties',copy:'The included checkout uses PayPal Sandbox, not live merchant settlement. Any real retailer purchase is separate. Google, Channel3 and PayPal each have their own conditions and service availability.'},
      {title:'Ownership and permissions',copy:'Source code and branding remain proprietary and subject to the repository LICENSE. Hackathon evaluator access does not grant a general right to reuse or redistribute the code.'},
      {title:'Availability and liability',copy:'This evaluation prototype is provided without a guaranteed uptime, support response time, or fitness for commercial procurement. Validate legal terms and liability limitations with qualified counsel before a public launch.'},
    ],
    action:{label:'Responsible use',to:'/responsible-use'},
  },
  security:{
    eyebrow:'TRUST / SECURITY',title:'Controls before claims.',
    intro:'We distinguish protections implemented in code from capabilities not yet independently validated in production.',
    accent:'Security information is not a certification.',
    sections:[
      {title:'Account and data controls',copy:'Passwords are hashed with Argon2id. Access uses short-lived JWT bearer tokens. Backend endpoints scope purchasing data to the authenticated user and avoid returning provider secrets.'},
      {title:'Buying safeguards',copy:'Product offers, amounts and currency are validated against saved catalogue evidence. Orders require recorded human approval before Sandbox checkout. AI cannot independently approve or pay.'},
      {title:'Provider and webhook checks',copy:'PayPal capture details are verified server-side; webhook events require PayPal verification and are deduplicated. The status panel shows configuration, not a passed live provider connectivity test.'},
      {title:'Remaining hardening',copy:'The prototype does not yet claim independent enterprise approver roles, full distributed rate limiting, device-session revocation, complete payment race reconciliation or independently tested disaster recovery.'},
      {title:'Security reports',copy:'Avoid publishing active exploit details in a public issue. Use GitHub repository owner contact or private vulnerability reporting if available; see the project security documentation for technical boundaries.'},
    ],
    action:{label:'Contact the project',to:'/contact'},
  },
  accessibility:{
    eyebrow:'TRUST / ACCESSIBILITY',title:'Designed for more ways to work.',
    intro:'The interface is built for phones, tablets and desktops, with simple navigation and semantic interaction patterns.',
    accent:'Accessibility is a practice, not a badge.',
    sections:[
      {title:'Navigation',copy:'The application uses labeled links, buttons and form fields. On narrow screens the authenticated sidebar becomes a bottom dock; the same six destinations remain available.'},
      {title:'Reading and motion',copy:'Responsive typography, visible keyboard focus and reduced-motion preferences are supported. The landing photo carousel includes manual controls and a pause action.'},
      {title:'Content and errors',copy:'Forms identify required information, and API failures are presented in text. Status indicators use words alongside their colors to avoid a purely color-dependent meaning.'},
      {title:'Known limitations',copy:'The application has not been independently certified for WCAG conformance or tested with every assistive technology, browser or device. Please report obstacles to the maintainer.'},
    ],
    action:{label:'Contact the project',to:'/contact'},
  },
  'responsible-use':{
    eyebrow:'PRODUCT / RESPONSIBLE USE',title:'Automation with a clear boundary.',
    intro:'ProcurePilot supports better purchasing judgment. It does not delegate financial authority to an AI model.',
    accent:'Evidence is required. People approve.',
    sections:[
      {title:'AI assists; it does not authorize',copy:'Gemini produces a short procurement assessment based on allowed evidence. The backend enforces offer validity and the user explicitly submits and approves the purchase order.'},
      {title:'Unverified means unknown',copy:'Delivery suitability, warranties, stock and pricing are not guaranteed by model prose. Buyers must inspect the actual retailer offer and confirm suitability directly.'},
      {title:'Sandbox is not settlement',copy:'PayPal Sandbox tests merchant/buyer approval and capture logic. It does not pay Channel3 retailers or create real fulfillment obligations.'},
      {title:'Prototype governance limits',copy:'The current personal workspace allows the requester to approve their own order. Independent procurement role separation and other production policies would be required for a larger organization.'},
    ],
    action:{label:'How it works',to:'/how-it-works'},
  },
  contact:{
    eyebrow:'SUPPORT / CONTACT',title:'A direct line to the project.',
    intro:'Questions about the prototype, judge access, a bug, data use or a responsible security report? Start with the maintainer’s GitHub project.',
    accent:'Clear conversations. No automated support promises.',
    sections:[
      {title:'Project and issues',copy:'For setup questions or ordinary bugs, use the ProcurePilot AI GitHub repository and its issue tracker if available. Include your OS, the command you ran and a redacted error log.'},
      {title:'Privacy and security',copy:'For personal information requests or vulnerabilities, contact the project owner privately through a suitable channel. Do not expose API keys, JWTs or private security details in public issues.'},
      {title:'Hackathon access',copy:'The README includes one-command Windows, macOS and Linux setup guides. API keys from Google, Channel3 and PayPal remain controlled by the evaluator or project operator.'},
    ],
    action:{label:'Back to ProcurePilot',to:'/'},
  },
};
const allLinks=[
  {name:'About',to:'/about'},{name:'How it works',to:'/how-it-works'},
  {name:'Privacy',to:'/privacy'},{name:'Terms',to:'/terms'},
  {name:'Security',to:'/security'},{name:'Accessibility',to:'/accessibility'},
  {name:'Responsible use',to:'/responsible-use'},{name:'Contact',to:'/contact'},
];

export default function PublicInfoPage({kind}){
  const page=PAGES[kind];
  if(!page)return null;
  return <div className="site-info site-container">
    <nav aria-label="Breadcrumb" className="site-info-crumb">
      <Link to="/">Home</Link><span>/</span><span>{kind==='how-it-works'?'How it works':kind.replaceAll('-',' ')}</span>
    </nav>
    <header className="site-info-head">
      <div><span className="site-section-index">{page.eyebrow}</span>
        <h1>{page.title}</h1>
        <p>{page.intro}</p>
      </div>
      <aside className="site-info-side"><ShieldCheck size={22} aria-hidden="true"/>
        <strong>{page.accent}</strong>
      </aside>
    </header>
    <div className="site-info-body">
      <nav className="site-info-sidebar" aria-label="More information">
        <strong>MORE INFORMATION</strong>
        {allLinks.map(link=><Link key={link.to} to={link.to}
          aria-current={'/'+kind===link.to?'page':undefined}
          className={'site-info-nav-link'+('/'+kind===link.to?' is-selected':'')}
        >{link.name}</Link>)}
      </nav>
      <div className="site-info-cards">
        {page.sections.map((section,index)=><section key={section.title} className="site-info-card">
          <span className="site-info-count">{String(index+1).padStart(2,'0')}</span>
          <h2>{section.title}</h2>
          <p>{section.copy}</p>
        </section>)}
        {kind==='contact'&&<div className="site-contact-links">
          <a href="https://github.com/PerezChris99/ProcurePilot-AI" target="_blank" rel="noopener noreferrer">
            Open the project repository <ExternalLink size={16} aria-hidden="true"/>
          </a>
          <a href="https://github.com/PerezChris99" target="_blank" rel="noopener noreferrer">
            Repository owner <ExternalLink size={16} aria-hidden="true"/>
          </a>
        </div>}
      </div>
    </div>
    <aside className="site-info-next">
      <span>KEEP EXPLORING</span>
      <Link to={page.action.to}>{page.action.label} <ArrowRight size={17} aria-hidden="true"/></Link>
    </aside>
  </div>;
}

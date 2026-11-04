import {
  Activity,BookOpenText,ClipboardList,CircleHelp,House,
  LayoutDashboard,ListChecks,Plus,Search,ShieldCheck,UserRound,
} from 'lucide-react';

// Every workspace destination is defined once for both sidebar and mobile dock.
export const workspaceNavigation=[
  {label:'Overview',short:'Home',to:'/dashboard',icon:LayoutDashboard,group:'workspace'},
  {label:'New procurement',short:'New',to:'/procurement',icon:Plus,group:'workspace'},
  {label:'Purchase orders',short:'Orders',to:'/orders',icon:ClipboardList,group:'workspace'},
  {label:'Approvals',short:'Approve',to:'/approvals',icon:ShieldCheck,group:'workspace'},
  {label:'Activity',short:'Activity',to:'/activity',icon:Activity,group:'manage'},
  {label:'Product discovery',short:'Discover',to:'/discovery',icon:Search,group:'manage'},
];

// Public navigation is useful before authentication; it never suggests that
// private orders, approvals or activity are anonymous visitor destinations.
export function publicNavigation(signedIn){
  return [
    {label:'Home',short:'Home',to:'/',icon:House},
    {label:'The problem',short:'Why',to:'/#why',icon:Search},
    {label:'How it works',short:'How',to:'/#how',icon:ListChecks},
    {label:'Frequently asked questions',short:'FAQ',to:'/#faq',icon:CircleHelp},
    {label:'About ProcurePilot',short:'About',to:'/about',icon:BookOpenText},
    signedIn
      ?{label:'Open workspace',short:'App',to:'/dashboard',icon:LayoutDashboard}
      :{label:'Sign in',short:'Account',to:'/login',icon:UserRound},
  ];
}

export function isNavigationActive(pathname,hash,to){
  if(to==='/discovery' && pathname.startsWith('/requests/'))return true;
  const index=to.indexOf('#');
  if(index!==-1){
    return pathname===to.slice(0,index)&&hash===to.slice(index);
  }
  if(to==='/' && pathname==='/' && hash)return false;
  return pathname===to;
}

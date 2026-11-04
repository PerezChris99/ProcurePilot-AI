import {
  Activity,BookOpenText,ClipboardList,CircleHelp,House,
  LayoutDashboard,ListChecks,Plus,Search,ShieldCheck,UserRound,
} from 'lucide-react';

// Every workspace destination is defined once for both sidebar and mobile dock.
export const workspaceNavigation=[
  {label:'Overview',short:'Home',to:'/dashboard',icon:LayoutDashboard,iosIcon:'dashboard',group:'workspace'},
  {label:'New procurement',short:'New',to:'/procurement',icon:Plus,iosIcon:'new',group:'workspace'},
  {label:'Purchase orders',short:'Orders',to:'/orders',icon:ClipboardList,iosIcon:'orders',group:'workspace'},
  {label:'Approvals',short:'Approve',to:'/approvals',icon:ShieldCheck,iosIcon:'approve',group:'workspace'},
  {label:'Activity',short:'Activity',to:'/activity',icon:Activity,iosIcon:'activity',group:'manage'},
  {label:'Product discovery',short:'Discover',to:'/discovery',icon:Search,iosIcon:'search',group:'manage'},
];

// Public navigation is useful before authentication; it never suggests that
// private orders, approvals or activity are anonymous visitor destinations.
export function publicNavigation(signedIn){
  return [
    {label:'Home',short:'Home',to:'/',icon:House,iosIcon:'home'},
    {label:'The problem',short:'Why',to:'/#why',icon:Search,iosIcon:'search'},
    {label:'How it works',short:'How',to:'/#how',icon:ListChecks,iosIcon:'how'},
    {label:'Frequently asked questions',short:'FAQ',to:'/#faq',icon:CircleHelp,iosIcon:'faq'},
    {label:'About ProcurePilot',short:'About',to:'/about',icon:BookOpenText,iosIcon:'about'},
    signedIn
      ?{label:'Open workspace',short:'App',to:'/dashboard',icon:LayoutDashboard,iosIcon:'dashboard'}
      :{label:'Sign in',short:'Account',to:'/login',icon:UserRound,iosIcon:'account'},
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

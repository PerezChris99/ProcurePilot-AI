import {Link,useLocation} from 'react-router-dom';
import {useAuth} from '../../context/useAuth.js';
import {isNavigationActive,publicNavigation,workspaceNavigation} from './navigation.js';

/**
 * One bottom dock across the public website, sign-in, and the authenticated
 * workspace. CSS hides it only at desktop widths (>=961px).
 */
export default function MobileDock({variant='public'}){
  const {user}=useAuth();
  const {pathname,hash}=useLocation();
  const workspace=variant==='workspace';
  const items=workspace?workspaceNavigation:publicNavigation(Boolean(user));
  return <nav className={'mobile-dock'+(workspace?' mobile-dock-workspace':' mobile-dock-public')}
    aria-label={workspace?'Mobile workspace navigation':'Mobile website navigation'}>
    {items.map(({label,short,to,icon:Icon})=>{
      const active=isNavigationActive(pathname,hash,to);
      return <Link key={to} to={to} aria-label={label}
        aria-current={active?'page':undefined}
        className={'mobile-dock-link'+(active?' active':'')}>
        <Icon size={19} strokeWidth={1.9} aria-hidden="true"/>
        <span>{short}</span>
      </Link>;
    })}
  </nav>;
}

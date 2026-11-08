import {lazy,Suspense} from 'react';
import {Route,Routes} from 'react-router-dom';
import PageMetadata from './components/routing/PageMetadata.jsx';
import PublicLayout from './components/layout/PublicLayout.jsx';
import RequireAuth from './components/routing/RequireAuth.jsx';
import AsyncProgress from './components/ui/AsyncProgress.jsx';
import LoginPage from './pages/LoginPage.jsx';
import RegisterPage from './pages/RegisterPage.jsx';

// Keep sign-in and registration in the first bundle. Load unrelated pages
// on demand so judges do not download charts, catalogue and payment code
// before they can enter their account credentials.
const LandingPage=lazy(()=>import('./pages/LandingPage.jsx'));
const PublicInfoPage=lazy(()=>import('./pages/PublicInfoPage.jsx'));
const NotFoundPage=lazy(()=>import('./pages/NotFoundPage.jsx'));
const AppShell=lazy(()=>import('./components/layout/AppShell.jsx'));
const DashboardPage=lazy(()=>import('./pages/DashboardPage.jsx'));
const TrustLabPage=lazy(()=>import('./pages/TrustLabPage.jsx'));
const ProcurementPage=lazy(()=>import('./pages/ProcurementPage.jsx'));
const OrdersPage=lazy(()=>import('./pages/OrdersPage.jsx'));
const ApprovalsPage=lazy(()=>import('./pages/ApprovalsPage.jsx'));
const ActivityPage=lazy(()=>import('./pages/ActivityPage.jsx'));
const DiscoveryPage=lazy(()=>import('./pages/DiscoveryPage.jsx'));
const RequestDetailPage=lazy(()=>import('./pages/RequestDetailPage.jsx'));

const publicPages=[
  'about','how-it-works','privacy','terms',
  'security','accessibility','responsible-use','contact',
];
function RouteFallback(){
  return <div className="route-loading">
    <AsyncProgress compact label="Opening page…"/>
  </div>;
}
export default function App(){
  return <><PageMetadata/><Suspense fallback={<RouteFallback/>}><Routes>
    <Route element={<PublicLayout/>}>
      <Route path="/" element={<LandingPage/>}/>
      {publicPages.map(kind=><Route key={kind} path={'/'+kind} element={<PublicInfoPage kind={kind}/>}/>)}
      <Route path="*" element={<NotFoundPage/>}/>
    </Route>
    <Route path="/login" element={<LoginPage/>}/>
    <Route path="/register" element={<RegisterPage/>}/>
    <Route element={<RequireAuth/>}>
      <Route element={<AppShell/>}>
        <Route path="/dashboard" element={<DashboardPage/>}/>
        <Route path="/trust-lab" element={<TrustLabPage/>}/>
        <Route path="/procurement" element={<ProcurementPage/>}/>
        <Route path="/orders" element={<OrdersPage/>}/>
        <Route path="/approvals" element={<ApprovalsPage/>}/>
        <Route path="/activity" element={<ActivityPage/>}/>
        <Route path="/discovery" element={<DiscoveryPage/>}/>
        <Route path="/requests/:requestId" element={<RequestDetailPage/>}/>
      </Route>
    </Route>
  </Routes></Suspense></>;
}

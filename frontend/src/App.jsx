import {Route,Routes} from 'react-router-dom';
import PublicLayout from './components/layout/PublicLayout.jsx';
import LandingPage from './pages/LandingPage.jsx';
import PublicInfoPage from './pages/PublicInfoPage.jsx';
import AppShell from './components/layout/AppShell.jsx';
import RequireAuth from './components/routing/RequireAuth.jsx';
import DashboardPage from './pages/DashboardPage.jsx';
import ProcurementPage from './pages/ProcurementPage.jsx';
import OrdersPage from './pages/OrdersPage.jsx';
import ApprovalsPage from './pages/ApprovalsPage.jsx';
import ActivityPage from './pages/ActivityPage.jsx';
import DiscoveryPage from './pages/DiscoveryPage.jsx';
import RequestDetailPage from './pages/RequestDetailPage.jsx';
import LoginPage from './pages/LoginPage.jsx';
import RegisterPage from './pages/RegisterPage.jsx';
import NotFoundPage from './pages/NotFoundPage.jsx';

const publicPages=[
  'about','how-it-works','privacy','terms',
  'security','accessibility','responsible-use','contact',
];
export default function App(){
  return <Routes>
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
        <Route path="/procurement" element={<ProcurementPage/>}/>
        <Route path="/orders" element={<OrdersPage/>}/>
        <Route path="/approvals" element={<ApprovalsPage/>}/>
        <Route path="/activity" element={<ActivityPage/>}/>
        <Route path="/discovery" element={<DiscoveryPage/>}/>
        <Route path="/requests/:requestId" element={<RequestDetailPage/>}/>
      </Route>
    </Route>
  </Routes>;
}

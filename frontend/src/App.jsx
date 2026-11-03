import {Navigate,Route,Routes} from 'react-router-dom';
import AppShell from './components/layout/AppShell.jsx';
import RequireAuth from './components/routing/RequireAuth.jsx';
import DashboardPage from './pages/DashboardPage.jsx';
import ProcurementPage from './pages/ProcurementPage.jsx';
import OrdersPage from './pages/OrdersPage.jsx';
import NotFoundPage from './pages/NotFoundPage.jsx';
import LoginPage from './pages/LoginPage.jsx';
import RegisterPage from './pages/RegisterPage.jsx';
import RequestDetailPage from './pages/RequestDetailPage.jsx';
export default function App(){return <Routes><Route path="/login" element={<LoginPage/>}/><Route path="/register" element={<RegisterPage/>}/><Route element={<RequireAuth/>}><Route element={<AppShell/>}><Route index element={<DashboardPage/>}/><Route path="procurement" element={<ProcurementPage/>}/><Route path="orders" element={<OrdersPage/>}/><Route path="approvals" element={<Navigate to="/orders?status=pending_approval" replace/>}/><Route path="requests/:requestId" element={<RequestDetailPage/>}/><Route path="*" element={<NotFoundPage/>}/></Route></Route></Routes>}

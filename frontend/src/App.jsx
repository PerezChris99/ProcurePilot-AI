import { Navigate, Route, Routes } from 'react-router-dom';
import AppShell from './components/layout/AppShell.jsx';
import DashboardPage from './pages/DashboardPage.jsx';
import ProcurementPage from './pages/ProcurementPage.jsx';
import OrdersPage from './pages/OrdersPage.jsx';
import NotFoundPage from './pages/NotFoundPage.jsx';
export default function App(){return <Routes><Route element={<AppShell/>}><Route index element={<DashboardPage/>}/><Route path="procurement" element={<ProcurementPage/>}/><Route path="orders" element={<OrdersPage/>}/><Route path="approvals" element={<Navigate to="/orders?status=pending_approval" replace/>}/><Route path="*" element={<NotFoundPage/>}/></Route></Routes>}

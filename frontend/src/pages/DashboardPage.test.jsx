import {describe,expect,it,vi} from 'vitest';
import {render,screen} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {MemoryRouter} from 'react-router-dom';
import DashboardPage from './DashboardPage.jsx';
vi.mock('../services/api.js',()=>({
 getHealth:vi.fn().mockResolvedValue({status:'ok'}),
 getIntegrationStatus:vi.fn().mockResolvedValue({
  database:{connected:true},
  ai:{provider:'Google Gemini',configured:true,model:'gemini-3.8-flash'},
  channel3:{provider:'Channel3',configured:true},
  paypal:{provider:'PayPal',credentials_configured:true,webhook_configured:false,environment:'sandbox'}
 })
}));
function renderPage(){const client=new QueryClient({defaultOptions:{queries:{retry:false}}});return render(<QueryClientProvider client={client}><MemoryRouter><DashboardPage/></MemoryRouter></QueryClientProvider>)}
describe('DashboardPage',()=>{
 it('renders the procurement overview and primary action',()=>{
  renderPage();
  expect(screen.getByRole('heading',{name:/let's buy smarter/i})).toBeInTheDocument();
  expect(screen.getByRole('link',{name:/new procurement/i})).toBeInTheDocument();
  expect(screen.getByText(/no activity yet/i)).toBeInTheDocument();
 });
 it('shows live provider configuration rather than hard-coded not configured labels',async()=>{
  renderPage();
  expect(await screen.findByText('Google Gemini')).toBeInTheDocument();
  expect(screen.getAllByText('Connected').length).toBeGreaterThan(1);
  expect(screen.getByText('Webhook pending')).toBeInTheDocument();
 });
});

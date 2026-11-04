import {describe,expect,it,vi} from 'vitest';
import {render,screen,waitFor,within} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {MemoryRouter} from 'react-router-dom';
import DashboardPage from './DashboardPage.jsx';
vi.mock('../context/useAuth.js',()=>({useAuth:()=>({user:{full_name:'Amina Kombe'}})}));
vi.mock('../services/api.js',()=>({
 getHealth:vi.fn().mockResolvedValue({status:'ok'}),
 getDashboardSummary:vi.fn().mockResolvedValue({completed_orders:2,active_orders:3,pending_approvals:1,requests_with_results:4,recent_activity:[{id:'event-1',action:'purchase_order.created',created_at:'2026-11-04T12:00:00Z'}]}),
 getIntegrationStatus:vi.fn().mockResolvedValue({
  database:{connected:true,schema_ready:true,engine:'postgresql'},
  ai:{provider:'Google Gemini',configured:true,api_key_set:true,model:'gemini-3.8-flash'},
  channel3:{provider:'Channel3',configured:true,api_key_set:true,base_url_configured:true},
  paypal:{provider:'PayPal',credentials_configured:true,client_id_set:true,client_secret_set:true,webhook_configured:false,environment:'sandbox'}
 })
}));
function renderPage(){const client=new QueryClient({defaultOptions:{queries:{retry:false}}});return render(<QueryClientProvider client={client}><MemoryRouter><DashboardPage/></MemoryRouter></QueryClientProvider>)}
describe('DashboardPage',()=>{
 it('renders the procurement overview and primary action',()=>{
  renderPage();
  expect(screen.getByRole('heading',{name:/good (morning|afternoon|evening), amina/i})).toBeInTheDocument();
  expect(screen.getByRole('heading',{name:/let's buy smarter/i})).toBeInTheDocument();
  expect(screen.getByRole('link',{name:/new procurement/i})).toBeInTheDocument();
 });
 it('shows live provider configuration rather than hard-coded not configured labels',async()=>{
  renderPage();
  expect(await screen.findByText('Google Gemini')).toBeInTheDocument();
  expect(screen.getByText('PayPal Sandbox')).toBeInTheDocument();
  expect((await screen.findAllByText('Configured')).length).toBe(3);
  expect(screen.getByText('Webhook ID missing')).toBeInTheDocument();
  expect(screen.getByText('PayPal webhook')).toBeInTheDocument();
  expect(screen.getByText(/configured means credentials are present, not verified/i)).toBeInTheDocument();
 });
});

describe('Live overview',()=>{
 it('renders real overview counts and recent activity',async()=>{
  renderPage();
  const completed=await screen.findByText('Completed purchases');
  const active=screen.getByText('Active purchase orders');
  const requests=screen.getByText('Requests with results');
  // Labels render synchronously; totals arrive after the React Query promise settles.
  await waitFor(()=>{
   expect(within(completed.closest('article')).getByText('2')).toBeInTheDocument();
   expect(within(active.closest('article')).getByText('3')).toBeInTheDocument();
   expect(within(requests.closest('article')).getByText('4')).toBeInTheDocument();
  });
  expect(await screen.findByText('purchase order · created')).toBeInTheDocument();
 });
});

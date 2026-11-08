import {describe,expect,it,vi} from 'vitest';
import {render,screen,waitFor,within,fireEvent} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {MemoryRouter} from 'react-router-dom';
import DashboardPage from './DashboardPage.jsx';
import {getHealth,getIntegrationStatus} from '../services/api.js';
vi.mock('../context/useAuth.js',()=>({useAuth:()=>({user:{full_name:'Amina Kombe'}})}));
vi.mock('../services/api.js',()=>({
 getHealth:vi.fn().mockResolvedValue({status:'ok'}),
 getDashboardSummary:vi.fn().mockResolvedValue({completed_orders:2,active_orders:3,pending_approvals:1,requests_with_results:4,recent_activity:[{id:'event-1',action:'purchase_order.created',created_at:'2026-11-04T12:00:00Z'}]}),
 getIntegrationStatus:vi.fn().mockResolvedValue({
  database:{connected:true,schema_ready:true,engine:'postgresql'},
  ai:{provider:'Google ADK / LiteLLM',configured:true,api_key_set:true,model:'gemini-3.5-flash-lite',fallback_enabled:true,backup_providers:{groq:true,openrouter:true}},
  channel3:{provider:'Channel3',configured:true,api_key_set:true,base_url_configured:true},
  paypal:{provider:'PayPal',credentials_configured:true,client_id_set:true,client_secret_set:true,webhook_configured:false,environment:'sandbox'}
 })
}));
function renderPage(){const client=new QueryClient({defaultOptions:{queries:{retry:false}}});return render(<QueryClientProvider client={client}><MemoryRouter><DashboardPage/></MemoryRouter></QueryClientProvider>)}
describe('DashboardPage',()=>{
 it('renders the procurement overview and primary action',()=>{
  renderPage();
  expect(screen.getByRole('heading',{name:/good (morning|afternoon|evening), amina/i})).toBeInTheDocument();
  expect(screen.getByRole('heading',{name:'Purchase overview'})).toBeInTheDocument();
  expect(screen.queryByText(/let's buy smarter/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/YOUR AI PROCUREMENT COPILOT/i)).not.toBeInTheDocument();
  expect(screen.getByRole('link',{name:/new procurement/i})).toBeInTheDocument();
  expect(screen.getByRole('link',{name:/open decision trust lab/i})).toHaveAttribute('href','/trust-lab');
 });
 it('shows live provider configuration rather than hard-coded not configured labels',async()=>{
  renderPage();
  // Dashboard renders the actual ADK and LiteLLM provider configuration.
  // Provider names render before React Query resolves, but the PayPal
  // environment and credential states come from the asynchronous API response.
  await waitFor(()=>{
   expect(screen.getByText('AI models · Google ADK')).toBeInTheDocument();
   expect(screen.getByText(/Primary: gemini-3.5-flash-lite/)).toBeInTheDocument();
   expect(screen.getByText(/Groq ready, OpenRouter ready/)).toBeInTheDocument();
   expect(screen.getByText('PayPal Sandbox')).toBeInTheDocument();
   expect(screen.getAllByText('Configured')).toHaveLength(3);
   expect(screen.getByText('Webhook ID missing')).toBeInTheDocument();
   expect(screen.getByText('PayPal webhook')).toBeInTheDocument();
   expect(screen.getByText(/configured means credentials are present, not verified/i)).toBeInTheDocument();
  });
 });
});

describe('Live overview',()=>{
 it('renders real overview counts and recent activity',async()=>{
  renderPage();
  const completed=await screen.findByText('Completed purchases');
  const active=screen.getByText('Active orders');
  const requests=screen.getByText('Requests with results');
  expect(screen.getByText('Pending approval')).toBeInTheDocument();
  // Labels render synchronously; totals arrive after the React Query promise settles.
  await waitFor(()=>{
   expect(within(completed.closest('article')).getByText('2')).toBeInTheDocument();
   expect(within(active.closest('article')).getByText('3')).toBeInTheDocument();
   expect(within(requests.closest('article')).getByText('4')).toBeInTheDocument();
  });
  expect(await screen.findByText('purchase order · created')).toBeInTheDocument();
 });
});


describe('Hosted system status refresh',()=>{
 it('forces new API calls, updates webhook ID status, and leaves purchase metrics untouched',async()=>{
  renderPage();
  expect(await screen.findByText('Webhook ID missing')).toBeInTheDocument();
  getHealth.mockResolvedValueOnce({status:'ok'});
  getIntegrationStatus.mockResolvedValueOnce({
    database:{connected:true,schema_ready:true,engine:'postgresql'},
    ai:{configured:true,api_key_set:true,model:'gemini-3.5-flash-lite',
      backup_providers:{groq:true,openrouter:true}},
    channel3:{configured:true,api_key_set:true,base_url_configured:true},
    paypal:{
      environment:'sandbox',credentials_configured:true,
      client_id_set:true,client_secret_set:true,
      webhook_configured:true,webhook_id_valid:true,
      webhook_id_hint:'••••771C',webhook_url_configured:true,
      webhook_last_verified_at:null,merchant_checkout_verified:false,
    },
  });
  fireEvent.click(screen.getByRole('button',{name:'Refresh system status'}));
  await waitFor(()=>{
    expect(getHealth).toHaveBeenCalledWith({force:true});
    expect(getIntegrationStatus).toHaveBeenCalledWith({force:true});
    expect(screen.getByText(/Webhook ID ••••771C/)).toBeInTheDocument();
  });
  expect(screen.getByText(/Status updated just now/)).toBeInTheDocument();
  expect(screen.getByText('Completed purchases')).toBeInTheDocument();
 });
});

import {beforeEach,describe,expect,it,vi} from 'vitest';
import {fireEvent,render,screen,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {MemoryRouter} from 'react-router-dom';
import ApprovalsPage from './ApprovalsPage.jsx';
import {apiRequest} from '../services/api.js';

vi.mock('../services/api.js',()=>({apiRequest:vi.fn()}));

function renderPage(){
  const queryClient=new QueryClient({defaultOptions:{queries:{retry:false}}});
  return render(<QueryClientProvider client={queryClient}><MemoryRouter><ApprovalsPage/></MemoryRouter></QueryClientProvider>);
}

const order={
  id:'po-123',po_number:'PP-20261104-ABC123',status:'pending_approval',
  total_amount:'250.00',currency:'USD',submitted_at:'2026-11-04T11:00:00Z',
  items:[{product_title:'Office monitor',merchant:'Verified retailer',quantity:2,offer_url:'https://retailer.example/monitor'}],
};

describe('ApprovalsPage',()=>{
  beforeEach(()=>apiRequest.mockReset());

  it('shows a helpful empty state for a newly registered user',async()=>{
    apiRequest.mockResolvedValue([]);
    renderPage();
    expect(await screen.findByText('Nothing awaiting approval')).toBeInTheDocument();
    expect(screen.getByRole('link',{name:/start a procurement/i})).toHaveAttribute('href','/procurement');
    expect(apiRequest).toHaveBeenCalledWith('/purchase-orders?status=pending_approval');
  });

  it('allows the authenticated demo user to review and approve a queued order',async()=>{
    apiRequest.mockResolvedValueOnce([order]).mockResolvedValueOnce({...order,status:'approved'}).mockResolvedValue([]);
    renderPage();
    expect(await screen.findByRole('heading',{name:'Office monitor'})).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button',{name:/approve purchase/i}));
    await waitFor(()=>expect(apiRequest).toHaveBeenCalledWith('/purchase-orders/po-123/approve',{
      method:'POST',body:JSON.stringify({comment:null}),
    }));
  });

  it('states the demo self-approval boundary explicitly',async()=>{
    apiRequest.mockResolvedValue([]);
    renderPage();
    expect(await screen.findByText(/can assign another registered user/i)).toBeInTheDocument();
  });
});

describe('Independent approver access',()=>{
  beforeEach(()=>apiRequest.mockReset());
  it('does not permit the requester to approve a delegated order',async()=>{
    apiRequest.mockResolvedValue([{...order,assigned_approver_id:'other-account',can_approve:false}]);
    renderPage();
    expect(await screen.findByText('Awaiting the assigned independent reviewer.')).toBeInTheDocument();
    expect(screen.queryByRole('button',{name:/approve purchase/i})).not.toBeInTheDocument();
  });
});

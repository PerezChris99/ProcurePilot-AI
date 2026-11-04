import {beforeEach,describe,expect,it,vi} from 'vitest';
import {fireEvent,render,screen,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {MemoryRouter} from 'react-router-dom';
import OrdersPage from './OrdersPage.jsx';
import {apiRequest} from '../services/api.js';

vi.mock('../services/api.js',()=>({apiRequest:vi.fn()}));

const pendingOrder={
  id:'po-1',
  po_number:'PP-20261104-ABC12345',
  status:'pending_approval',
  currency:'USD',
  total_amount:'240.00',
  created_at:'2026-11-04T07:00:00Z',
  items:[{id:'item-1',product_title:'Business monitor',merchant:'Retailer',quantity:2,offer_url:'https://retailer.example/item'}],
  approvals:[],payment:null,audit_events:[],
};

function renderPage(entry='/orders'){
  const client=new QueryClient({defaultOptions:{queries:{retry:false},mutations:{retry:false}}});
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[entry]}><OrdersPage/></MemoryRouter>
    </QueryClientProvider>
  );
}

describe('OrdersPage',()=>{
  beforeEach(()=>apiRequest.mockReset());

  it('renders pending approval orders and the saved total',async()=>{
    apiRequest.mockResolvedValue([pendingOrder]);
    renderPage();
    expect(await screen.findByRole('heading',{name:'Business monitor'})).toBeInTheDocument();
    expect(screen.getByText('$240.00')).toBeInTheDocument();
    expect(screen.getByRole('button',{name:/approve purchase/i})).toBeInTheDocument();
  });

  it('records a human approval through the API',async()=>{
    apiRequest.mockResolvedValueOnce([pendingOrder])
      .mockResolvedValueOnce({...pendingOrder,status:'approved'})
      .mockResolvedValue([]);
    renderPage();
    fireEvent.click(await screen.findByRole('button',{name:/approve purchase/i}));
    await waitFor(()=>expect(apiRequest).toHaveBeenCalledWith('/purchase-orders/po-1/approve',{
      method:'POST',body:JSON.stringify({comment:null}),
    }));
  });

  it('does not expose capture before the buyer returns from PayPal',async()=>{
    apiRequest.mockResolvedValue([{
      ...pendingOrder,status:'payment_pending',
      payment:{status:'created',approval_url:'https://www.sandbox.paypal.com/checkout'},
    }]);
    renderPage();
    const checkout=await screen.findByRole('link',{name:/continue to paypal/i});
    expect(checkout).toHaveAttribute('href','https://www.sandbox.paypal.com/checkout');
    expect(screen.queryByRole('button',{name:/confirm buyer approval/i})).not.toBeInTheDocument();
  });

  it('uses the current tab for PayPal approval so the session survives the return',async()=>{
    apiRequest.mockResolvedValue([{
      ...pendingOrder,status:'payment_pending',
      payment:{status:'created',approval_url:'https://www.sandbox.paypal.com/checkout'},
    }]);
    renderPage();
    const checkout=await screen.findByRole('link',{name:/continue to paypal/i});
    expect(checkout).toHaveAttribute('href','https://www.sandbox.paypal.com/checkout');
    expect(checkout).not.toHaveAttribute('target','_blank');
  });
});

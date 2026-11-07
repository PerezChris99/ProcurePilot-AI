import {beforeEach,describe,expect,it,vi} from 'vitest';
import {fireEvent,render,screen,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {MemoryRouter} from 'react-router-dom';
import OrdersPage from './OrdersPage.jsx';
import {apiRequest} from '../services/api.js';
import {reservePayPalSandboxTab,navigatePayPalSandboxTab,closePendingPayPalTab} from '../services/paypalCheckout.js';

vi.mock('../services/api.js',()=>({apiRequest:vi.fn(),downloadAuthorizedFile:vi.fn()}));
vi.mock('../services/paypalCheckout.js',()=>({reservePayPalSandboxTab:vi.fn(),navigatePayPalSandboxTab:vi.fn(),closePendingPayPalTab:vi.fn(),verifiedSandboxApprovalUrl:vi.fn(raw=>raw)}));

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
    const checkout=await screen.findByRole('link',{name:/open paypal in new tab/i});
    expect(checkout).toHaveAttribute('href','https://www.sandbox.paypal.com/checkout');
    expect(screen.queryByRole('button',{name:/confirm buyer approval/i})).not.toBeInTheDocument();
  });

  it('opens the saved PayPal approval link in a separate, opener-safe tab',async()=>{
    apiRequest.mockResolvedValue([{
      ...pendingOrder,status:'payment_pending',
      payment:{status:'created',approval_url:'https://www.sandbox.paypal.com/checkout'},
    }]);
    renderPage();
    const checkout=await screen.findByRole('link',{name:/open paypal in new tab/i});
    expect(checkout).toHaveAttribute('href','https://www.sandbox.paypal.com/checkout');
    expect(checkout).toHaveTextContent(/^Open PayPal\s*$/);
    expect(checkout).toHaveAttribute('target','_blank');
    expect(checkout).toHaveAttribute('rel','noopener noreferrer');
  });
});


describe('Decision Passport disclosure',()=>{
  beforeEach(()=>apiRequest.mockReset());
  it('loads an owner-scoped immutable snapshot only when asked',async()=>{
    apiRequest.mockImplementation(path=>{
      if(path==='/purchase-orders')return Promise.resolve([pendingOrder]);
      if(path==='/purchase-orders/po-1/passport')return Promise.resolve({
        order_number:pendingOrder.po_number,status:'pending_approval',
        evidence:{discovered_at:'2026-11-04T12:00:00Z',selected:{title:'Business monitor'},
          request:{currency:'USD'},compared_offers:[{product_id:'product-a',title:'Monitor A',merchant:'store.example',currency:'USD',unit_price:'120.00',eligible:true}]},
        comparison:{selected_total:'240.00',least_cost_eligible_total:'240.00',premium_vs_least_cost:'0.00'},
        payment_proof:{status:'not_started',signed_webhook_correlated:false},
        buyer_decision:{approved_at:null},audit_timeline:[],snapshot_sha256:'test-hash',
      });
      return Promise.resolve([]);
    });
    renderPage();
    const toggle=await screen.findByRole('button',{name:'View Decision Passport'});
    expect(apiRequest).not.toHaveBeenCalledWith('/purchase-orders/po-1/passport');
    fireEvent.click(toggle);
    expect(await screen.findByRole('heading',{name:'Decision Passport'})).toBeInTheDocument();
    expect(screen.getByText('Monitor A')).toBeInTheDocument();
    expect(screen.getByRole('button',{name:'Export PDF'})).toBeInTheDocument();
    expect(apiRequest).toHaveBeenCalledWith('/purchase-orders/po-1/passport');
  });
});


describe('New-tab PayPal Sandbox checkout navigation',()=>{
  beforeEach(()=>{apiRequest.mockReset();reservePayPalSandboxTab.mockReset();navigatePayPalSandboxTab.mockReset();closePendingPayPalTab.mockReset();});

  it('reserves a new tab on click before the async API call then redirects only that tab',async()=>{
    const checkout='https://www.sandbox.paypal.com/checkoutnow?token=PAYPAL-123';
    const tab={closed:false};
    reservePayPalSandboxTab.mockReturnValue(tab);
    navigatePayPalSandboxTab.mockReturnValue(true);
    apiRequest.mockImplementation(path=>{
      if(path==='/purchase-orders')return Promise.resolve([
        {...pendingOrder,status:'approved'},
      ]);
      if(path==='/purchase-orders/po-1/payments/paypal/create')
        return Promise.resolve({approval_url:checkout});
      return Promise.resolve([]);
    });
    renderPage();
    fireEvent.click(await screen.findByRole('button',{
      name:/create paypal sandbox checkout/i,
    }));
    await waitFor(()=>expect(navigatePayPalSandboxTab).toHaveBeenCalledWith(checkout,tab));
    expect(reservePayPalSandboxTab).toHaveBeenCalledTimes(1);
    const post=apiRequest.mock.calls.findIndex(call=>call[0]==='/purchase-orders/po-1/payments/paypal/create');
    expect(reservePayPalSandboxTab.mock.invocationCallOrder[0])
      .toBeLessThan(apiRequest.mock.invocationCallOrder[post]);
    expect(closePendingPayPalTab).not.toHaveBeenCalled();
    expect(apiRequest).toHaveBeenCalledWith(
      '/purchase-orders/po-1/payments/paypal/create',{method:'POST'});
  });

  it('shows a secure manual new-tab link when a popup blocker prevents automatic opening',async()=>{
    const checkout='https://www.sandbox.paypal.com/checkoutnow?token=PAYPAL-123';
    let checkoutCreated=false;
    reservePayPalSandboxTab.mockReturnValue(null);
    navigatePayPalSandboxTab.mockReturnValue(false);
    apiRequest.mockImplementation(path=>{
      if(path==='/purchase-orders')return Promise.resolve([
        {...pendingOrder,status:checkoutCreated?'payment_pending':'approved',
          payment:checkoutCreated?{status:'created',approval_url:checkout}:null},
      ]);
      if(path==='/purchase-orders/po-1/payments/paypal/create'){
        checkoutCreated=true;
        return Promise.resolve({approval_url:checkout});
      }
      return Promise.resolve([]);
    });
    renderPage();
    fireEvent.click(await screen.findByRole('button',{name:/create paypal sandbox checkout/i}));
    expect(await screen.findByText(/browser blocked the separate PayPal tab/i)).toBeInTheDocument();
    const link=await screen.findByRole('link',{name:/open paypal in new tab/i});
    expect(link).toHaveAttribute('href',checkout);
    expect(link).toHaveAttribute('target','_blank');
    expect(link).toHaveAttribute('rel','noopener noreferrer');
    expect(navigatePayPalSandboxTab).toHaveBeenCalledWith(checkout,null);
    expect(apiRequest).toHaveBeenCalledWith('/purchase-orders/po-1/payments/paypal/create',{method:'POST'});
  });

  it('closes a reserved blank tab when the backend fails before returning a link',async()=>{
    const tab={closed:false};
    reservePayPalSandboxTab.mockReturnValue(tab);
    apiRequest.mockImplementation(path=>{
      if(path==='/purchase-orders')return Promise.resolve([{...pendingOrder,status:'approved'}]);
      if(path==='/purchase-orders/po-1/payments/paypal/create')
        return Promise.reject(new Error('PayPal Sandbox unavailable'));
      return Promise.resolve([]);
    });
    renderPage();
    fireEvent.click(await screen.findByRole('button',{name:/create paypal sandbox checkout/i}));
    expect(await screen.findByRole('alert')).toHaveTextContent('PayPal Sandbox unavailable');
    expect(closePendingPayPalTab).toHaveBeenCalledWith(tab);
    expect(navigatePayPalSandboxTab).not.toHaveBeenCalled();
  });

  it('keeps failed URL validation from navigating the tab or the application',async()=>{
    const tab={closed:false};
    reservePayPalSandboxTab.mockReturnValue(tab);
    navigatePayPalSandboxTab.mockImplementation(()=>{throw new Error('invalid sandbox link')});
    apiRequest.mockImplementation(path=>{
      if(path==='/purchase-orders')return Promise.resolve([{...pendingOrder,status:'approved'}]);
      if(path==='/purchase-orders/po-1/payments/paypal/create')
        return Promise.resolve({approval_url:'https://www.paypal.com/checkoutnow?token=live'});
      return Promise.resolve([]);
    });
    renderPage();
    fireEvent.click(await screen.findByRole('button',{name:/create paypal sandbox checkout/i}));
    expect(await screen.findByText(/unexpected checkout address/i)).toBeInTheDocument();
    expect(closePendingPayPalTab).toHaveBeenCalledWith(tab);
  });

  it('shows explicit capture only after an approved buyer returns in another tab',async()=>{
    apiRequest.mockResolvedValue([{
      ...pendingOrder,status:'payment_pending',
      payment:{status:'created',approval_url:'https://www.sandbox.paypal.com/checkoutnow?token=PAYPAL-123'},
    }]);
    renderPage('/orders?paypal=return&po=po-1');
    expect(await screen.findByRole('button',{name:/confirm buyer approval & capture/i})).toBeInTheDocument();
    expect(screen.getByText(/return alone never captures payment/i)).toBeInTheDocument();
  });

});

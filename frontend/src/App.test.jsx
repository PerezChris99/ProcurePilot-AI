import {beforeEach,describe,expect,it,vi} from 'vitest';
import {fireEvent,render,screen,waitFor} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';
import App from './App.jsx';

const {auth}=vi.hoisted(()=>({auth:{user:null,initializing:false,busy:false,sessionExpired:false,login:vi.fn()}}));
vi.mock('./context/useAuth.js',()=>({useAuth:()=>auth}));
vi.mock('./components/layout/AppShell.jsx',async()=>{
  const {Outlet}=await vi.importActual('react-router-dom');
  return {default:()=> <Outlet/>};
});
vi.mock('./pages/DashboardPage.jsx',()=>({default:()=> <h1>Signed-in dashboard</h1>}));
vi.mock('./pages/OrdersPage.jsx',async()=>{
  const {useLocation}=await vi.importActual('react-router-dom');
  function OrdersPageStub(){
    const location=useLocation();
    return <><h1>Orders checkout return</h1><p data-testid="checkout-query">{location.search}</p></>;
  }
  return {default:OrdersPageStub};
});

function renderAt(path){return render(<MemoryRouter initialEntries={[path]}><App/></MemoryRouter>)}

describe('Public landing and protected workspace routing',()=>{
  beforeEach(()=>{auth.user=null;auth.initializing=false;auth.busy=false;auth.sessionExpired=false;});

  it('shows the landing page at / for unauthenticated judges',async()=>{
    renderAt('/');
    expect(await screen.findByRole('heading',{level:1})).toHaveTextContent(/every purchase, accountable/i);
    expect(screen.getByRole('link',{name:/get started/i})).toHaveAttribute('href','/register');
  });

  it('requires authentication for the signed-in /dashboard, not for public privacy',()=>{
    renderAt('/dashboard');
    expect(screen.getByRole('heading',{name:'Sign in to ProcurePilot'})).toBeInTheDocument();
    expect(screen.queryByRole('heading',{name:'Signed-in dashboard'})).not.toBeInTheDocument();
  });

  it('shows the protected dashboard to an authenticated workspace user',async()=>{
    auth.user={id:'person-1',full_name:'Procurement Judge'};
    renderAt('/dashboard');
    expect(await screen.findByRole('heading',{name:'Signed-in dashboard'})).toBeInTheDocument();
  });

  it('returns to the original PayPal callback and PO after a required sign-in',async()=>{
    auth.login=vi.fn(async()=>{auth.user={id:'person-1',full_name:'Procurement Judge'}});
    renderAt('/orders?paypal=return&po=po-123');
    expect(screen.getByRole('heading',{name:'Sign in to ProcurePilot'})).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Email address'),{target:{value:'judge@example.com'}});
    fireEvent.change(screen.getByLabelText('Password'),{target:{value:'sample-sign-in'}});
    fireEvent.click(screen.getByRole('button',{name:'Sign in'}));
    await waitFor(()=>expect(screen.getByRole('heading',{name:'Orders checkout return'})).toBeInTheDocument());
    expect(screen.getByTestId('checkout-query')).toHaveTextContent('?paypal=return&po=po-123');
    expect(auth.login).toHaveBeenCalledTimes(1);
  });

  it('retains the /orders path used by PayPal Sandbox return',async()=>{
    auth.user={id:'person-1',full_name:'Procurement Judge'};
    renderAt('/orders?token=SANDBOX-ORDER-ID');
    expect(await screen.findByRole('heading',{name:'Orders checkout return'})).toBeInTheDocument();
  });
  it('shows an accessible pending state while checking sign-in credentials',()=>{
    auth.busy=true;
    renderAt('/login');
    expect(screen.getByRole('button',{name:'Signing in…'})).toBeDisabled();
    expect(screen.getByRole('progressbar',{name:'Verifying your account securely…'})).toBeInTheDocument();
  });

  it('shows a pending state while securely creating a workspace',()=>{
    auth.busy=true;
    renderAt('/register');
    expect(screen.getByRole('button',{name:'Creating workspace…'})).toBeDisabled();
    expect(screen.getByRole('progressbar',{name:'Creating your secure workspace…'})).toBeInTheDocument();
  });

  it('shows restored-session progress while revalidating an existing token',()=>{
    auth.initializing=true;
    renderAt('/dashboard');
    expect(screen.getByRole('progressbar',{name:'Restoring your secure session…'})).toBeInTheDocument();
  });

});

import {beforeEach,describe,expect,it,vi} from 'vitest';
import {render,screen} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';
import App from './App.jsx';

const {auth}=vi.hoisted(()=>({auth:{user:null,initializing:false,busy:false}}));
vi.mock('./context/useAuth.js',()=>({useAuth:()=>auth}));
vi.mock('./components/layout/AppShell.jsx',async()=>{
  const {Outlet}=await vi.importActual('react-router-dom');
  return {default:()=> <Outlet/>};
});
vi.mock('./pages/DashboardPage.jsx',()=>({default:()=> <h1>Signed-in dashboard</h1>}));
vi.mock('./pages/OrdersPage.jsx',()=>({default:()=> <h1>Orders checkout return</h1>}));

function renderAt(path){return render(<MemoryRouter initialEntries={[path]}><App/></MemoryRouter>)}

describe('Public landing and protected workspace routing',()=>{
  beforeEach(()=>{auth.user=null;auth.initializing=false;});

  it('shows the landing page at / for unauthenticated judges',()=>{
    renderAt('/');
    expect(screen.getByRole('heading',{level:1})).toHaveTextContent(/every purchase, accountable/i);
    expect(screen.getByRole('link',{name:/get started/i})).toHaveAttribute('href','/register');
  });

  it('requires authentication for the signed-in /dashboard, not for public privacy',()=>{
    renderAt('/dashboard');
    expect(screen.getByRole('heading',{name:'Sign in to ProcurePilot'})).toBeInTheDocument();
    expect(screen.queryByRole('heading',{name:'Signed-in dashboard'})).not.toBeInTheDocument();
  });

  it('shows the protected dashboard to an authenticated workspace user',()=>{
    auth.user={id:'person-1',full_name:'Procurement Judge'};
    renderAt('/dashboard');
    expect(screen.getByRole('heading',{name:'Signed-in dashboard'})).toBeInTheDocument();
  });

  it('retains the /orders path used by PayPal Sandbox return',()=>{
    auth.user={id:'person-1',full_name:'Procurement Judge'};
    renderAt('/orders?token=SANDBOX-ORDER-ID');
    expect(screen.getByRole('heading',{name:'Orders checkout return'})).toBeInTheDocument();
  });
});

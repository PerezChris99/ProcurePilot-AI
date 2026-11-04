import {beforeEach,describe,expect,it,vi} from 'vitest';
import {render,screen,within,fireEvent} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {MemoryRouter,Route,Routes} from 'react-router-dom';
import AppShell from './AppShell.jsx';
import {getIntegrationStatus} from '../../services/api.js';

const {mockLogout}=vi.hoisted(()=>({mockLogout:vi.fn()}));
vi.mock('../../context/useAuth.js',()=>({
  useAuth:()=>({user:{full_name:'Judge Example',email:'judge@example.com'},logout:mockLogout}),
}));
vi.mock('../../services/api.js',()=>({getIntegrationStatus:vi.fn()}));

function renderShell(path='/dashboard'){
  const client=new QueryClient({defaultOptions:{queries:{retry:false}}});
  return render(<QueryClientProvider client={client}>
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route element={<AppShell/>}>
          <Route path="/dashboard" element={<p>Overview content</p>}/>
          <Route path="/activity" element={<p>Activity content</p>}/>
          <Route path="/discovery" element={<p>Discovery content</p>}/>
          <Route path="/requests/:requestId" element={<p>Research detail</p>}/>
        </Route>
      </Routes>
    </MemoryRouter>
  </QueryClientProvider>);
}

describe('AppShell navigation and environment',()=>{
  beforeEach(()=>{
    getIntegrationStatus.mockReset();
    mockLogout.mockReset();
    getIntegrationStatus.mockResolvedValue({
      runtime:{environment:'development'},
      ai:{configured:false},
      paypal:{environment:'sandbox'},
    });
  });

  it('offers all six real sidebar destinations in the mobile bottom dock',async()=>{
    renderShell();
    const dock=screen.getByRole('navigation',{name:'Mobile workspace navigation'});
    const paths=['/dashboard','/procurement','/orders','/approvals','/activity','/discovery'];
    const links=within(dock).getAllByRole('link');
    expect(links.map(link=>link.getAttribute('href'))).toEqual(paths);
    expect(within(dock).getByRole('link',{name:'Overview'})).toHaveClass('active');
    expect(await screen.findByText('LOCAL DEMO · PAYPAL SANDBOX')).toBeInTheDocument();
    expect(screen.getByText('Key not configured')).toBeInTheDocument();
  });

  it('supports real Activity and Discover routes without duplicate destinations',async()=>{
    renderShell('/activity');
    expect(screen.getByText('Activity content')).toBeInTheDocument();
    expect(within(screen.getByRole('navigation',{name:'Mobile workspace navigation'}))
      .getByRole('link',{name:'Activity'})).toHaveClass('active');
    expect(within(screen.getByRole('navigation',{name:'Management navigation'}))
      .getByRole('link',{name:'Product discovery'})).toHaveAttribute('href','/discovery');
  });

  it('keeps the Discover dock selected while inspecting a saved request',()=>{
    renderShell('/requests/r-123');
    expect(screen.getByText('Research detail')).toBeInTheDocument();
    expect(within(screen.getByRole('navigation',{name:'Mobile workspace navigation'}))
      .getByRole('link',{name:'Product discovery'})).toHaveClass('active');
  });

  it('reflects actual live environment configuration rather than fixed sandbox copy',async()=>{
    getIntegrationStatus.mockResolvedValue({
      runtime:{environment:'production'},
      ai:{configured:true},
      paypal:{environment:'live'},
    });
    renderShell();
    expect(await screen.findByText('PRODUCTION · PAYPAL LIVE')).toBeInTheDocument();
    expect(screen.getByText('Key configured')).toBeInTheDocument();
    fireEvent.click(screen.getAllByRole('button',{name:'Sign out'})[0]);
    expect(mockLogout).toHaveBeenCalledTimes(1);
  });
});

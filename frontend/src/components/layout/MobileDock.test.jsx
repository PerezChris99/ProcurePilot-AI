import {beforeEach,describe,expect,it,vi} from 'vitest';
import {render,screen,within} from '@testing-library/react';
import {MemoryRouter,Route,Routes} from 'react-router-dom';
import MobileDock from './MobileDock.jsx';
import PublicLayout from './PublicLayout.jsx';
import AuthLayout from './AuthLayout.jsx';
import {isNavigationActive,workspaceNavigation} from './navigation.js';

const {auth}=vi.hoisted(()=>({auth:{user:null}}));
vi.mock('../../context/useAuth.js',()=>({useAuth:()=>auth}));

function renderDock(path='/',variant='public'){
  return render(<MemoryRouter initialEntries={[path]}><MobileDock variant={variant}/></MemoryRouter>);
}
function dock(){
  return screen.getByRole('navigation',{name:'Mobile website navigation'});
}

describe('universal mobile navigation',()=>{
  beforeEach(()=>{auth.user=null;});

  it('presents six useful public routes before sign-in, with no private-order traps',()=>{
    renderDock();
    const links=within(dock()).getAllByRole('link');
    for(const link of links){
      const symbol=link.querySelector('svg.ios-dock-icon');
      expect(symbol).toHaveAttribute('data-icon-style','ios');
      expect(symbol).toHaveAttribute('aria-hidden','true');
    }
    expect(links.map(link=>link.getAttribute('href')))
      .toEqual(['/','/#why','/#how','/#faq','/about','/login']);
    expect(within(dock()).getByRole('link',{name:'Home'}))
      .toHaveAttribute('aria-current','page');
    expect(within(dock()).queryByRole('link',{name:'Purchase orders'}))
      .not.toBeInTheDocument();
  });

  it('selects exactly one public section for a hash link',()=>{
    renderDock('/#how');
    const selected=within(dock()).getAllByRole('link')
      .filter(link=>link.getAttribute('aria-current')==='page');
    expect(selected).toHaveLength(1);
    expect(selected[0]).toHaveAttribute('href','/#how');
    expect(isNavigationActive('/','#faq','/#faq')).toBe(true);
    expect(isNavigationActive('/','#faq','/')).toBe(false);
  });

  it('changes account action to Workspace when signed in',()=>{
    auth.user={id:'member-1'};
    renderDock('/about');
    expect(within(dock()).getByRole('link',{name:'Open workspace'}))
      .toHaveAttribute('href','/dashboard');
    expect(within(dock()).getByRole('link',{name:'About ProcurePilot'}))
      .toHaveAttribute('aria-current','page');
  });

  it('keeps all six protected workspace destinations and discovery detail state',()=>{
    renderDock('/requests/request-123','workspace');
    const nav=screen.getByRole('navigation',{name:'Mobile workspace navigation'});
    for(const link of within(nav).getAllByRole('link')){
      expect(link.querySelector('svg.ios-dock-icon')).toHaveAttribute('data-icon-style','ios');
    }
    expect(within(nav).getAllByRole('link').map(link=>link.getAttribute('href')))
      .toEqual(workspaceNavigation.map(item=>item.to));
    expect(within(nav).getByRole('link',{name:'Product discovery'}))
      .toHaveAttribute('aria-current','page');
  });

  it('mounts the same public mobile dock inside public information pages',()=>{
    render(<MemoryRouter initialEntries={['/about']}>
      <Routes><Route element={<PublicLayout/>}>
        <Route path="/about" element={<h1>About ProcurePilot</h1>}/>
      </Route></Routes>
    </MemoryRouter>);
    expect(screen.getByRole('heading',{name:'About ProcurePilot'})).toBeInTheDocument();
    expect(within(dock()).getAllByRole('link')).toHaveLength(6);
    expect(within(dock()).getByRole('link',{name:'About ProcurePilot'}))
      .toHaveAttribute('aria-current','page');
  });

  it('mounts the same dock for login and registration layouts',()=>{
    render(<MemoryRouter initialEntries={['/login']}>
      <AuthLayout><h1>Sign in</h1></AuthLayout>
    </MemoryRouter>);
    expect(screen.getByRole('heading',{name:'Sign in'})).toBeInTheDocument();
    expect(within(dock()).getByRole('link',{name:'Sign in'}))
      .toHaveAttribute('href','/login');
  });
});

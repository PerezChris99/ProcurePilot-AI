import {beforeEach,describe,expect,it,vi} from 'vitest';
import {render,screen,fireEvent} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {MemoryRouter} from 'react-router-dom';
import DiscoveryPage from './DiscoveryPage.jsx';
import {apiRequest} from '../services/api.js';

vi.mock('../services/api.js',()=>({apiRequest:vi.fn()}));
function renderPage(){
  const client=new QueryClient({defaultOptions:{queries:{retry:false}}});
  return render(<QueryClientProvider client={client}><MemoryRouter><DiscoveryPage/></MemoryRouter></QueryClientProvider>);
}

describe('DiscoveryPage',()=>{
  beforeEach(()=>apiRequest.mockReset());
  it('loads user-owned saved requests and filters on-device',async()=>{
    apiRequest.mockResolvedValue([
      {id:'r-1',request_text:'27 inch IPS monitors',status:'products_discovered',currency:'USD',quantity:2,created_at:'2026-11-04T12:00:00Z'},
      {id:'r-2',request_text:'Office laptop stands',status:'draft',currency:'USD',quantity:4,created_at:'2026-11-04T12:00:00Z'},
    ]);
    renderPage();
    expect(await screen.findByRole('heading',{name:'27 inch IPS monitors'})).toBeInTheDocument();
    expect(screen.getByRole('link',{name:/open product discovery/i})).toHaveAttribute('href','/requests/r-1');
    fireEvent.change(screen.getByRole('searchbox',{name:'Filter saved procurement requests'}),{target:{value:'monitors'}});
    expect(screen.getByRole('heading',{name:'27 inch IPS monitors'})).toBeInTheDocument();
    expect(screen.queryByRole('heading',{name:'Office laptop stands'})).not.toBeInTheDocument();
    expect(apiRequest).toHaveBeenCalledWith('/procurement-requests?limit=100');
  });

  it('shows a new-request action when no saved searches exist',async()=>{
    apiRequest.mockResolvedValue([]);
    renderPage();
    expect(await screen.findByText('No saved requests yet')).toBeInTheDocument();
    expect(screen.getByRole('link',{name:/create request/i})).toHaveAttribute('href','/procurement');
  });
});

import {beforeEach,describe,expect,it,vi} from 'vitest';
import {render,screen} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {MemoryRouter} from 'react-router-dom';
import ActivityPage from './ActivityPage.jsx';
import {getDashboardSummary} from '../services/api.js';

vi.mock('../services/api.js',()=>({getDashboardSummary:vi.fn()}));
function renderPage(){
  const client=new QueryClient({defaultOptions:{queries:{retry:false}}});
  return render(<QueryClientProvider client={client}><MemoryRouter><ActivityPage/></MemoryRouter></QueryClientProvider>);
}

describe('ActivityPage',()=>{
  beforeEach(()=>getDashboardSummary.mockReset());
  it('renders genuine saved order events and opens their audit overview',async()=>{
    getDashboardSummary.mockResolvedValue({
      recent_activity:[{id:'event-1',action:'purchase_order.approved',created_at:'2026-11-04T11:00:00Z'}],
    });
    renderPage();
    expect(await screen.findByText('purchase order · approved')).toBeInTheDocument();
    expect(screen.getByRole('link',{name:/open purchase-order audit trails/i})).toHaveAttribute('href','/orders');
  });
  it('keeps an honest empty state with no fabricated events',async()=>{
    getDashboardSummary.mockResolvedValue({recent_activity:[]});
    renderPage();
    expect(await screen.findByText('No purchasing activity yet')).toBeInTheDocument();
    expect(screen.queryByText('purchase order · approved')).not.toBeInTheDocument();
  });
});

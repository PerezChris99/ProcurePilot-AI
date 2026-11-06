import {beforeEach,describe,expect,it,vi} from 'vitest';
import {fireEvent,render,screen,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {MemoryRouter} from 'react-router-dom';
import TrustLabPage from './TrustLabPage.jsx';
import {apiRequest} from '../services/api.js';

vi.mock('../services/api.js',()=>({apiRequest:vi.fn()}));

function renderPage(){
  const client=new QueryClient({defaultOptions:{queries:{retry:false}}});
  return render(<QueryClientProvider client={client}>
    <MemoryRouter><TrustLabPage/></MemoryRouter>
  </QueryClientProvider>);
}

const example={
  source:'synthetic_policy_fixtures',
  executed_at:'2026-11-06T14:00:00Z',
  passed:2,total:2,payment_calls:0,
  scenarios:[
    {id:'valid_offer',name:'Valid 27-inch monitor',intent:'Two 27-inch monitors',
      product_title:'27-inch monitor',quantity:2,unit_price:'140.00',
      quoted_total:'280.00',offer_currency:'USD',
      expected_allowed:true,allowed:true,passed:true,violations:[]},
    {id:'wrong_diagonal',name:'Wrong monitor diagonal',intent:'Four 72-inch monitors',
      product_title:'24-inch monitor',quantity:4,unit_price:'180.00',
      quoted_total:'720.00',offer_currency:'USD',expected_allowed:false,
      allowed:false,passed:true,
      violations:['Required 72-inch monitor diagonal does not match the listing']},
  ],
};

describe('Decision Trust Lab',()=>{
  beforeEach(()=>apiRequest.mockReset());

  it('shows real policy results on clearly labelled synthetic fixture data',async()=>{
    apiRequest.mockResolvedValue(example);
    renderPage();
    expect(await screen.findByRole('heading',{name:'2 / 2 checks matched expectations'}))
      .toBeInTheDocument();
    expect(screen.getByText('Wrong monitor diagonal')).toBeInTheDocument();
    expect(screen.getByText('Required 72-inch monitor diagonal does not match the listing'))
      .toBeInTheDocument();
    expect(screen.getByText(/Fixtures only · No Channel3, Gemini, or PayPal calls/))
      .toBeInTheDocument();
    expect(apiRequest).toHaveBeenCalledWith('/trust-lab/scenarios');
    fireEvent.click(screen.getByRole('button',{name:'Run policy checks'}));
    await waitFor(()=>expect(apiRequest).toHaveBeenCalledTimes(2));
  });

  it('reports backend failure instead of inventing passed scenarios',async()=>{
    apiRequest.mockRejectedValue(new Error('Not authenticated'));
    renderPage();
    expect(await screen.findByRole('alert')).toHaveTextContent('Not authenticated');
    expect(screen.queryByText(/checks matched expectations/)).not.toBeInTheDocument();
  });
});

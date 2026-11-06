import {beforeEach,describe,expect,it,vi} from 'vitest';
import {fireEvent,render,screen,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {MemoryRouter} from 'react-router-dom';
import TrustLabPage from './TrustLabPage.jsx';
import {apiRequest} from '../services/api.js';

vi.mock('../services/api.js',()=>({apiRequest:vi.fn()}));

function renderPage(){
  const client=new QueryClient({defaultOptions:{queries:{retry:false}}});
  const result=render(<QueryClientProvider client={client}>
    <MemoryRouter><TrustLabPage/></MemoryRouter>
  </QueryClientProvider>);
  return {...result,client};
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
    const {client}=renderPage();
    expect(await screen.findByRole('heading',{name:'2 / 2 checks matched expectations'}))
      .toBeInTheDocument();
    expect(screen.getByText('Wrong monitor diagonal')).toBeInTheDocument();
    expect(screen.getByText('Required 72-inch monitor diagonal does not match the listing'))
      .toBeInTheDocument();
    expect(screen.getByText(/Fixtures only · No Channel3, Gemini, or PayPal calls/))
      .toBeInTheDocument();
    expect(apiRequest).toHaveBeenCalledWith('/trust-lab/scenarios');
    fireEvent.click(screen.getByRole('button',{name:'Run policy checks'}));
    // Await the REFRESH COMPLETION, not merely its invocation, so one test
    // cannot leave a query active while the next test changes the API mock.
    await waitFor(()=>{
      expect(apiRequest).toHaveBeenCalledTimes(2);
      expect(client.isFetching()).toBe(0);
    });
  });

  it('reports backend failure without fabricating checks and recovers only after a successful retry',async()=>{
    // Reject exactly the initial request. A later explicit retry must use a
    // real resolved API response rather than inheriting a permanently failing
    // mock from this test.
    apiRequest.mockRejectedValueOnce(new Error('Not authenticated'))
      .mockResolvedValueOnce(example);
    const {client}=renderPage();
    expect(await screen.findByRole('alert')).toHaveTextContent('Not authenticated');
    expect(screen.queryByText(/checks matched expectations/)).not.toBeInTheDocument();
    expect(apiRequest).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole('button',{name:'Run policy checks'}));
    expect(await screen.findByRole('heading',{name:'2 / 2 checks matched expectations'}))
      .toBeInTheDocument();
    await waitFor(()=>{
      expect(apiRequest).toHaveBeenCalledTimes(2);
      expect(client.isFetching()).toBe(0);
    });
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});

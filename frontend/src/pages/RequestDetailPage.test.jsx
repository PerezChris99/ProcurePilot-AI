import {beforeEach,describe,expect,it,vi} from 'vitest';
import {fireEvent,render,screen,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {MemoryRouter,Route,Routes} from 'react-router-dom';
import RequestDetailPage from './RequestDetailPage.jsx';
import {apiRequest} from '../services/api.js';

vi.mock('../services/api.js',()=>({apiRequest:vi.fn()}));

const offer={
  url:'https://approved.example.com/monitor',
  domain:'approved.example.com',
  availability:'InStock',
  condition:'new',
  price:{amount:'120.00',currency:'USD'},
};

function requestFixture({source='Channel3',eligible=true,records=true}={}){
  return {
    id:'req-qa',status:source==='Channel3'?'products_discovered':'sample_preview',
    request_text:'Two 27-inch monitors for a small office',
    quantity:2,budget:'280.00',currency:'USD',policy_json:{},
    analysis_json:{
      source,discovered_at:'2026-11-05T10:00:00Z',
      demo_fixture:source==='offline_demo',
      results:records?[{
        product:{
          id:'monitor-qa',title:'QA 27-inch monitor',
          brands:[],images:[],description:'Business display',
          offers:[offer],structured_attributes:{screen_size:['27 inch']},
        },
        ranking:{
          eligible,score:'92.00',matched_attributes:[],
          unmet_requirements:eligible?[]:['screen_size'],
          available:true,explanation:['Catalogue evidence checked'],
        },
        policy:{
          eligible_offer_urls:eligible?[offer.url]:[],
          offer_reasons:eligible?{}:{[offer.url]:['Required screen_size is not evidenced']},
        },
      }]:[],
      ai_source:null,ai_usage:null,next_page_available:false,
    },
  };
}

function renderRequest(){
  const client=new QueryClient({
    defaultOptions:{queries:{retry:false},mutations:{retry:false}},
  });
  return render(<QueryClientProvider client={client}>
    <MemoryRouter initialEntries={['/requests/req-qa']}>
      <Routes><Route path="/requests/:requestId" element={<RequestDetailPage/>}/></Routes>
    </MemoryRouter>
  </QueryClientProvider>);
}

describe('RequestDetailPage - accountable product discovery',()=>{
  beforeEach(()=>{apiRequest.mockReset();});

  it('renders genuine eligible Channel3 offer with evidence and creates priced PO',async()=>{
    apiRequest.mockImplementation(path=>{
      if(path==='/procurement-requests/req-qa')return Promise.resolve(requestFixture());
      if(path==='/procurement-requests/req-qa/purchase-orders')
        return Promise.resolve({id:'po-from-qa'});
      return Promise.resolve({});
    });
    renderRequest();
    expect(await screen.findByRole('heading',{name:'QA 27-inch monitor'}))
      .toBeInTheDocument();
    expect(screen.getByRole('region',{name:'Evidence comparison'}))
      .toBeInTheDocument();
    const order=screen.getByRole('button',{name:/create po/i});
    expect(order).toBeEnabled();
    fireEvent.click(order);
    await waitFor(()=>expect(apiRequest).toHaveBeenCalledWith(
      '/procurement-requests/req-qa/purchase-orders',{
        method:'POST',
        body:JSON.stringify({product_id:'monitor-qa',offer_url:offer.url}),
      },
    ));
  });

  it('never allows purchase of an ineligible real catalogue offer',async()=>{
    apiRequest.mockResolvedValue(requestFixture({eligible:false}));
    renderRequest();
    expect(await screen.findByRole('heading',{name:'QA 27-inch monitor'}))
      .toBeInTheDocument();
    expect(screen.getByRole('button',{name:/create po/i})).toBeDisabled();
    expect(apiRequest).toHaveBeenCalledWith('/procurement-requests/req-qa');
  });

  it('keeps offline sample visibly non-payable even when product looks available',async()=>{
    apiRequest.mockResolvedValue(requestFixture({source:'offline_demo'}));
    renderRequest();
    expect(await screen.findByText(/Offline sample only/i)).toBeInTheDocument();
    expect(screen.getByRole('button',{name:/create po/i})).toBeDisabled();
  });

  it('shows an honest empty-state without generating fake catalogue data',async()=>{
    apiRequest.mockResolvedValue(requestFixture({records:false}));
    renderRequest();
    expect(await screen.findByRole('heading',{name:'No products loaded yet'}))
      .toBeInTheDocument();
    expect(screen.queryByRole('button',{name:/create po/i}))
      .not.toBeInTheDocument();
  });

  it('invokes real application AI analysis route instead of inventing an answer',async()=>{
    apiRequest.mockImplementation(path=>{
      if(path==='/procurement-requests/req-qa')return Promise.resolve(requestFixture());
      if(path==='/procurement-requests/req-qa/analyze')
        return Promise.resolve({explanation:'Evidence-based AI explanation',source:'gemini'});
      return Promise.resolve({});
    });
    renderRequest();
    const button=await screen.findByRole('button',{name:/ask ai to analyze/i});
    fireEvent.click(button);
    await waitFor(()=>expect(apiRequest).toHaveBeenCalledWith(
      '/procurement-requests/req-qa/analyze',{method:'POST'},
    ));
  });
});

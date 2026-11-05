import {beforeEach,describe,expect,it,vi} from 'vitest';
import {fireEvent,render,screen,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import DecisionPassport from './DecisionPassport.jsx';
import {apiRequest,downloadAuthorizedFile} from '../../services/api.js';

vi.mock('../../services/api.js',()=>({
  apiRequest:vi.fn(),downloadAuthorizedFile:vi.fn(),
}));

const report={
  order_number:'PP-20261105-QATEST',status:'approved',
  evidence:{
    discovered_at:'2026-11-05T10:00:00Z',
    selected:{title:'QA monitor'},
    request:{currency:'USD'},
    compared_offers:[{
      product_id:'monitor-qa',title:'Another QA monitor',
      merchant:'retailer.example',unit_price:'120.00',
      currency:'USD',eligible:true,
    }],
    ai:{source:'gemini',explanation:'The catalogue is bounded evidence.'},
  },
  comparison:{
    selected_total:'240.00',least_cost_eligible_total:'240.00',
    premium_vs_least_cost:'0.00',
    note:'Not realized savings; shipping and tax excluded.',
  },
  payment_proof:{status:'not_started',capture_id:null,signed_webhook_correlated:false},
  buyer_decision:{approved_at:null},audit_timeline:[],
  snapshot_sha256:'abc123',
};

function renderPassport(){
  const client=new QueryClient({defaultOptions:{queries:{retry:false}}});
  return render(<QueryClientProvider client={client}>
    <DecisionPassport orderId="po-qa"/>
  </QueryClientProvider>);
}

describe('Decision Passport evidence and exports',()=>{
  beforeEach(()=>{
    apiRequest.mockReset();
    downloadAuthorizedFile.mockReset();
    downloadAuthorizedFile.mockResolvedValue(undefined);
  });

  it('fetches the protected record only after an explicit user action',async()=>{
    apiRequest.mockResolvedValue(report);
    renderPassport();
    expect(apiRequest).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button',{name:'View Decision Passport'}));
    expect(await screen.findByRole('heading',{name:'Decision Passport'}))
      .toBeInTheDocument();
    expect(apiRequest).toHaveBeenCalledWith('/purchase-orders/po-qa/passport');
    expect(screen.getByText('Another QA monitor')).toBeInTheDocument();
    expect(screen.getByText(/not an externally notarized record/i))
      .toBeInTheDocument();
  });

  it('keeps JSON and PDF exports protected by the authenticated API',async()=>{
    apiRequest.mockResolvedValue(report);
    renderPassport();
    fireEvent.click(screen.getByRole('button',{name:'View Decision Passport'}));
    await screen.findByRole('heading',{name:'Decision Passport'});
    fireEvent.click(screen.getByRole('button',{name:'Export JSON'}));
    fireEvent.click(screen.getByRole('button',{name:'Export PDF'}));
    await waitFor(()=>expect(downloadAuthorizedFile).toHaveBeenCalledTimes(2));
    expect(downloadAuthorizedFile).toHaveBeenCalledWith(
      '/purchase-orders/po-qa/passport',
      'ProcurePilot-Decision-Passport-po-qa.json',
    );
    expect(downloadAuthorizedFile).toHaveBeenCalledWith(
      '/purchase-orders/po-qa/passport.pdf',
      'ProcurePilot-Decision-Passport-po-qa.pdf',
    );
  });

  it('reports an unavailable passport instead of showing fabricated evidence',async()=>{
    apiRequest.mockRejectedValue(new Error('Not authorized'));
    renderPassport();
    fireEvent.click(screen.getByRole('button',{name:'View Decision Passport'}));
    expect(await screen.findByRole('alert')).toHaveTextContent(/not authorized/i);
    expect(screen.queryByText('Another QA monitor')).not.toBeInTheDocument();
  });
});

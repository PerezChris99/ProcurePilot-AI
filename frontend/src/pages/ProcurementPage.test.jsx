import {beforeEach,describe,expect,it,vi} from 'vitest';
import {fireEvent,render,screen,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {MemoryRouter} from 'react-router-dom';
import ProcurementPage from './ProcurementPage.jsx';
import {apiRequest} from '../services/api.js';

vi.mock('../services/api.js',()=>({apiRequest:vi.fn(),getHealth:vi.fn(),setAuthToken:vi.fn()}));

function renderPage(){
  const client=new QueryClient({defaultOptions:{queries:{retry:false}}});
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter><ProcurementPage/></MemoryRouter>
    </QueryClientProvider>
  );
}

describe('ProcurementPage',()=>{
  beforeEach(()=>apiRequest.mockReset());

  it('requires a meaningful request before enabling submit',()=>{
    renderPage();
    const submit=screen.getByRole('button',{name:/save and discover products/i});
    expect(submit).toBeDisabled();
    fireEvent.change(screen.getByLabelText(/what are you looking to purchase/i),{
      target:{value:'20 office monitors, 27 inch, IPS'},
    });
    expect(submit).toBeEnabled();
  });

  it('submits only the user request to the authenticated API',async()=>{
    apiRequest.mockResolvedValue({id:'request-123'});
    renderPage();
    fireEvent.change(screen.getByLabelText(/what are you looking to purchase/i),{
      target:{value:'20 office monitors, 27 inch, IPS'},
    });
    fireEvent.change(screen.getByLabelText(/quantity/i),{target:{value:'20'}});
    fireEvent.click(screen.getByRole('button',{name:/save and discover products/i}));
    await waitFor(()=>expect(apiRequest).toHaveBeenCalledWith('/procurement-requests',{
      method:'POST',
      body:JSON.stringify({
        request_text:'20 office monitors, 27 inch, IPS',
        quantity:20,budget:null,currency:'USD',
      }),
    }));
  });
});

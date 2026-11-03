import {describe,expect,it,vi} from 'vitest';
import {fireEvent,render,screen,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {MemoryRouter} from 'react-router-dom';
import ProcurementPage from './ProcurementPage.jsx';
import {apiRequest} from '../services/api.js';
vi.mock('../services/api.js',()=>({apiRequest:vi.fn(),getHealth:vi.fn(),setAuthToken:vi.fn()}));
function renderPage(){const client=new QueryClient({defaultOptions:{queries:{retry:false}}});return render(<QueryClientProvider client={client}><MemoryRouter><ProcurementPage/></MemoryRouter></QueryClientProvider>)}
describe('ProcurementPage',()=>{
  it('requires a meaningful request before enabling submit',()=>{renderPage();expect(screen.getByRole('button',{name:/save and discover products/i})).toBeDisabled();fireEvent.change(screen.getByLabelText(/what are you looking to purchase/i),{target:{value:'20 office monitors, 27 inch, IPS'}});expect(screen.getByRole('button',{name:/save and discover products/i})).toBeEnabled()});
  it('submits the request to the authenticated API instead of faking a purchase',async()=>{apiRequest.mockResolvedValue({id:'request-123'});renderPage();fireEvent.change(screen.getByLabelText(/what are you looking to purchase/i),{target:{value:'20 office monitors, 27 inch, IPS'}});fireEvent.change(screen.getByLabelText(/quantity/i),{target:{value:'20'}});fireEvent.click(screen.getByRole('button',{name:/save and discover products/i}));await waitFor(()=>expect(apiRequest).toHaveBeenCalledWith('/procurement-requests',{method:'POST',body:JSON.stringify({request_text:'20 office monitors, 27 inch, IPS',quantity:20,budget:null,currency:'USD'})}))});
});

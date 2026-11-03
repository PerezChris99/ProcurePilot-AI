import {describe,expect,it,vi} from 'vitest';
import {render,screen} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {MemoryRouter} from 'react-router-dom';
import DashboardPage from './DashboardPage.jsx';
vi.mock('../services/api.js',()=>({getHealth:vi.fn().mockResolvedValue({status:'ok'})}));
function renderPage(){const client=new QueryClient({defaultOptions:{queries:{retry:false}}});return render(<QueryClientProvider client={client}><MemoryRouter><DashboardPage/></MemoryRouter></QueryClientProvider>)}
describe('DashboardPage',()=>{it('renders the procurement overview and primary action',()=>{renderPage();expect(screen.getByRole('heading',{name:/let's buy smarter/i})).toBeInTheDocument();expect(screen.getByRole('link',{name:/new procurement/i})).toBeInTheDocument();expect(screen.getByText(/no activity yet/i)).toBeInTheDocument()})});

import {describe,expect,it,vi} from 'vitest';
import {render,screen,within} from '@testing-library/react';
import {MemoryRouter,Route,Routes} from 'react-router-dom';
import PublicLayout from '../components/layout/PublicLayout.jsx';
import PublicInfoPage from './PublicInfoPage.jsx';

vi.mock('../context/useAuth.js',()=>({useAuth:()=>({user:null})}));

function renderPublic(path){
  return render(<MemoryRouter initialEntries={[path]}>
    <Routes><Route element={<PublicLayout/>}>
      <Route path="/privacy" element={<PublicInfoPage kind="privacy"/>}/>
      <Route path="/terms" element={<PublicInfoPage kind="terms"/>}/>
      <Route path="/security" element={<PublicInfoPage kind="security"/>}/>
    </Route></Routes>
  </MemoryRouter>);
}

describe('Public legal pages',()=>{
  it('exposes legal navigation and real privacy disclosure without requiring authentication',()=>{
    renderPublic('/privacy');
    expect(screen.getByRole('heading',{level:1,name:/privacy, in plain language/i})).toBeInTheDocument();
    expect(screen.getByText(/sessionstorage/i)).toBeInTheDocument();
    const footer=screen.getByRole('navigation',{name:'Legal and support pages'});
    expect(within(footer).getByRole('link',{name:'Privacy'})).toHaveAttribute('href','/privacy');
    expect(within(footer).getByRole('link',{name:'Terms'})).toHaveAttribute('href','/terms');
    expect(within(footer).getByRole('link',{name:'Security'})).toHaveAttribute('href','/security');
    expect(screen.getByRole('link',{name:'Skip to content'})).toHaveAttribute('href','#site-main');
  });

  it('does not advertise a commercial payment product or nonexistent compliance certification',()=>{
    renderPublic('/terms');
    expect(screen.getByText(/PayPal Sandbox, not live merchant settlement/i)).toBeInTheDocument();
    expect(screen.getByText(/not a replacement for jurisdiction-specific legal review/i)).toBeInTheDocument();
  });

  it('lists concrete implemented protections and candid limitations',()=>{
    renderPublic('/security');
    expect(screen.getByText(/Passwords are hashed with Argon2id/i)).toBeInTheDocument();
    expect(screen.getByText(/does not yet claim independent enterprise approver roles/i)).toBeInTheDocument();
  });
});

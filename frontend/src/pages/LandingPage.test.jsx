import {describe,expect,it,vi} from 'vitest';
import {fireEvent,render,screen,within} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';
import LandingPage from './LandingPage.jsx';

vi.mock('../context/useAuth.js',()=>({useAuth:()=>({user:null})}));

function renderLanding(){return render(<MemoryRouter><LandingPage/></MemoryRouter>)}

describe('Public landing page',()=>{
  it('explains the product without invented customer proof or live payment claims',()=>{
    renderLanding();
    expect(screen.getByRole('heading',{level:1})).toHaveTextContent(/every purchase.*accountable/i);
    expect(screen.getByRole('link',{name:/explore procurepilot/i})).toHaveAttribute('href','/register');
    expect(screen.getByText('INTEGRATIONS')).toBeInTheDocument();
    expect(screen.getByText(/sandbox payments/i)).toBeInTheDocument();
    expect(screen.getByText(/PayPal Sandbox only/i)).toBeInTheDocument();
    expect(screen.getByRole('heading',{name:/from request to approval/i})).toBeInTheDocument();
  });

  it('shows three real photo slides with meaningful manual controls and pause',()=>{
    renderLanding();
    const carousel=screen.getByRole('region',{name:'Procurement photography'});
    const hero=screen.getByRole('region',{name:/every purchase.*accountable/i});
    expect(hero).toContainElement(screen.getByRole('heading',{level:1}));
    expect(hero).toContainElement(carousel);
    expect(carousel).not.toContainElement(screen.getByRole('heading',{level:1}));
    expect(within(hero).getByRole('link',{name:/explore procurepilot/i}))
      .toHaveAttribute('href','/register');
    expect(carousel).toHaveClass('site-hero-visual');
    expect(carousel).not.toHaveClass('site-hero');
    // Hidden slides are intentionally decorative (alt=""), so query the slide images directly.
    const images=carousel.querySelectorAll('img.site-hero-image');
    expect(images).toHaveLength(3);
    expect(images[0].getAttribute('src')).toMatch(/^https:\/\/images\.unsplash\.com\/photo-/);
    expect(within(carousel).getByText('Less uncertainty in sourcing')).toBeInTheDocument();
    fireEvent.click(within(carousel).getByRole('button',{name:'Next image'}));
    expect(within(carousel).getByText('Decisions people can stand behind')).toBeInTheDocument();
    fireEvent.click(within(carousel).getByRole('button',{name:'Pause slideshow'}));
    expect(within(carousel).getByRole('button',{name:'Play slideshow'})).toBeInTheDocument();
    fireEvent.click(within(carousel).getByRole('button',{name:/show slide 3/i}));
    expect(within(carousel).getByText('One clearer purchasing workspace')).toBeInTheDocument();
  });

  it('contains factual FAQ answers and a safe CTA for visitors',()=>{
    renderLanding();
    const faq=screen.getByText('Does the AI place orders automatically?').closest('details');
    fireEvent.click(within(faq).getByText('Does the AI place orders automatically?'));
    expect(faq).toHaveAttribute('open');
    expect(within(faq).getByText(/a signed-in person must approve/i)).toBeInTheDocument();
    expect(screen.getByRole('link',{name:/start your workspace/i})).toHaveAttribute('href','/register');
  });
});

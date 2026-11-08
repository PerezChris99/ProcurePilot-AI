import {describe,expect,it} from 'vitest';
import {render,screen} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';
import {PublicFooter} from './PublicLayout.jsx';

describe('PublicFooter attribution',()=>{
  it('places the requested developer link immediately below the photography link',()=>{
    render(<MemoryRouter><PublicFooter/></MemoryRouter>);
    const photo=screen.getByRole('link',{name:/Photography: Unsplash/i});
    const credit=screen.getByRole('link',{name:/Kweezi Perez Christopher/i});
    expect(credit).toHaveAttribute('href','https://kweeziperez.com');
    expect(credit).toHaveAttribute('target','_blank');
    expect(credit).toHaveAttribute('rel','noopener noreferrer');
    expect(photo.nextElementSibling).toContainElement(credit);
    expect(photo.nextElementSibling).toHaveClass('site-footer-credit');
  });
});

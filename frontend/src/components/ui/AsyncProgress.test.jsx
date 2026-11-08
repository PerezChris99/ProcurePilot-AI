import {describe,expect,it} from 'vitest';
import {render,screen} from '@testing-library/react';
import AsyncProgress from './AsyncProgress.jsx';

describe('AsyncProgress',()=>{
  it('reports a real pending request without inventing a percentage',()=>{
    render(<AsyncProgress label="Verifying your account securely…"/>);
    const bar=screen.getByRole('progressbar',{name:'Verifying your account securely…'});
    expect(bar).toBeInTheDocument();
    expect(bar).not.toHaveAttribute('aria-valuenow');
    expect(screen.getByRole('status')).toHaveTextContent('Verifying your account securely…');
  });

  it('supports the compact route-loading presentation',()=>{
    const {container}=render(<AsyncProgress compact label="Opening page…"/>);
    expect(container.querySelector('.async-progress-compact')).toBeInTheDocument();
    expect(screen.getByRole('progressbar',{name:'Opening page…'})).toBeInTheDocument();
  });
});

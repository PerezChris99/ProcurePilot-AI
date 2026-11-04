import {afterEach,beforeEach,describe,expect,it,vi} from 'vitest';
import {act,render,screen} from '@testing-library/react';
import LocalClock from './LocalClock.jsx';

describe('LocalClock',()=>{
  beforeEach(()=>vi.useFakeTimers());
  afterEach(()=>vi.useRealTimers());

  it('shows a live date, seconds and the browser IANA time zone and UTC offset',()=>{
    vi.setSystemTime(new Date('2026-11-04T16:05:06Z'));
    render(<LocalClock/>);
    const zone=Intl.DateTimeFormat().resolvedOptions().timeZone||'UTC';
    expect(screen.getByText(new RegExp(zone.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')))).toBeInTheDocument();
    expect(screen.getByText(/GMT(?:[+-]\d{2}:\d{2})?/)).toBeInTheDocument();
    const before=screen.getByRole('time').textContent;
    act(()=>{vi.advanceTimersByTime(2000);});
    expect(screen.getByRole('time').textContent).not.toBe(before);
  });
});

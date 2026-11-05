import React from 'react';

/* Original iOS-style tab glyphs for web platforms.
   No Apple-proprietary SF Symbols or Lucide assets are used in the dock. */
const glyphs={
  home:<><path d="m3.5 10.2 8.5-7.1 8.5 7.1v9.1c0 1-.8 1.7-1.7 1.7H5.2c-.9 0-1.7-.7-1.7-1.7z"/><path d="M9.2 21v-7.3h5.6V21"/></>,
  search:<><circle cx="10.7" cy="10.7" r="6.6"/><path d="m15.6 15.6 5.2 5.2"/></>,
  how:<><path d="m3.5 6 1.7 1.7 2.7-3.1M11 6h9.5M3.5 13 5.2 14.7 7.9 11.6M11 13h9.5M3.5 20l1.7 1.2 2.7-3.1M11 20h9.5"/></>,
  faq:<><circle cx="12" cy="12" r="9.1"/><path d="M9.2 9.1a2.95 2.95 0 0 1 5.6 1.3c0 2-2.8 2.4-2.8 4.5"/><circle cx="12" cy="18" r=".55" fill="currentColor" stroke="none"/></>,
  about:<><circle cx="12" cy="12" r="9.1"/><path d="M12 11v6.2"/><circle cx="12" cy="7.4" r=".7" fill="currentColor" stroke="none"/></>,
  account:<><circle cx="12" cy="8" r="3.9"/><path d="M4.6 20.3c.5-4 3.4-6 7.4-6s6.9 2 7.4 6"/></>,
  dashboard:<><rect x="3" y="3" width="8" height="8" rx="1.7"/><rect x="13" y="3" width="8" height="8" rx="1.7"/><rect x="3" y="13" width="8" height="8" rx="1.7"/><rect x="13" y="13" width="8" height="8" rx="1.7"/></>,
  new:<><circle cx="12" cy="12" r="9.1"/><path d="M12 7v10M7 12h10"/></>,
  orders:<><path d="M7 3.2h7.8l3.6 3.7v13.5c0 .7-.6 1.4-1.4 1.4H7c-.8 0-1.4-.7-1.4-1.4V4.6c0-.8.6-1.4 1.4-1.4Z"/><path d="M14.6 3.5v4h3.8M9 12h6M9 16h6"/></>,
  approve:<><path d="M12 2.5 20 6v5.6c0 5.1-3 8.2-8 10-5-1.8-8-4.9-8-10V6z"/><path d="m8.4 12.2 2.5 2.5 4.9-5"/></>,
  activity:<><path d="M3 12h4.2l2.5-6 4.2 12 2.7-6H21"/></>,
};
export default function IosDockIcon({name,active=false}){
  const glyph=glyphs[name];
  if(!glyph)return null;
  return <svg className="ios-dock-icon" data-icon-style="ios"
    viewBox="0 0 24 24" width="22" height="22" fill="none"
    stroke="currentColor" strokeWidth={active?2.05:1.85}
    strokeLinecap="round" strokeLinejoin="round"
    aria-hidden="true" focusable="false">{glyph}</svg>;
}

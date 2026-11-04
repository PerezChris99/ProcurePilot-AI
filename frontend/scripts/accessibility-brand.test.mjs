import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {dirname,resolve} from 'node:path';
import test from 'node:test';
import assert from 'node:assert/strict';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const styles=readFileSync(resolve(root,'src/styles/accessibility-brand.css'),'utf8');
const layout=readFileSync(resolve(root,'src/styles/layout-refinement.css'),'utf8');
const main=readFileSync(resolve(root,'src/main.jsx'),'utf8');
const landing=readFileSync(resolve(root,'src/pages/LandingPage.jsx'),'utf8');
const dock=readFileSync(resolve(root,'src/components/layout/MobileDock.jsx'),'utf8');
const dockIcons=readFileSync(resolve(root,'src/components/layout/IosDockIcon.jsx'),'utf8');
const navigation=readFileSync(resolve(root,'src/components/layout/navigation.js'),'utf8');
const publicLayout=readFileSync(resolve(root,'src/components/layout/PublicLayout.jsx'),'utf8');

function luminance(hex){
  const color=hex.replace('#','');
  assert.match(color,/^[0-9a-f]{6}$/i);
  const channels=[0,2,4].map(i=>parseInt(color.slice(i,i+2),16)/255);
  const [r,g,b]=channels.map(value=>value<=.04045?value/12.92:((value+.055)/1.055)**2.4);
  return .2126*r+.7152*g+.0722*b;
}
function contrast(a,b){
  const [bright,dark]=[luminance(a),luminance(b)].sort((a,b)=>b-a);
  return (bright+.05)/(dark+.05);
}

test('brand yellow, navy and text color pairs reach strong reading contrast',()=>{
  // WCAG contrast formula: normal text minimum 4.5:1; these brand pairs
  // intentionally target >=7:1 where possible.
  const pairs=[
    ['Navy on honey','#0B1B3D','#FFD66B',7],
    ['Yellow ink on warm tint','#704D00','#FFF5D7',7],
    ['Normal paragraph on white','#425570','#FFFFFF',7],
    ['Mobile tab text on white','#3E536B','#FFFFFF',7],
    // Links meet WCAG AA 4.5:1, but the brighter on-brand blue is not AAA.
    ['Link blue on white','#075CA9','#FFFFFF',4.5],
    ['White on navy','#FFFFFF','#0B1B3D',7],
  ];
  for(const [name,textColor,surface,minimum] of pairs){
    assert.ok(contrast(textColor,surface)>=minimum,
      name+' contrast was '+contrast(textColor,surface).toFixed(2)+':1, expected '+minimum+':1');
  }
});

test('accessibility typography overrides load after prior theme layers',()=>{
  assert.match(main,/import '\.\/styles\/fintech-polish\.css';\s*import '\.\/styles\/accessibility-brand\.css';/);
  assert.match(styles,/:root\s*\{[^}]*font-size:16px/);
  for(const selector of [
    '.site-hero-text>p',
    '.site-faq-item summary',
    '.site-info-card p',
    '.auth-form>label',
    '.app-frame .service-row small',
    '.app-frame .audit-details li',
    '.app-frame .order-card-top h2',
    '.mobile-dock-link',
  ]){
    assert.ok(styles.includes(selector),selector+' should have a readability override');
  }
});

test('yellow remains an intentional, high-contrast accent without decorative underlines',()=>{
  assert.match(styles,/--brand-yellow:#FFD66B/);
  assert.match(styles,/\.site-top-cta\s*\{[^}]*background:#0865cc;[^}]*color:#fff/);
  assert.match(styles,/\.site-button-light\s*\{[^}]*background:var\(--brand-yellow\);[^}]*color:var\(--brand-navy\)/);
  assert.doesNotMatch(styles,/\.site-kicker::before\s*\{[^}]*content:""/);
  assert.doesNotMatch(styles,/background:linear-gradient\(transparent 81%,var\(--brand-yellow\)/);
  assert.match(layout,/\.site-kicker::before\{content:none\}/);
  assert.match(layout,/\.site-hero-text h1 em\{color:#d8efff;background:none;text-decoration:none\}/);
  assert.match(styles,/\.mobile-dock-link\.active::before\{background:#0865cc/);
  assert.match(styles,/@media\(max-width:519px\)/);
  assert.match(styles,/@media\(prefers-reduced-motion:reduce\)/);
});

test('image fills the hero and every CTA belongs to the photographic section',()=>{
  assert.match(main,/import '\.\/styles\/accessibility-brand\.css';\s*import '\.\/styles\/layout-refinement\.css';/);
  assert.match(layout,/--site-gutter:clamp\(16px,2\.4vw,44px\)/);
  assert.match(layout,/\.site-container,\s*\.site-footer-top\s*\{[^}]*width:calc\(100% - 2 \* var\(--site-gutter\)\)/);
  assert.match(layout,/\.site-hero\.site-hero-visual\s*\{[^}]*width:calc\(100% - 2 \* var\(--site-gutter\)\);[^}]*height:510px;\s*min-height:510px/);
  assert.match(layout,/\.site-hero-content\s*\{[^}]*z-index:2/);
  assert.match(landing,/<HeroSlideshow>\s*<div className="site-hero-text">/);
  assert.match(landing,/<div className="site-hero-content">\{children\}<\/div>/);
  assert.match(layout,/\.site-hero-mist\s*\{[^}]*linear-gradient\(90deg,rgba\(5,18,38,\.91\)/);
  assert.match(layout,/@media\(max-width:1279px\)/);
});

test('parallax is bounded and motion-safe; anchor navigation follows user preference',()=>{
  assert.match(landing,/const desktop=window\.matchMedia\('\(min-width: 961px\)'\)/);
  assert.match(landing,/const reduced=window\.matchMedia\('\(prefers-reduced-motion: reduce\)'\)/);
  assert.match(landing,/Math\.max\(-36,Math\.min\(36,/);
  assert.match(landing,/requestAnimationFrame\(paint\)/);
  assert.match(landing,/window\.addEventListener\('scroll',schedule,\{passive:true\}\)/);
  assert.match(layout,/html\{scroll-behavior:smooth\}/);
  assert.match(layout,/@media\(prefers-reduced-motion:reduce\)\s*\{\s*html\{scroll-behavior:auto\}/);
  assert.match(publicLayout,/scrollIntoView\(\{behavior:reduced\?'auto':'smooth'/);
});

test('mobile icons are exclusively original iOS-style SVG glyphs',()=>{
  assert.match(dock,/<IosDockIcon name=\{iosIcon\} active=\{active\}\/>/);
  assert.doesNotMatch(dock,/<Icon\s+size=/);
  assert.match(dockIcons,/data-icon-style="ios"/);
  assert.match(dockIcons,/viewBox="0 0 24 24"/);
  assert.equal((navigation.match(/iosIcon:/g)||[]).length,13);
  assert.match(layout,/\.mobile-dock-link svg\.ios-dock-icon/);
});

test('dashboard metrics use one neutral summary strip, without colored rounded cards',()=>{
  assert.match(layout,/\.dashboard-refined \.metrics-grid\s*\{[^}]*grid-template-columns:repeat\(4,minmax\(0,1fr\)\)/);
  assert.match(layout,/\.dashboard-refined \.metric-card\s*\{[^}]*border:0;\s*border-radius:0;\s*box-shadow:none;/);
  assert.match(layout,/\.dashboard-refined \.metric-card\+\.metric-card\s*\{\s*border-left:1px solid/);
  assert.match(layout,/@media\(max-width:960px\)\s*\{/);
});

import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {dirname,resolve} from 'node:path';
import test from 'node:test';
import assert from 'node:assert/strict';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const styles=readFileSync(resolve(root,'src/styles/accessibility-brand.css'),'utf8');
const main=readFileSync(resolve(root,'src/main.jsx'),'utf8');

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
    ['Navy on honey','#0B1B3D','#FFD66B'],
    ['Yellow ink on warm tint','#704D00','#FFF5D7'],
    ['Normal paragraph on white','#425570','#FFFFFF'],
    ['Mobile tab text on white','#3E536B','#FFFFFF'],
    ['Link blue on white','#075CA9','#FFFFFF'],
    ['White on navy','#FFFFFF','#0B1B3D'],
  ];
  for(const [name,textColor,surface] of pairs){
    assert.ok(contrast(textColor,surface)>=7,
      name+' contrast was '+contrast(textColor,surface).toFixed(2)+':1');
  }
});

test('accessibility typography overrides load after prior theme layers',()=>{
  assert.match(main,/import '\.\/styles\/fintech-polish\.css';\s*import '\.\/styles\/accessibility-brand\.css';/);
  assert.match(styles,/html\s*\{\s*font-size:16px/);
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

test('yellow is used as a readable highlight, not tiny text on white',()=>{
  assert.match(styles,/--brand-yellow:#FFD66B/);
  assert.match(styles,/\.site-top-cta\s*\{[^}]*background:var\(--brand-yellow\);[^}]*color:var\(--brand-navy\)/);
  assert.match(styles,/\.site-hero-text h1 em\s*\{[^}]*background:linear-gradient\([^;]*var\(--brand-yellow\)/);
  assert.match(styles,/\.site-step-number\s*\{[^}]*color:var\(--brand-yellow-ink\);[^}]*background:var\(--brand-yellow-tint\)/);
  assert.match(styles,/\.mobile-dock-link\.active::before\s*\{[^}]*background:var\(--brand-yellow\)/);
  assert.match(styles,/@media\(max-width:519px\)/);
  assert.match(styles,/@media\(prefers-reduced-motion:reduce\)/);
});

import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {dirname,resolve} from 'node:path';
import {test} from 'node:test';
import assert from 'node:assert/strict';

const base=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const vercel=JSON.parse(readFileSync(resolve(base,'vercel.json'),'utf8'));
const netlify=readFileSync(resolve(base,'public/_headers'),'utf8');

test('production hosting policies prevent inline scripts and framing',()=>{
  const settings=vercel.headers.find(item=>item.source==='/(.*)');
  assert.ok(settings,'Vercel must protect all SPA routes');
  const byName=Object.fromEntries(settings.headers.map(item=>[item.key,item.value]));
  const csp=byName['Content-Security-Policy'];
  assert.match(csp,/script-src 'self'/);
  assert.match(csp,/frame-ancestors 'none'/);
  assert.match(csp,/object-src 'none'/);
  assert.match(csp,/connect-src 'self' https:/);
  assert.doesNotMatch(csp,/unsafe-eval|script-src[^;]*unsafe-inline/);
  for(const name of ['X-Frame-Options','X-Content-Type-Options','Strict-Transport-Security','Referrer-Policy']){
    assert.ok(byName[name]);
    assert.ok(netlify.includes(name+': '+byName[name]),'Netlify policy differs: '+name);
  }
  assert.ok(netlify.includes('Content-Security-Policy: '+csp));
});

test('hosting still routes direct SPA URLs to index.html',()=>{
  assert.ok(vercel.rewrites.some(rule=>rule.source==='/(.*)'&&rule.destination==='/index.html'));
  const redirects=readFileSync(resolve(base,'public/_redirects'),'utf8');
  assert.match(redirects,/\/\*\s+\/index\.html\s+200/);
});

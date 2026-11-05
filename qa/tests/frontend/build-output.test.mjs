import assert from 'node:assert/strict';
import {test} from 'node:test';
import {existsSync, readFileSync, readdirSync, statSync} from 'node:fs';
import {dirname, join, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../../..');
const dist = join(root, 'frontend', 'dist');
const assets = join(dist, 'assets');

test('strict build generates HTML, nonempty JavaScript and CSS', () => {
  const htmlPath = join(dist, 'index.html');
  assert.ok(existsSync(htmlPath), 'No Vite index.html');
  const html = readFileSync(htmlPath, 'utf8');
  assert.match(html, /<html\b/i);
  assert.match(html, /<script[^>]+\.js/i);
  assert.ok(existsSync(assets), 'No compiled asset folder');
  const names = readdirSync(assets);
  assert.ok(names.some(name => name.endsWith('.js')), 'Missing JavaScript bundle');
  assert.ok(names.some(name => name.endsWith('.css')), 'Missing compiled stylesheet');
  for (const name of names) {
    assert.ok(statSync(join(assets, name)).size > 0, 'Empty compiled asset');
  }
});

test('built QA bundle uses the safe configured API base, not localhost backend', () => {
  const names = readdirSync(assets).filter(name => name.endsWith('.js'));
  const code = names.map(name => readFileSync(join(assets, name), 'utf8')).join('\n');
  assert.ok(code.includes('/api/v1'), 'Production base path not compiled');
  assert.ok(!code.includes('http://localhost:8000/api/v1'),
    'A public production bundle must not call local backend');
  assert.ok(!code.includes('development-only-change-this-secret'),
    'Backend default JWT secret must not appear in public bundle');
});

test('client-side deep links have a host rewrite configuration', () => {
  assert.ok(
    existsSync(join(root, 'frontend', 'public', '_redirects')) ||
    existsSync(join(root, 'frontend', 'vercel.json')),
    'Missing SPA rewrite/fallback configuration',
  );
});

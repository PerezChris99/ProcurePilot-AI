import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {dirname,resolve} from 'node:path';
import {verifiedSandboxApprovalUrl,redirectToPayPalSandbox} from '../src/services/paypalCheckout.js';

test('PayPal checkout accepts only genuine HTTPS Sandbox approval hosts',()=>{
  const expected='https://www.sandbox.paypal.com/checkoutnow?token=PAYPAL-123';
  assert.equal(verifiedSandboxApprovalUrl(expected),expected);
  for(const unsafe of [
    'https://www.sandbox.paypal.com.evil.example/checkoutnow',
    'http://www.sandbox.paypal.com/checkoutnow',
    'https://www.paypal.com/checkoutnow',
    'https://attacker@www.sandbox.paypal.com/checkoutnow',
    'javascript:alert(1)',
  ]){
    assert.throws(()=>verifiedSandboxApprovalUrl(unsafe));
  }
});

test('checkout redirect navigates current tab immediately after API response',()=>{
  const destinations=[];
  redirectToPayPalSandbox('https://www.sandbox.paypal.com/checkoutnow?token=123',
                         url=>destinations.push(url));
  assert.deepEqual(destinations,
    ['https://www.sandbox.paypal.com/checkoutnow?token=123']);
});

test('purchase order action uses completed create response and home logo scrolls',()=>{
  const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
  const orders=readFileSync(resolve(root,'src/pages/OrdersPage.jsx'),'utf8');
  const publicLayout=readFileSync(resolve(root,'src/components/layout/PublicLayout.jsx'),'utf8');
  assert.match(orders,/onSuccess:\(result,variables\)=>\{if\(variables\.action==='create-payment'\)\{redirectToPayPalSandbox\(result\.approval_url\)/);
  assert.match(publicLayout,/className="site-brand"[^>]*onClick=\{scrollHomeToTop\}/);
  assert.match(publicLayout,/window\.scrollTo\(\{top:0,behavior:reduced\?'auto':'smooth'\}\)/);
});

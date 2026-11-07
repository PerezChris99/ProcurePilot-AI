import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {dirname,resolve} from 'node:path';
import {verifiedSandboxApprovalUrl,reservePayPalSandboxTab,navigatePayPalSandboxTab,closePendingPayPalTab} from '../src/services/paypalCheckout.js';

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

test('checkout reserves one blank tab before async API and detaches opener',()=>{
  const actions=[];
  const tab={
    opener:{},
    closed:false,
    document:{title:'',body:{textContent:''}},
    location:{replace:url=>actions.push(['navigate',url])},
    close:()=>actions.push(['close']),
  };
  const held=reservePayPalSandboxTab(()=>{
    actions.push(['reserve']);
    return tab;
  });
  assert.equal(held,tab);
  assert.equal(tab.opener,null);
  assert.match(tab.document.body.textContent,/Connecting to PayPal Sandbox/);
  assert.equal(navigatePayPalSandboxTab(
    'https://www.sandbox.paypal.com/checkoutnow?token=123',held),true);
  assert.deepEqual(actions,[
    ['reserve'],['navigate','https://www.sandbox.paypal.com/checkoutnow?token=123'],
  ]);
  closePendingPayPalTab(tab);
  assert.deepEqual(actions.at(-1),['close']);
});

test('checkout fails closed when browser refuses to detach window.opener',()=>{
  const actions=[];
  const unsafe={closed:false,close:()=>actions.push('closed')};
  Object.defineProperty(unsafe,'opener',{
    get:()=>({}),set:()=>{throw new Error('opener isolation unavailable')},
  });
  assert.equal(reservePayPalSandboxTab(()=>unsafe),null);
  assert.deepEqual(actions,['closed']);
});

test('popup blockers or closed tabs do not navigate the current application tab',()=>{
  const checkout='https://www.sandbox.paypal.com/checkoutnow?token=123';
  assert.equal(reservePayPalSandboxTab(()=>null),null);
  assert.equal(navigatePayPalSandboxTab(checkout,null),false);
  assert.equal(navigatePayPalSandboxTab(checkout,{closed:true}),false);
  assert.throws(()=>navigatePayPalSandboxTab('https://www.paypal.com/checkoutnow',null));
});

test('purchase order action uses completed create response and home logo scrolls',()=>{
  const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
  const orders=readFileSync(resolve(root,'src/pages/OrdersPage.jsx'),'utf8');
  const publicLayout=readFileSync(resolve(root,'src/components/layout/PublicLayout.jsx'),'utf8');
  assert.match(orders,/checkoutTab\.current=reservePayPalSandboxTab\(\)/);
  assert.match(orders,/navigatePayPalSandboxTab\(result\.approval_url,tab\)/);
  assert.match(orders,/target="_blank" rel="noopener noreferrer" aria-label="Open PayPal in new tab"[^>]*>Open PayPal\s*</);
  assert.doesNotMatch(orders,/window\.location\.assign\(/);
  assert.match(publicLayout,/className="site-brand"[^>]*onClick=\{scrollHomeToTop\}/);
  assert.match(publicLayout,/window\.scrollTo\(\{top:0,behavior:reduced\?'auto':'smooth'\}\)/);
});

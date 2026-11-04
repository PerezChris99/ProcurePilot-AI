'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const {supportsVite7}=require('./check-node-version.cjs');

test('accepts the Vite 7 Node.js version boundaries',()=>{
  for(const version of ['20.19.0','20.20.1','22.12.0','22.16.0','24.0.0']){
    assert.equal(supportsVite7(version),true,version);
  }
});
test('rejects unsupported Node.js runtimes and malformed versions',()=>{
  for(const version of ['18.20.8','19.9.0','20.18.9','21.1.0','22.11.0','v22.11.0','',null,'22.12']){
    assert.equal(supportsVite7(version),false,String(version));
  }
});

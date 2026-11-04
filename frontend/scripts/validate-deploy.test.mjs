import assert from 'node:assert/strict';
import {test} from 'node:test';
import {validateApiBaseUrl} from './validate-deploy.mjs';

test('accepts configured HTTPS and same-origin reverse proxy',()=>{
  assert.equal(validateApiBaseUrl('/api/v1'),'/api/v1');
  assert.equal(validateApiBaseUrl('https://api.example.com/api/v1'),'https://api.example.com/api/v1');
});

for(const raw of [
  undefined,'','http://localhost:8000/api/v1','https://localhost/api/v1',
  'http://api.example.com/api/v1','https://api.example.com/login',
  'https://api.example.com/api/v1?token=secret','https://name:password@api.example.com/api/v1',
]){
  test('rejects missing or unsafe deployment API URL: '+String(raw),()=>{
    assert.throws(()=>validateApiBaseUrl(raw),/VITE_API_BASE_URL/);
  });
}

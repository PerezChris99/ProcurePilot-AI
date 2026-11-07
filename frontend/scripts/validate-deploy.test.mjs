import assert from 'node:assert/strict';
import {test} from 'node:test';
import {validateApiBaseUrl} from './validate-deploy.mjs';

test('accepts only the same-origin FastAPI route for Vercel Services',()=>{
  assert.equal(validateApiBaseUrl('/api/v1'),'/api/v1');
});

for(const raw of [
  undefined,'', ' /api/v1 ', 'http://localhost:8000/api/v1',
  'https://localhost/api/v1', 'https://api.example.com/api/v1',
  'https://procurepilotai.vercel.app/api/v1',
  'http://api.example.com/api/v1', '/api/v2',
  'https://api.example.com/api/v1?token=secret',
  'https://name:password@api.example.com/api/v1',
]){
  test('rejects API base inconsistent with same-origin Services contract: '+String(raw),()=>{
    assert.throws(()=>validateApiBaseUrl(raw),/VITE_API_BASE_URL/);
  });
}

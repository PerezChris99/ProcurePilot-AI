import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {dirname,resolve} from 'node:path';
import test from 'node:test';
import assert from 'node:assert/strict';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const original=readFileSync(resolve(root,'src/styles/index.css'),'utf8');
const overrides=readFileSync(resolve(root,'src/styles/features.css'),'utf8');

test('offer price and Create PO have independent intrinsic-width columns',()=>{
  assert.doesNotMatch(original,/\.offer-row\{[^}]*grid-template-columns:minmax\(0,1fr\) auto 25px/);
  assert.match(original,/\.offer-row\{[^}]*grid-template-columns:minmax\(0,1fr\) max-content max-content/);
  assert.match(overrides,/\.offer-row>strong:nth-child\(2\)\{white-space:nowrap/);
  assert.match(overrides,/\.offer-row>\.offer-actions\{min-width:max-content/);
});

test('offer action controls move below the price on narrow product cards',()=>{
  assert.match(overrides,/\.offer-list\{container-type:inline-size\}/);
  assert.match(overrides,/@container \(max-width:590px\)/);
  assert.match(overrides,/\.offer-row>\.offer-actions\{grid-column:1\/-1/);
});

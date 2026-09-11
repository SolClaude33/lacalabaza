import assert from 'node:assert/strict';
import test from 'node:test';

import { createRuntimeConfig, createRuntimeConfigSource } from '../scripts/build-helpers.mjs';

const VALID_CA = '0xAbCdEf0123456789aBCdEf0123456789ABcDef01';

test('empty public environment produces safe empty launch configuration', () => {
  assert.deepEqual(createRuntimeConfig({}), {
    buyUrl: '',
    xUrl: '',
    contractAddress: ''
  });
});

test('valid public launch values remain independent and preserve CA casing', () => {
  const config = createRuntimeConfig({
    PUBLIC_BUY_URL: 'https://dex.example/swap?token=calabaza',
    PUBLIC_X_URL: 'https://x.com/calabaza',
    PUBLIC_TOKEN_CA: VALID_CA
  });

  assert.equal(config.buyUrl, 'https://dex.example/swap?token=calabaza');
  assert.equal(config.xUrl, 'https://x.com/calabaza');
  assert.equal(config.contractAddress, VALID_CA);
});

test('runtime config source serializes data without executable interpolation', () => {
  const source = createRuntimeConfigSource({ PUBLIC_X_URL: 'https://x.com/calabaza' });
  assert.match(source, /^window\.__LA_CALABAZA_CONFIG__ = Object\.freeze\(/);
  assert.match(source, /"xUrl": "https:\/\/x\.com\/calabaza"/);
  assert.doesNotMatch(source, /eval|innerHTML/);
});

for (const [variableName, value] of [
  ['PUBLIC_BUY_URL', 'javascript:alert(1)'],
  ['PUBLIC_X_URL', 'ftp://x.example/profile'],
  ['PUBLIC_TOKEN_CA', '0x1234']
]) {
  test(`invalid ${variableName} fails closed`, () => {
    assert.throws(
      () => createRuntimeConfig({ [variableName]: value }),
      new RegExp(variableName)
    );
  });
}

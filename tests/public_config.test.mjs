import assert from 'node:assert/strict';
import test from 'node:test';

import { applyPublicConfig, resolvePublicConfig } from '../public-config.mjs';

class FakeClassList {
  constructor(initial = []) {
    this.values = new Set(initial);
  }
  add(value) { this.values.add(value); }
  remove(value) { this.values.delete(value); }
  contains(value) { return this.values.has(value); }
}

class FakeElement {
  constructor(dataset = {}, attributes = {}) {
    this.dataset = { ...dataset };
    this.attributes = new Map(Object.entries(attributes));
    this.classList = new FakeClassList(['pending-action']);
    this.textContent = '';
    this.disabled = true;
  }
  setAttribute(name, value) { this.attributes.set(name, String(value)); }
  removeAttribute(name) { this.attributes.delete(name); }
  getAttribute(name) { return this.attributes.get(name) ?? null; }
}

function makeRoot({ links = [], fields = [], copyButtons = [] } = {}) {
  return {
    querySelectorAll(selector) {
      if (selector === '[data-link]') return links;
      if (selector === '[data-config="contractAddress"]') return fields;
      if (selector === '[data-copy-contract]') return copyButtons;
      return [];
    }
  };
}

const VALID_CA = '0xAbCdEf0123456789aBCdEf0123456789ABcDef01';

test('configured Buy anchors share one URL while X remains independent', () => {
  const headerBuy = new FakeElement({ link: 'buy' });
  const footerBuy = new FakeElement({ link: 'buy' });
  const xLink = new FakeElement({ link: 'x' });
  const contractFields = [new FakeElement(), new FakeElement()];
  const copyButton = new FakeElement();

  applyPublicConfig(makeRoot({
    links: [headerBuy, footerBuy, xLink],
    fields: contractFields,
    copyButtons: [copyButton]
  }), {
    buyUrl: 'https://dex.example/calabaza',
    xUrl: 'https://x.com/calabaza',
    contractAddress: VALID_CA
  });

  assert.equal(headerBuy.getAttribute('href'), 'https://dex.example/calabaza');
  assert.equal(footerBuy.getAttribute('href'), headerBuy.getAttribute('href'));
  assert.equal(xLink.getAttribute('href'), 'https://x.com/calabaza');
  for (const link of [headerBuy, footerBuy, xLink]) {
    assert.equal(link.getAttribute('target'), '_blank');
    assert.equal(link.getAttribute('rel'), 'noopener noreferrer');
    assert.equal(link.getAttribute('aria-disabled'), null);
    assert.equal(link.classList.contains('pending-action'), false);
  }
  assert.deepEqual(contractFields.map((field) => field.textContent), [VALID_CA, VALID_CA]);
  assert.equal(copyButton.disabled, false);
  assert.equal(copyButton.dataset.copyValue, VALID_CA);
});

test('missing or unsafe values remove stale navigation and show SOON', () => {
  const staleBuy = new FakeElement(
    { link: 'buy' },
    { href: 'https://stale.example', target: '_blank', rel: 'noreferrer' }
  );
  const unsafeX = new FakeElement({ link: 'x' }, { href: 'https://stale-x.example' });
  const contractField = new FakeElement();
  const copyButton = new FakeElement();
  copyButton.disabled = false;

  applyPublicConfig(makeRoot({
    links: [staleBuy, unsafeX],
    fields: [contractField],
    copyButtons: [copyButton]
  }), {
    buyUrl: '',
    xUrl: 'javascript:alert(1)',
    contractAddress: '0x1234'
  });

  for (const link of [staleBuy, unsafeX]) {
    assert.equal(link.getAttribute('href'), null);
    assert.equal(link.getAttribute('target'), null);
    assert.equal(link.getAttribute('rel'), null);
    assert.equal(link.getAttribute('aria-disabled'), 'true');
    assert.equal(link.classList.contains('pending-action'), true);
  }
  assert.equal(contractField.textContent, 'SOON');
  assert.equal(copyButton.disabled, true);
  assert.equal(copyButton.dataset.copyValue, '');
});

test('runtime resolver accepts only HTTP URLs and exact EVM addresses', () => {
  assert.deepEqual(resolvePublicConfig({
    buyUrl: 'ftp://dex.example',
    xUrl: 'https://x.com/calabaza',
    contractAddress: VALID_CA
  }), {
    buyUrl: '',
    xUrl: 'https://x.com/calabaza',
    contractAddress: VALID_CA
  });
});

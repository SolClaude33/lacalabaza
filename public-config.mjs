const HTTP_PROTOCOLS = new Set(['http:', 'https:']);
const EVM_ADDRESS = /^0x[a-fA-F0-9]{40}$/;

function normalizePublicUrl(value) {
  if (typeof value !== 'string' || !value.trim()) return '';
  try {
    const url = new URL(value.trim());
    return HTTP_PROTOCOLS.has(url.protocol) ? url.href : '';
  } catch {
    return '';
  }
}

function normalizeContractAddress(value) {
  if (typeof value !== 'string') return '';
  const address = value.trim();
  return EVM_ADDRESS.test(address) ? address : '';
}

export function resolvePublicConfig(rawConfig = {}) {
  return {
    buyUrl: normalizePublicUrl(rawConfig.buyUrl),
    xUrl: normalizePublicUrl(rawConfig.xUrl),
    contractAddress: normalizeContractAddress(rawConfig.contractAddress)
  };
}

function applyLink(link, url) {
  if (url) {
    link.setAttribute('href', url);
    link.setAttribute('target', '_blank');
    link.setAttribute('rel', 'noopener noreferrer');
    link.removeAttribute('aria-disabled');
    link.removeAttribute('data-pending');
    link.classList.remove('pending-action');
    return;
  }

  link.removeAttribute('href');
  link.removeAttribute('target');
  link.removeAttribute('rel');
  link.setAttribute('aria-disabled', 'true');
  link.setAttribute('data-pending', 'true');
  link.classList.add('pending-action');
}

export function applyPublicConfig(root, rawConfig = {}) {
  const config = resolvePublicConfig(rawConfig);

  root.querySelectorAll('[data-link]').forEach((link) => {
    const url = link.dataset.link === 'buy' ? config.buyUrl : config.xUrl;
    applyLink(link, url);
  });

  root.querySelectorAll('[data-config="contractAddress"]').forEach((field) => {
    field.textContent = config.contractAddress || 'SOON';
  });

  root.querySelectorAll('[data-copy-contract]').forEach((button) => {
    button.disabled = !config.contractAddress;
    button.dataset.copyValue = config.contractAddress;
  });

  return config;
}

if (typeof document !== 'undefined') {
  const rawConfig = globalThis.__LA_CALABAZA_CONFIG__ || {};
  globalThis.__LA_CALABAZA_PUBLIC_CONFIG__ = applyPublicConfig(document, rawConfig);
}

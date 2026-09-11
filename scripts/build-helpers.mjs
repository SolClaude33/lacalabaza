const URL_VARIABLES = Object.freeze({
  PUBLIC_BUY_URL: 'buyUrl',
  PUBLIC_X_URL: 'xUrl'
});

function readPublicHttpUrl(environment, variableName) {
  const rawValue = environment[variableName];
  if (typeof rawValue !== 'string' || !rawValue.trim()) return '';

  try {
    const url = new URL(rawValue.trim());
    if (url.protocol !== 'https:' && url.protocol !== 'http:') {
      throw new Error('unsupported protocol');
    }
    return url.href;
  } catch {
    throw new Error(`${variableName} must be a valid http:// or https:// URL`);
  }
}

function readPublicEvmAddress(environment, variableName) {
  const rawValue = environment[variableName];
  if (typeof rawValue !== 'string' || !rawValue.trim()) return '';

  const address = rawValue.trim();
  if (!/^0x[a-fA-F0-9]{40}$/.test(address)) {
    throw new Error(`${variableName} must be a valid EVM address`);
  }
  return address;
}

export function createRuntimeConfig(environment) {
  const config = Object.fromEntries(
    Object.entries(URL_VARIABLES).map(([variableName, key]) => [
      key,
      readPublicHttpUrl(environment, variableName)
    ])
  );

  config.contractAddress = readPublicEvmAddress(environment, 'PUBLIC_TOKEN_CA');
  return config;
}

export function createRuntimeConfigSource(environment) {
  const config = createRuntimeConfig(environment);
  return `window.__LA_CALABAZA_CONFIG__ = Object.freeze(${JSON.stringify(config, null, 2)});\n`;
}

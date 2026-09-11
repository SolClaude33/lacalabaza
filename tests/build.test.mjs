import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { readFile } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import { join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const DIST = join(ROOT, 'dist');
const VALID_CA = '0xAbCdEf0123456789aBCdEf0123456789ABcDef01';

function runBuild(extraEnvironment = {}) {
  return spawnSync(process.execPath, ['scripts/build.mjs'], {
    cwd: ROOT,
    env: { ...process.env, ...extraEnvironment },
    encoding: 'utf8'
  });
}

test('production build emits typed public config and only runtime files', async () => {
  const result = runBuild({
    PUBLIC_BUY_URL: 'https://dex.example/calabaza',
    PUBLIC_X_URL: 'https://x.com/calabaza',
    PUBLIC_TOKEN_CA: VALID_CA
  });
  assert.equal(result.status, 0, result.stderr || result.stdout);

  const runtimeConfig = await readFile(join(DIST, 'runtime-config.js'), 'utf8');
  assert.match(runtimeConfig, /"buyUrl": "https:\/\/dex\.example\/calabaza"/);
  assert.match(runtimeConfig, /"xUrl": "https:\/\/x\.com\/calabaza"/);
  assert.match(runtimeConfig, new RegExp(VALID_CA));

  const html = await readFile(join(DIST, 'index.html'), 'utf8');
  assert.match(html, /<script src="\.\/runtime-config\.js"><\/script>/);
  assert.match(html, /<script type="module" src="\.\/public-config\.mjs"><\/script>/);

  for (const runtimeFile of [
    'styles.css',
    'script.js',
    'public-config.mjs',
    'favicon.ico',
    'assets/hero-kittens.png',
    'assets/story-kittens-stage.png',
    'assets/video-01.mp4'
  ]) {
    assert.equal(existsSync(join(DIST, runtimeFile)), true, `missing ${runtimeFile}`);
  }

  for (const excluded of [
    'qa',
    'tests',
    'assets/manifest.json',
    'assets/character-shy-card.png',
    'assets/character-drama-face.png'
  ]) {
    assert.equal(existsSync(join(DIST, excluded)), false, `unexpected ${excluded}`);
  }
});

test('production build rejects an unsafe public URL', () => {
  const result = runBuild({ PUBLIC_X_URL: 'javascript:alert(1)' });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /PUBLIC_X_URL/);
});

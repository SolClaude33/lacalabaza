import { cp, mkdir, rm, writeFile } from 'node:fs/promises';
import { join } from 'node:path';

import { createRuntimeConfigSource } from './build-helpers.mjs';

const root = process.cwd();
const dist = join(root, 'dist');
const runtimeConfigSource = createRuntimeConfigSource(process.env);

const runtimeFiles = [
  'index.html',
  'styles.css',
  'script.js',
  'public-config.mjs',
  'favicon.ico'
];

const runtimeAssets = [
  'favicon.svg',
  'hero-kittens.png',
  'hero-background.png',
  'hero-dance-alpha.webm',
  'hero-dance-poster.png',
  'character-shy-face.png',
  'character-drama-hat-face.png',
  'character-brain-face.png',
  'story-kittens-stage.png',
  'video-01.mp4',
  'video-02.mp4',
  'video-03.mp4',
  'tiktok-poster-01.png',
  'tiktok-poster-02.png',
  'tiktok-poster-03.png'
];

await rm(dist, { recursive: true, force: true });
await mkdir(join(dist, 'assets'), { recursive: true });

for (const file of runtimeFiles) {
  await cp(join(root, file), join(dist, file));
}
for (const asset of runtimeAssets) {
  await cp(join(root, 'assets', asset), join(dist, 'assets', asset));
}

await writeFile(join(dist, 'runtime-config.js'), runtimeConfigSource, 'utf8');
console.log(`Built ${runtimeFiles.length + runtimeAssets.length + 1} runtime files in dist/.`);

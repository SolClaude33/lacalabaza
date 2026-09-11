# LA CALABAZA

Static, dependency-free landing page for the LA CALABAZA meme project on BNB Chain.

## Preview

Open `index.html` directly, or serve the folder locally:

```bash
python -m http.server 4173 --bind 127.0.0.1
```

Then visit `http://127.0.0.1:4173/`.

## Verification

```bash
npm test
npm run build
```

The production output is written to `dist/`. Preview that exact build with:

```bash
python -m http.server 4173 --bind 127.0.0.1 --directory dist
```

## Public launch configuration

The Vercel build reads three public environment variables:

| Variable | Used by | Accepted value | Empty fallback |
| --- | --- | --- | --- |
| `PUBLIC_TOKEN_CA` | Hero and footer CA | `0x` + 40 hexadecimal characters | `SOON` |
| `PUBLIC_X_URL` | Navbar, mobile menu and footer X buttons | Explicit `http://` or `https://` URL | Disabled |
| `PUBLIC_BUY_URL` | Navbar, mobile menu and footer Buy buttons | Explicit `http://` or `https://` URL | Disabled |

These values are embedded into browser JavaScript and are **public, not secrets**. Invalid addresses, malformed URLs and non-HTTP schemes make the build fail. Use `.env.example` as the variable checklist; set the real values in Vercel before the production deployment.

## Current placeholders

The contract address, Buy destination, X profile and chart destination remain intentionally unavailable until verified. The CA renders as `SOON`; the environment-controlled links have no `href` while empty. The three local videos and the cited original TikTok post are active. The site does not request wallet access or signatures.

## Files

- `index.html` — semantic page structure and copy
- `styles.css` — responsive visual system and motion
- `script.js` — user-triggered 128 BPM dance mode, pending-link feedback, and reveal behavior
- `public-config.mjs` — browser-side typed configuration binding
- `runtime-config.js` — safe empty defaults for direct local preview
- `scripts/` — dependency-free static build and environment validation
- `assets/` — generated production artwork and provenance manifest
- `tests/` — dependency-free acceptance tests

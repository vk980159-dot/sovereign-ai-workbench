# 00. Frontend Architecture Overview
**Status:** [VERIFIED]

## Vanilla Single-Page Architecture
The frontend is built strictly with **HTML5, CSS3, and ES6 JavaScript** in `frontend/index.html`, `login.html`, and `register.html`.

## Zero-CDN Air-Gap Guarantee
- Contains **zero external script or stylesheet CDN dependencies** (no React, Vue, jQuery, Bootstrap, or Tailwind CDNs).
- Renders and functions 100% reliably in a completely offline air-gapped network environment.
- Communicates with the FastAPI backend over REST APIs (`/api/*`) and persistent WebSockets (`/ws/*`).

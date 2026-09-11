# 10. HTTP Security Response Headers
**Status:** [VERIFIED]

## 1. File Path
`backend/app/main.py`: Security Headers Middleware

## 2. Injected Headers
- `X-Frame-Options: DENY`: Defends against clickjacking by preventing embedding in iframes.
- `X-Content-Type-Options: nosniff`: Prevents MIME-type sniffing attacks.
- `X-XSS-Protection: 1; mode=block`: Activates browser XSS filters.
- `Content-Security-Policy`: Restricts script execution to local origin; disallows inline malicious injections.
- `Referrer-Policy: strict-origin-when-cross-origin`: Prevents leakage of internal URL paths.

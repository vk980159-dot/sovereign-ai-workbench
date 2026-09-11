# 11. Sliding-Window Rate Limiting
**Status:** [VERIFIED]

## 1. File Path
`backend/app/security/rate_limiter.py`: `SlidingWindowRateLimiter`, `RateLimitMiddleware`

## 2. Mechanism & Thresholds
- **Algorithm:** In-memory sliding time window with thread-safe lock (`threading.Lock`).
- **Standard Threshold:** 60 requests per minute per client IP.
- **Burst Allowance:** 10 requests.
- **IP Detection:** Uses `Request.client.host`, with fallback to `CF-Connecting-IP` in Public Share Mode.

## 3. Response
Requests exceeding the sliding window threshold are intercepted before reaching route handlers, returning HTTP 429 Too Many Requests with `{ "error": "Rate limit exceeded. Maximum 60 requests per minute." }`.

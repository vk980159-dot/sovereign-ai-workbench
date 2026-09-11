# 06. OAuth Integration (`backend/app/security/auth.py` & `api/router.py`)
**Status:** [PARTIALLY VERIFIED]

## 1. File Paths
`backend/app/security/auth.py`, `backend/app/api/router.py`

## 2. Purpose & Supported Providers
Provides optional federated login via:
1. **Google OAuth2** (`/api/auth/google/authorize`, `/api/auth/google/callback`)
2. **GitHub OAuth2** (`/api/auth/github/authorize`, `/api/auth/github/callback`)

## 3. Implementation Status
- **Code Status:** [VERIFIED] Full authorization code exchange, state validation, and account linking in `auth.db:linked_accounts`.
- **Air-Gap Behavior:** [VERIFIED] In pure air-gapped environments (`LOCAL_AIR_GAPPED`), OAuth fails closed gracefully. Local authentication operates 100% offline.
- **Limitation:** OAuth requires external internet connectivity to reach Google/GitHub token endpoints; strictly optional for on-premise deployments.

# 08. PII Redaction Engine
**Status:** [VERIFIED]

## 1. File Path
`backend/app/security/pii_redactor.py`: `PIIRedactor`

## 2. Redacted Identifiers
- Indian Aadhaar Numbers (`\d{4}\s\d{4}\s\d{4}`) -> `[REDACTED_AADHAAR]`
- Indian PAN Cards (`[A-Z]{5}[0-9]{4}[A-Z]{1}`) -> `[REDACTED_PAN]`
- US Social Security Numbers (`\d{3}-\d{2}-\d{4}`) -> `[REDACTED_SSN]`
- Email Addresses -> `[REDACTED_EMAIL]`
- Phone Numbers -> `[REDACTED_PHONE]`
Protects against indexing confidential operator personal data into RAG.

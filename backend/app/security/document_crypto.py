"""
Sovereign Document Storage Encryption Engine (AES-256-GCM).
SIH26117 - MRPL Sovereign AI Workbench.

Ensures that confidential industrial documents stored on the server disk are
never stored in plaintext. In the event of physical server drive theft or unauthorized
filesystem reads, confidential documents remain protected by authenticated AES-256-GCM.

Production-Grade KMS / HSM Migration Architecture:
--------------------------------------------------
In production MRPL refinery infrastructure, this software-level key management can be
seamlessly swapped for an on-premise Hardware Security Module (HSM) or Enterprise KMS:
1. PKCS#11 API: Integrates directly with Thales Luna, Utimaco, or NitroKey HSMs.
2. HashiCorp Vault Transit Engine: Envelope encryption with centralized key rotation,
   dynamic access policies, and tamper-evident unseal keys.
3. TPM 2.0 (Trusted Platform Module): Sealing the master encryption key to the hardware's
   Platform Configuration Registers (PCRs), ensuring keys cannot be extracted if moved
   to different server hardware.
"""

import os
import hashlib
import secrets
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from Cryptodome.Cipher import AES

MAGIC_HEADER = b"MRPL_SOV_AES256"  # 15 bytes
VERSION_BYTE = b"\x01"            # 1 byte
HEADER_TOTAL = MAGIC_HEADER + VERSION_BYTE  # 16 bytes
SALT_LEN = 16
NONCE_LEN = 12
TAG_LEN = 16

_CACHED_MASTER_KEY: Optional[bytes] = None


def _resolve_master_key() -> bytes:
    """
    Resolves the 256-bit AES master encryption key.
    Key precedence:
    1. Environment variable: STORAGE_ENCRYPTION_KEY
    2. Secure keyfile on server storage: .storage_key (generated if not present)
    Never uses a hardcoded fallback.
    """
    global _CACHED_MASTER_KEY
    if _CACHED_MASTER_KEY is not None:
        return _CACHED_MASTER_KEY

    env_key = os.getenv("STORAGE_ENCRYPTION_KEY", "").strip()
    if env_key:
        # Derive 32-byte key from passphrase using SHA-256
        _CACHED_MASTER_KEY = hashlib.sha256(env_key.encode("utf-8")).digest()
        return _CACHED_MASTER_KEY

    # Auto-generate or load from server persistent secrets directory
    base_dir = Path(__file__).resolve().parent.parent.parent
    key_dir = base_dir / "data" / "secrets"
    key_dir.mkdir(parents=True, exist_ok=True)
    key_file = key_dir / ".storage_master_key.bin"

    if key_file.exists():
        with open(key_file, "rb") as f:
            raw_key = f.read()
            if len(raw_key) == 32:
                _CACHED_MASTER_KEY = raw_key
                return _CACHED_MASTER_KEY

    # Generate cryptographically secure 256-bit random key
    new_key = secrets.token_bytes(32)
    try:
        with open(key_file, "wb") as f:
            f.write(new_key)
        try:
            os.chmod(key_file, 0o600)
        except Exception:
            pass
    except Exception as e:
        print(f"[DOCUMENT CRYPTO WARNING]: Could not persist master key file: {e}")

    _CACHED_MASTER_KEY = new_key
    return _CACHED_MASTER_KEY


def get_storage_key_fingerprint() -> str:
    """
    Returns a SHA-256 fingerprint (first 16 hex chars) of the active master key
    for verification and audit logging without disclosing the secret key.
    """
    key = _resolve_master_key()
    return hashlib.sha256(key).hexdigest()[:16].upper()


def encrypt_bytes(data: bytes) -> bytes:
    """
    Encrypts arbitrary byte payload using AES-256-GCM.
    Payload format: [HEADER: 16B][SALT: 16B][NONCE: 12B][TAG: 16B][CIPHERTEXT: NB]
    """
    master_key = _resolve_master_key()
    salt = secrets.token_bytes(SALT_LEN)
    
    # Subkey derivation per document using HKDF-like HKDF-SHA256
    derived_key = hashlib.pbkdf2_hmac("sha256", master_key, salt, iterations=10_000, dklen=32)
    
    nonce = secrets.token_bytes(NONCE_LEN)
    cipher = AES.new(derived_key, AES.MODE_GCM, nonce=nonce)
    cipher.update(HEADER_TOTAL)  # Authenticate header as AAD
    
    ciphertext, tag = cipher.encrypt_and_digest(data)
    
    return HEADER_TOTAL + salt + nonce + tag + ciphertext


def decrypt_bytes(encrypted_data: bytes) -> bytes:
    """
    Decrypts an AES-256-GCM encrypted payload and validates cryptographic integrity.
    Raises ValueError if payload is tampered, corrupted, or key is invalid.
    """
    if len(encrypted_data) < len(HEADER_TOTAL) + SALT_LEN + NONCE_LEN + TAG_LEN:
        raise ValueError("Encrypted payload is corrupted: length shorter than header minimum.")

    header = encrypted_data[:len(HEADER_TOTAL)]
    if header != HEADER_TOTAL:
        raise ValueError("Encrypted document header mismatch or unsupported crypto version.")

    offset = len(HEADER_TOTAL)
    salt = encrypted_data[offset:offset + SALT_LEN]
    offset += SALT_LEN
    nonce = encrypted_data[offset:offset + NONCE_LEN]
    offset += NONCE_LEN
    tag = encrypted_data[offset:offset + TAG_LEN]
    offset += TAG_LEN
    ciphertext = encrypted_data[offset:]

    master_key = _resolve_master_key()
    derived_key = hashlib.pbkdf2_hmac("sha256", master_key, salt, iterations=10_000, dklen=32)

    cipher = AES.new(derived_key, AES.MODE_GCM, nonce=nonce)
    cipher.update(HEADER_TOTAL)

    try:
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        return plaintext
    except Exception as e:
        raise ValueError("Cryptographic verification failed: document integrity corrupted or invalid key.") from e


def encrypt_file(source_path: Path | str, target_encrypted_path: Path | str) -> Dict[str, Any]:
    """
    Reads a plaintext document from source_path, encrypts it with AES-256-GCM,
    and writes the encrypted blob to target_encrypted_path.
    Returns metadata dict with plaintext and ciphertext hashes.
    """
    source_path = Path(source_path)
    target_encrypted_path = Path(target_encrypted_path)
    target_encrypted_path.parent.mkdir(parents=True, exist_ok=True)

    with open(source_path, "rb") as f:
        plaintext = f.read()

    sha256_plaintext = hashlib.sha256(plaintext).hexdigest()
    encrypted_blob = encrypt_bytes(plaintext)
    sha256_ciphertext = hashlib.sha256(encrypted_blob).hexdigest()

    with open(target_encrypted_path, "wb") as f:
        f.write(encrypted_blob)

    return {
        "source_filename": source_path.name,
        "encrypted_path": str(target_encrypted_path),
        "plaintext_size_bytes": len(plaintext),
        "ciphertext_size_bytes": len(encrypted_blob),
        "plaintext_sha256": sha256_plaintext,
        "ciphertext_sha256": sha256_ciphertext,
        "key_fingerprint": get_storage_key_fingerprint(),
        "algorithm": "AES-256-GCM",
        "kdf": "PBKDF2-HMAC-SHA256 (10,000 rounds)"
    }


def decrypt_file(encrypted_path: Path | str, target_plaintext_path: Path | str) -> Dict[str, Any]:
    """
    Reads an encrypted document from encrypted_path, decrypts it, and writes
    the plaintext to target_plaintext_path.
    """
    encrypted_path = Path(encrypted_path)
    target_plaintext_path = Path(target_plaintext_path)
    target_plaintext_path.parent.mkdir(parents=True, exist_ok=True)

    with open(encrypted_path, "rb") as f:
        encrypted_blob = f.read()

    plaintext = decrypt_bytes(encrypted_blob)
    sha256_plaintext = hashlib.sha256(plaintext).hexdigest()

    with open(target_plaintext_path, "wb") as f:
        f.write(plaintext)

    return {
        "decrypted_path": str(target_plaintext_path),
        "size_bytes": len(plaintext),
        "plaintext_sha256": sha256_plaintext,
        "key_fingerprint": get_storage_key_fingerprint()
    }

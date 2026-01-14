# Phase 0: Research & Technical Decisions

**Date**: 2026-01-14  
**Purpose**: Resolve all NEEDS CLARIFICATION items from Technical Context before Phase 1 design

## Research Areas

### 1. Salt Encryption Method

**Question**: What encryption method should be used to store salts securely?

**Decision**: Use Fernet (symmetric encryption) from Python's cryptography library with a machine-specific derived key

**Rationale**:
- Fernet provides authenticated encryption (AES-128 CBC + HMAC)
- Part of Python's cryptography library (well-maintained, security-audited)
- Simple API: `Fernet.generate_key()`, `f.encrypt()`, `f.decrypt()`
- Authenticated encryption prevents tampering
- Environment variable approach enables portability across CI/CD nodes
- Key can be stored in CI/CD secrets manager (e.g., GitHub Secrets, GitLab CI variables)

**Implementation Pattern**:
```python
from cryptography.fernet import Fernet
import os
import secrets
import base64

# Get or generate encryption key from environment
def get_encryption_key() -> bytes:
    key_b64 = os.environ.get('TF_ANALYZER_SALT_KEY')
    if key_b64:
        return base64.urlsafe_b64decode(key_b64)
    # Generate new key and warn user to save it
    key = Fernet.generate_key()
    print("="*70, file=sys.stderr)
    print("WARNING: TF_ANALYZER_SALT_KEY environment variable not set!", file=sys.stderr)
    print("="*70, file=sys.stderr)
    print("Generated new encryption key (save this securely):", file=sys.stderr)
    print(f"\n  export TF_ANALYZER_SALT_KEY={key.decode()}\n", file=sys.stderr)
    print("SECURITY WARNINGS:", file=sys.stderr)
    print("  - Store this key in a secure location (password manager, CI secrets)", file=sys.stderr)
    print("  - DO NOT commit this key to version control", file=sys.stderr)
    print("  - This key will be visible in terminal history and CI logs", file=sys.stderr)
    print("  - Without this key, you cannot decrypt/reuse the salt file", file=sys.stderr)
    print("  - For CI/CD: Store in GitHub Secrets, GitLab CI variables, etc.", file=sys.stderr)
    print("="*70, file=sys.stderr)
    return key

# Store salt with encryption
def store_salt(salt_data: bytes, position_seed: bytes, output_path: str):
    key = get_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(salt_data)
    
    # Store position seed + encrypted salt
    with open(output_path, 'wb') as file:
        file.write(struct.pack('!H', len(salt_data)))  # 2 bytes: salt length
        file.write(position_seed)  # 32 bytes
        file.write(encrypted)  # variable length

# Load salt with decryption
def load_salt(salt_path: str) -> tuple[bytes, bytes]:
    with open(salt_path, 'rb') as file:
        salt_length = struct.unpack('!H', file.read(2))[0]
        position_seed = file.read(32)
        encrypted_data = file.read()
    
    key = get_encryption_key()
    f = Fernet(key)
    try:
        salt_data = f.decrypt(encrypted_data)
        return salt_data, position_seed
    except Exception as e:
        print(f"Error: Failed to decrypt salt file: {salt_path}")
        print(f"  Ensure TF_ANALYZER_SALT_KEY environment variable is set correctly")
        sys.exit(6)
```

**Alternatives Considered**:
- **AES-256 GCM**: More complex API, requires managing IV/nonce separately
- **Age encryption**: External dependency, overkill for file-level encryption
- **Simple XOR**: Insufficient security, vulnerable to known-plaintext attacks
- **Base64 encoding only**: Not encryption, provides no security

**Dependencies Added**: `cryptography>=41.0.0` (already widely used in Python ecosystem)

### 2. Hashing Algorithm Selection

**Question**: Which hashing algorithm should be used for obfuscating sensitive values?

**Decision**: Use SHA-256 with salt prepended to the value before hashing

**Rationale**:
- SHA-256 is cryptographically secure and irreversible
- Fast enough for performance requirements (millions of hashes per second)
- Available in Python standard library (hashlib)
- Produces 32-byte (256-bit) output → 64 hex characters (reasonable length for "obf_" prefix format)
- Widely trusted and vetted algorithm
- No known practical collision attacks

**Implementation Pattern**:
```python
import hashlib

def obfuscate_value(value: any, salt: bytes, salt_position: int) -> str:
    # Convert value to string representation
    value_str = json.dumps(value) if not isinstance(value, str) else value
    value_bytes = value_str.encode('utf-8')
    
    # Insert salt at randomized position
    combined = value_bytes[:salt_position] + salt + value_bytes[salt_position:]
    
    # Hash the combined value
    hash_obj = hashlib.sha256(combined)
    hex_hash = hash_obj.hexdigest()
    
    return f"obf_{hex_hash}"
```

**Alternatives Considered**:
- **SHA-512**: Longer output (128 hex chars) - unnecessary for this use case
- **BLAKE2**: Faster but less universally recognized, not in standard library
- **MD5/SHA-1**: Deprecated, vulnerable to collision attacks
- **bcrypt/scrypt**: Designed for password hashing (intentionally slow), overkill here

### 3. Salt Position Randomization Strategy

**Question**: How should salt position be randomized while maintaining determinism?

**Decision**: Use a PRNG seeded with the salt itself to determine insertion position per value

**Rationale**:
- Deterministic: Same salt produces same positions across runs
- Variable: Different salts produce different positions
- No metadata storage required: Position is derived, not stored
- Per-value variation: Each value gets a different position based on value hash

**Implementation Pattern**:
```python
import hashlib
import random

def get_salt_position(value_bytes: bytes, salt: bytes, max_length: int) -> int:
    # Create deterministic seed from salt + value hash
    seed_material = salt + hashlib.sha256(value_bytes).digest()
    seed = int.hashlib.sha256(seed_material).hexdigest()[:8], 16)
    
    # Use seeded PRNG to get position
    rng = random.Random(seed)
    return rng.randint(0, max_length)
```

**Alternatives Considered**:
- **Fixed position (prepend)**: Less secure, easier pattern recognition
- **Random position stored in metadata**: Requires tracking per-value, complex
- **Position based only on salt**: Same position for all values (weak)

### 4. Salt File Format

**Question**: What format should salt files use for storage?

**Decision**: Binary format with structured header: [salt_length(2)] + [position_seed(32)] + [encrypted_salt(variable)]

**Rationale**:
- Compact: Binary is more efficient than JSON/text for cryptographic data
- Versioned: Can add header bytes for future format changes
- Self-describing: Contains all metadata needed for decryption
- Machine-readable: Easy to parse with struct module
- Portable: No machine-specific data, can be used across CI/CD nodes

**Implementation Pattern**:
```python
import struct

# Write salt file
def write_salt_file(path: str, salt: bytes, position_seed: bytes, encrypted: bytes):
    with open(path, 'wb') as f:
        f.write(struct.pack('!H', len(salt)))  # 2 bytes: salt length
        f.write(position_seed)  # 32 bytes: for position randomization
        f.write(encrypted)  # variable length

# Read salt file
def read_salt_file(path: str) -> tuple:
    with open(path, 'rb') as f:
        salt_length = struct.unpack('!H', f.read(2))[0]
        position_seed = f.read(32)
        encrypted_data = f.read()
        return salt_length, position_seed, encrypted_data
```

**Alternatives Considered**:
- **JSON format**: Human-readable but requires base64 encoding (larger files, encoding overhead)
- **Plain text**: No structure, harder to parse, no forward compatibility
- **Pickle**: Python-specific, security concerns

### 5. Default Salt Length

**Question**: What should be the default length for generated salts?

**Decision**: 32 bytes (256 bits) matching SHA-256 hash output size

**Rationale**:
- Matches security level of SHA-256
- Industry standard for cryptographic salts
- Large enough to prevent rainbow tables
- Small enough to be performant
- Consistent with authentication best practices

**Alternatives Considered**:
- **16 bytes**: Sufficient but less margin of safety
- **64 bytes**: Overkill, no meaningful security benefit
- **Variable random length**: Adds complexity without security benefit

## Summary of Resolved Clarifications

| Item | Question | Decision |
|------|----------|----------|
| Encryption method | How to encrypt salt files? | Fernet (AES-128 CBC + HMAC) with key from TF_ANALYZER_SALT_KEY env var |
| Machine ID source | How to get machine identifier? | Not used - environment variable provides portable encryption |
| Hash algorithm | Which algorithm for obfuscation? | SHA-256 (standard library, secure, fast) |
| Position randomization | How to randomize salt position? | PRNG seeded with salt + value hash |
| Salt file format | How to structure salt files? | Binary with header [length + seed + encrypted] |
| Salt length | Default salt size? | 32 bytes (256 bits) |

## Implementation Dependencies

**Required Libraries**:
- `cryptography>=41.0.0` - Fernet encryption for salt storage
- `hashlib` - SHA-256 hashing (Python standard library)
- `secrets` - Cryptographically secure random generation (Python standard library)
- `json` - Plan file parsing (Python standard library)
- `struct` - Binary file format handling (Python standard library)

**No Additional External Dependencies Required**: The design leverages Python standard library extensively with only one well-established external dependency (cryptography).

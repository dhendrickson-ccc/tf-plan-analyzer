# Phase 1: Data Model

**Date**: 2026-01-14  
**Purpose**: Define data structures for the obfuscate feature

## Entities

### SaltConfiguration

Represents the salt used for deterministic hashing during obfuscation, including encryption metadata.

**Purpose**: Encapsulate all salt-related data for secure storage and retrieval

**Attributes**:
- `salt_bytes`: bytes - The cryptographic salt value (32 bytes / 256 bits)
- `position_seed`: bytes - Seed for determining salt insertion position (32 bytes)
- `created_at`: datetime - Timestamp of salt generation
- `encryption_key`: bytes - Fernet key from TF_ANALYZER_SALT_KEY environment variable

**Behavior**:
- Generate new salt using `secrets.token_bytes(32)`
- Get encryption key from TF_ANALYZER_SALT_KEY environment variable
- Generate new key if env var not set and display for user to save
- Encrypt salt data using Fernet before file storage
- Decrypt salt data when loading from file

**Storage Format** (binary):
```
[salt_length: 2 bytes (uint16 big-endian)]
[position_seed: 32 bytes]
[encrypted_salt_data: variable length]
```

**Relationships**:
- Used by ObfuscationSession to hash values
- Persisted to `.salt` file alongside obfuscated output

---

### ObfuscatedValue

Represents a single sensitive value that has been replaced with a deterministic hash.

**Purpose**: Encapsulate the transformation from sensitive value to obfuscated hash

**Attributes**:
- `original_type`: str - Original JSON type (string, number, boolean, null)
- `hash_value`: str - The obfuscated hash with "obf_" prefix (e.g., "obf_a1b2c3...")
- `field_path`: list[str] - JSON path to the value (e.g., ["resource_changes", 0, "change", "after", "password"])

**Behavior**:
- Convert any JSON primitive to bytes for hashing
- Insert salt at position determined by `get_salt_position(value, salt)`
- Hash combined (value + salt) using SHA-256
- Format as "obf_" + hexdigest

**Derivation**:
```python
value_bytes = json.dumps(original_value).encode('utf-8')
position = get_salt_position(value_bytes, salt.salt_bytes, len(value_bytes))
combined = value_bytes[:position] + salt.salt_bytes + value_bytes[position:]
hash_hex = hashlib.sha256(combined).hexdigest()
result = f"obf_{hash_hex}"
```

**Relationships**:
- Created from SensitiveValueMarker and original value
- Replaces original value in TerraformPlanFile output

---

### SensitiveValueMarker

Represents Terraform's sensitive_values structure that indicates which fields contain sensitive data.

**Purpose**: Navigate the parallel structure to identify values requiring obfuscation

**Attributes**:
- `marker_dict`: dict - The sensitive_values object from Terraform plan
- `resource_address`: str - Full resource address (e.g., "azurerm_key_vault.main")

**Behavior**:
- Traverse in parallel with actual resource data
- Return paths where marker value is `true` (boolean)
- Handle nested objects and arrays
- Validate marker structure matches resource structure

**Structure Example**:
```json
{
  "sensitive_values": {
    "secret_key": true,
    "config": {
      "password": true,
      "username": false
    },
    "tags": false
  }
}
```

**Relationships**:
- Extracted from TerraformPlanFile for each resource
- Guides which values in TerraformPlanFile.resource_data to obfuscate

---

### ObfuscationSession

Represents a single execution of the obfuscate command with its configuration and results.

**Purpose**: Coordinate the obfuscation process for a single plan file

**Attributes**:
- `input_file`: Path - Input tfplan.json file
- `output_file`: Path - Output obfuscated plan file
- `salt_config`: SaltConfiguration - Salt used for this session
- `salt_file`: Path - Path to encrypted salt file
- `resource_count`: int - Number of resources processed
- `values_obfuscated`: int - Count of values replaced
- `force_overwrite`: bool - Whether to overwrite existing output

**Behavior**:
- Load or generate SaltConfiguration
- Parse input TerraformPlanFile
- Traverse each resource and its SensitiveValueMarker
- Create ObfuscatedValue for each sensitive field
- Write modified plan to output file
- Save SaltConfiguration to encrypted file
- Return summary statistics

**Error Handling**:
- Exit if output file exists and not force_overwrite
- Exit if input JSON is invalid
- Exit if sensitive_values structure is malformed
- Report detailed error with resource address and field path

**Relationships**:
- Uses SaltConfiguration for hashing
- Processes TerraformPlanFile input
- Produces modified TerraformPlanFile output

---

### TerraformPlanFile

*Reference: This entity already exists in the canonical data model (`.specify/memory/data_model.md`) and represents the Terraform plan JSON structure.*

**Relevant Attributes for Obfuscation**:
- `resource_changes`: list - Array of resource change objects
- `resource_changes[].change.after_sensitive`: dict - The sensitive_values marker (renamed from sensitive_values)
- `resource_changes[].change.after`: dict - The actual resource values to obfuscate
- `resource_changes[].address`: str - Resource identifier for error messages

**Obfuscation Interaction**:
- Read `after_sensitive` to find SensitiveValueMarker
- Modify `after` values in-place when they are marked sensitive
- Preserve all other fields unchanged
- Maintain JSON structure integrity

---

## Data Flow

```
Input: tfplan.json
    ↓
1. Parse TerraformPlanFile
    ↓
2. Load/Generate SaltConfiguration
    ↓
3. For each resource_change:
    ├─ Extract SensitiveValueMarker (after_sensitive)
    ├─ For each field marked true:
    │   ├─ Get value from resource_change.after
    │   ├─ Create ObfuscatedValue using SaltConfiguration
    │   └─ Replace value in resource_change.after
    └─ Continue to next resource
    ↓
4. Write modified TerraformPlanFile to output
    ↓
5. Save SaltConfiguration to encrypted .salt file
    ↓
Output: obfuscated.json + obfuscated.json.salt
```

## Type Definitions

### Hash Function Signature

```python
def obfuscate_value(
    value: Union[str, int, float, bool, None],
    salt: bytes,
    position_seed: bytes
) -> str:
    """
    Hash a value with salt inserted at deterministic position.
    
    Args:
        value: The sensitive value to obfuscate
        salt: Cryptographic salt (32 bytes)
        position_seed: Seed for position randomization (32 bytes)
    
    Returns:
        Obfuscated hash with "obf_" prefix (e.g., "obf_a1b2c3...")
    """
```

### Salt Position Function Signature

```python
def get_salt_position(
    value_bytes: bytes,
    salt: bytes,
    position_seed: bytes,
    max_length: int
) -> int:
    """
    Determine salt insertion position using deterministic PRNG.
    
    Args:
        value_bytes: Value as bytes
        salt: Cryptographic salt
        position_seed: Seed for position randomization
        max_length: Maximum valid position (length of value)
    
    Returns:
        Position index (0 to max_length inclusive)
    """
```

## Constraints

- **Immutability**: Original values must not be modified in input file
- **Determinism**: Same salt + value must always produce same hash
- **Type Preservation**: All obfuscated values become strings (with "obf_" prefix)
- **Structure Preservation**: JSON nesting and array order must be maintained
- **Error Atomicity**: If any error occurs, output file must not be created or modified

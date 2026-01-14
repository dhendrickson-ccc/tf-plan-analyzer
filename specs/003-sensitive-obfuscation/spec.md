# Feature Specification: Sensitive Data Obfuscation

**Feature Branch**: `003-sensitive-obfuscation`  
**Created**: January 14, 2026  
**Status**: Draft  
**Input**: User description: "I want to add a new sub command called "obfuscate" that will obfuscate sensitive data but still keep it unique. I'm thinking of using a randomized salt of a random length in a random location. Then hashing that. I want this to be irreversible, but still useful to determine if there's drift between 2 different files. This should be deterministic and not something that can be easily guessed. I guess that means it should provide the same output every run, but I would like it if there was some way to randomize it further. I want to sanitize data in a tfplan.json by looking at the "sensitive_values" in every resource and obfuscating all the values in the actual object that have their keys equal to "true" within the sensitive_values object. The output should be the same tfplan.json with the all sensitive values obfuscated."

---

**⚠️ Terminology Note**: This specification uses "sensitive_values" as shorthand for readability. The actual Terraform plan JSON structure uses `resource_changes[].change.after_sensitive` (and `before_sensitive`) to mark sensitive fields. When this spec references "sensitive_values markers" or "the sensitive_values object", it refers to these `after_sensitive` / `before_sensitive` structures within each resource's change block.

---

## Clarifications

### Session 2026-01-14

- Q: How should the obfuscate command respond when it encounters errors (invalid JSON, missing sensitive_values, I/O failures)? → A: Exit with error code, detailed error message to stderr including which resource/field failed, no output file created
- Q: Where should the auto-generated salt be saved, and how should it be named? → A: Save as `<output_filename>.salt` in the same directory as the output file (e.g., `plan-obfuscated.json` → `plan-obfuscated.json.salt`)
- Q: What format should obfuscated hash values have in the output file? → A: Hexadecimal string with prefix indicating obfuscation (e.g., `"obf_a1b2c3d4e5f6..."`)
- Q: How should the system handle existing output files? → A: Exit with error if output file exists unless a `--force` or `--overwrite` flag is provided
- Q: Should SC-002 be clarified to specify that identical output requires using the same salt? → A: Yes, clarify: "Obfuscating the same file multiple times with the same salt produces identical output 100% of the time"
- Q: Should salt length be fixed or variable as originally mentioned? → A: Fixed at 32 bytes (256 bits) for consistent cryptographic security and to match SHA-256 output size

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Obfuscate Sensitive Values in Single File (Priority: P1)

A DevOps engineer needs to share a Terraform plan file with team members or include it in logs/reports, but the plan contains sensitive credentials, tokens, or private data. They run the obfuscate command on their tfplan.json file to produce a sanitized version where all sensitive values are masked but remain unique and consistent, allowing the file to be safely shared while preserving the ability to detect differences between similar values.

**Why this priority**: This is the core functionality - being able to safely share plan files without exposing sensitive data. Without this, the feature has no value.

**Independent Test**: Can be fully tested by providing a tfplan.json with sensitive_values markers, running the obfuscate command, and verifying that the output file has all sensitive values replaced with deterministic obfuscated versions while non-sensitive values remain unchanged.

**Acceptance Scenarios**:

1. **Given** a tfplan.json file with resources containing sensitive_values markers, **When** the obfuscate command is executed, **Then** all values marked as sensitive (true in sensitive_values) are replaced with obfuscated hashes
2. **Given** a tfplan.json with multiple resources, **When** the same sensitive value appears in different locations, **Then** each occurrence is obfuscated to the same hash value
3. **Given** a tfplan.json with nested sensitive values, **When** the obfuscate command runs, **Then** all sensitive values at any depth level are obfuscated
4. **Given** a resource with no sensitive_values marker, **When** obfuscation runs, **Then** all values in that resource remain unchanged

---

### User Story 2 - Deterministic Obfuscation for Drift Detection (Priority: P2)

A DevOps engineer needs to compare two Terraform plan files to detect drift or differences, but both files contain sensitive data. They obfuscate both files and then compare them, knowing that identical sensitive values will produce identical obfuscated hashes, allowing them to accurately identify true differences while maintaining security.

**Why this priority**: This enables the key use case of drift detection across environments. It builds on P1 by proving the deterministic nature works for comparisons.

**Independent Test**: Can be tested by obfuscating the same tfplan.json twice and verifying identical output, then obfuscating two different plan files with some overlapping sensitive values and confirming matching values produce matching hashes.

**Acceptance Scenarios**:

1. **Given** the same tfplan.json file, **When** obfuscated multiple times, **Then** each run produces identical output
2. **Given** two different tfplan.json files with the same sensitive value, **When** both are obfuscated, **Then** that sensitive value produces the same obfuscated hash in both files
3. **Given** two plan files with different sensitive values, **When** obfuscated and compared, **Then** the differences are clearly visible as different hash values

---

### User Story 3 - Salt Management and Reuse (Priority: P3)

A security-conscious engineer wants to prevent rainbow table attacks or pattern recognition on obfuscated values. They run the obfuscate command which auto-generates a random salt (with variable position) for the session, and the system saves this salt in an encrypted format. For subsequent related comparisons, they can reuse the saved salt to ensure identical sensitive values produce identical hashes, or generate a new salt for unrelated obfuscation sessions.

**Why this priority**: This enhances security by making it harder to reverse-engineer or correlate obfuscated values across different runs, but the core functionality works without it.

**Independent Test**: Can be tested by running obfuscation with different salt configurations and verifying that the same input produces different outputs with different salts, but identical outputs with the same salt.

**Acceptance Scenarios**:

1. **Given** a tfplan.json and a previously saved salt file, **When** obfuscated with --salt-file, **Then** the output uses that salt for all hashing
2. **Given** different salt files, **When** the same file is obfuscated with each, **Then** the obfuscated outputs differ
3. **Given** the same salt file, **When** used across multiple files, **Then** identical sensitive values produce identical hashes

---

### Edge Cases

- **Malformed sensitive_values**: System exits with detailed error message identifying the problematic resource (malformed = non-boolean values in after_sensitive structure, such as nested objects, strings, or numbers instead of true/false)
- **Empty string values marked as sensitive**: System obfuscates empty strings like any other value
- **Deeply nested values (5+ levels)**: System handles arbitrary nesting depth
- **Null values marked as sensitive**: System obfuscates null values to a deterministic hash
- **Missing value for sensitive_values marker**: System exits with error identifying the mismatch
- **Invalid or corrupted tfplan.json**: System exits immediately with parse error details
- **Very large files (100+ MB)**: System processes incrementally without creating output on failure
- **Nested objects in sensitive_values**: System exits with error (sensitive_values must be boolean true/false)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a subcommand named "obfuscate" that accepts a tfplan.json file as input
- **FR-002**: System MUST traverse all resources in the tfplan.json and locate their corresponding sensitive_values markers
- **FR-003**: System MUST obfuscate all values whose keys are marked with true in the sensitive_values object
- **FR-004**: System MUST use a one-way hashing algorithm that produces irreversible output
- **FR-005**: System MUST ensure the same input value produces the same obfuscated output (deterministic hashing)
- **FR-006**: System MUST preserve the structure of the tfplan.json file, only replacing sensitive values
- **FR-007**: System MUST handle nested objects and arrays, obfuscating sensitive values at any depth level
- **FR-008**: System MUST output the modified tfplan.json with all sensitive values obfuscated
- **FR-009**: System MUST generate a random salt per session (with randomized position within the hashed data) and store it in encrypted format for potential reuse in related comparisons
- **FR-015**: Users MUST be able to specify a previously saved salt file to ensure deterministic hashing across multiple obfuscation runs
- **FR-016**: System MUST encrypt salt data before persisting it to prevent unauthorized reuse or reverse-engineering
- **FR-020**: System MUST save the generated salt file with the naming pattern `<output_filename>.salt` in the same directory as the output file
- **FR-021**: Users MUST be able to specify an existing salt file path via command-line to reuse a previously generated salt
- **FR-010**: System MUST ensure obfuscated values are unique when input values are unique (hash collision resistance)
- **FR-011**: System MUST preserve non-sensitive values exactly as they appear in the original file
- **FR-012**: System MUST handle all JSON primitive types (string, number, boolean, null) that are marked as sensitive
- **FR-022**: System MUST format all obfuscated values as hexadecimal strings with the prefix "obf_" regardless of the original data type
- **FR-023**: System MUST exit with error if the output file already exists unless an overwrite flag is explicitly provided
- **FR-013**: Users MUST be able to specify the output file path (defaults to `<input_stem>-obfuscated.json` if not specified)
- **FR-014**: System MUST validate that the input file is a valid tfplan.json structure before processing
- **FR-017**: System MUST exit with a non-zero error code when encountering validation failures, I/O errors, or malformed data
- **FR-018**: System MUST output detailed error messages to stderr indicating which resource or field caused the failure
- **FR-019**: System MUST NOT create or modify the output file when any error occurs during processing

### Key Entities

- **Terraform Plan File**: A JSON file containing planned infrastructure changes, including resource definitions, computed values, and sensitive_values markers indicating which fields contain secrets or private data
- **Sensitive Values Marker**: A parallel structure within each resource that maps field paths to boolean values, where true indicates the corresponding field in the actual resource data is sensitive
- **Obfuscated Value**: The irreversible hashed representation of a sensitive value as a hexadecimal string with "obf_" prefix, maintaining uniqueness and determinism for comparison purposes
- **Salt**: A cryptographic component (32 bytes / 256 bits) that enhances security by preventing reverse-engineering of obfuscated values. Generated randomly per session with variable position in the hashed data, stored in encrypted format, and optionally reusable for related comparisons to maintain determinism

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can obfuscate a tfplan.json file in under 5 seconds for files up to 10 MB (measured as average execution time across 10 test runs on representative hardware)
- **SC-002**: Obfuscating the same file multiple times with the same salt produces identical output 100% of the time
- **SC-003**: Two different files containing the same sensitive value produce matching obfuscated hashes for that value when using the same salt
- **SC-004**: Users can successfully compare two obfuscated files and identify actual drift vs. identical values
- **SC-005**: No sensitive values appear in plaintext in the obfuscated output (verified through manual inspection and automated scanning)
- **SC-006**: The obfuscation process completes without errors for valid tfplan.json files 100% of the time
- **SC-007**: Users can process files containing up to 1000 resources without memory issues or significant performance degradation

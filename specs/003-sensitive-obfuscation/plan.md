# Implementation Plan: Sensitive Data Obfuscation

**Branch**: `003-sensitive-obfuscation` | **Date**: 2026-01-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-sensitive-obfuscation/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Add an `obfuscate` subcommand to the Terraform Plan Analyzer that replaces sensitive values (marked by Terraform's sensitive_values structure) with irreversible deterministic hashes. The obfuscation uses per-session randomized salts with variable position, stored in encrypted format for optional reuse. This enables safe sharing of plan files while maintaining the ability to detect drift across environments through consistent hashing when using the same salt.

## Technical Context

**Language/Version**: Python 3.11+ (matches existing project)  
**Primary Dependencies**: 
- Python standard library (hashlib, secrets, json, argparse, struct)
- cryptography>=41.0.0 for Fernet salt encryption
**Storage**: File-based (input tfplan.json, output obfuscated.json, encrypted .salt file with binary format)  
**Testing**: pytest (matches existing test infrastructure)  
**Target Platform**: Cross-platform CLI (Linux, macOS, Windows)
**Project Type**: Single project (Python CLI tool)  
**Performance Goals**: Process 10 MB plan files in under 5 seconds, handle 1000+ resources without degradation  
**Constraints**: 
- Must preserve determinism (same salt + value = same hash)
- Hash output must be irreversible (SHA-256)
- Salt storage must be encrypted (Fernet with key from TF_ANALYZER_SALT_KEY env var)
- Salt files must be portable across CI/CD nodes
- Must not modify original file structure
**Scale/Scope**: Typical usage 10-1000 resources per plan, files up to 100 MB

## Clarifications

### Session 2026-01-14

- Q: How should the system obtain a machine identifier for PBKDF2 key derivation? → A: Not needed - use TF_ANALYZER_SALT_KEY environment variable for portable encryption across CI/CD nodes
- Q: How should responsibilities be divided between sensitive_obfuscator.py and salt_manager.py? → A: salt_manager.py handles all salt operations (generate, encrypt, decrypt, store, load), sensitive_obfuscator.py handles obfuscation logic (traverse JSON, hash values, replace fields)
- Q: How should the system respond when salt file decryption fails? → A: Exit with detailed error message explaining the failure and suggest checking TF_ANALYZER_SALT_KEY environment variable
- Q: Should users be able to provide a raw salt value directly, or only via salt file? → A: Only support --salt-file (file path) for better security and to avoid exposing cryptographic material in command line/shell history
- Q: Should the default output be a file or standard output? → A: Default to file `<input>-obfuscated.json` for safety and to support salt file creation (awkward with stdout)
- Q: How should the system handle missing TF_ANALYZER_SALT_KEY? → A: Generate key and display it with prominent security warnings (key visible in logs, store securely, don't commit, required for salt reuse)
- Q: What specific test scenarios need dedicated fixture files? → A: Comprehensive set: basic.json, nested.json, multiple-resources.json, empty-sensitive.json, null-sensitive.json, malformed-sensitive.json, no-sensitive-marker.json
- Q: Should salt length be fixed or variable as originally mentioned? → A: Fixed at 32 bytes (256 bits) for consistent cryptographic security and to match SHA-256 output size

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Code Duplication Prohibited ✅ PASS (Re-verified Post-Design)

**Status**: No violations - design promotes reuse
- Will search for existing hashing/salt utilities before creating new ones
- Will reuse existing JSON loading/validation patterns from analyze_plan.py
- Will follow established CLI subcommand pattern from existing 'report' and 'compare' commands
- **Post-Design**: Data model entities (SaltConfiguration, ObfuscatedValue) are single-purpose and reusable

### II. Shared Data Model Is Canonical ✅ PASS (Re-verified Post-Design)

**Status**: Data model updated in Phase 1
- **Completed**: Created data-model.md with canonical entities (SaltConfiguration, ObfuscatedValue, SensitiveValueMarker, ObfuscationSession)
- References existing TerraformPlanFile entity from canonical data model
- All feature entities documented in specs/003-sensitive-obfuscation/data-model.md
- **Post-Design**: No duplicate entity definitions across modules

### III. Live Testing Is Mandatory ✅ PASS (Re-verified Post-Design)

**Status**: Live test plan confirmed with real fixtures
- Test with actual Terraform plan files containing sensitive_values markers
- Validate obfuscation produces identical hashes across multiple runs with same salt
- Test salt reuse by obfuscating multiple files and verifying matching sensitive values produce matching hashes
- Test files from test_data/ directory (dev-sensitive.json, prod-sensitive.json)
- **Post-Design**: quickstart.md includes verification steps for live validation

### IV. Commit After Every User Story ✅ PASS (Re-verified Post-Design)

**Status**: Feature has 3 user stories; will commit after completing each
- P1: Basic obfuscation → commit
- P2: Deterministic drift detection → commit  
- P3: Salt configuration management → commit
- **Post-Design**: Each user story maps to independent deliverable (confirmed in data model)

### V. User-Facing Features Require End-to-End Testing ✅ PASS (Re-verified Post-Design)

**Status**: CLI contract defines comprehensive end-to-end test scenarios
- Will create tests that invoke `python analyze_plan.py obfuscate plan.json --output out.json`
- Test flag combinations: `--salt-file`, `--force`, `--output`, `--show-stats`
- Test error cases: missing file, invalid JSON, existing output file, corrupted salt
- Validate complete user journey from CLI invocation to file output
- **Post-Design**: contracts/cli-interface.md defines 8 exit codes and corresponding test scenarios

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# Existing structure (Python CLI tool)
/
├── analyze_plan.py           # Main CLI entry point - ADD obfuscate subcommand
├── sensitive_obfuscator.py   # NEW: Core obfuscation logic
├── salt_manager.py           # NEW: Salt generation, storage, encryption
├── multi_env_comparator.py   # Existing: multi-environment comparison
├── generate_html_report.py   # Existing: HTML report generation
├── hcl_value_resolver.py     # Existing: HCL value resolution
├── test_e2e_obfuscate.py     # NEW: End-to-end CLI tests for obfuscate
├── test_obfuscation_unit.py  # NEW: Unit tests for obfuscation logic
├── test_salt_manager.py      # NEW: Unit tests for salt management
├── test_change_detection.py  # Existing: change detection tests
├── test_e2e_multi_env.py     # Existing: multi-env e2e tests
├── test_data/                # Existing: test fixtures
│   ├── dev-sensitive.json    # Existing: dev plan with sensitive values
│   ├── prod-sensitive.json   # Existing: prod plan with sensitive values
│   ├── test-obfuscate-basic.json              # NEW: Simple resource with sensitive values
│   ├── test-obfuscate-nested.json             # NEW: Deeply nested sensitive values (5+ levels)
│   ├── test-obfuscate-multiple-resources.json # NEW: Multiple resources with overlapping sensitive values
│   ├── test-obfuscate-empty-sensitive.json    # NEW: Empty string marked as sensitive
│   ├── test-obfuscate-null-sensitive.json     # NEW: Null value marked as sensitive
│   ├── test-obfuscate-malformed-sensitive.json # NEW: Invalid sensitive_values structure for error testing
│   └── test-obfuscate-no-sensitive-marker.json # NEW: Resources without sensitive_values markers
└── specs/
    └── 003-sensitive-obfuscation/
        ├── spec.md
        ├── plan.md           # This file
        ├── research.md       # Phase 0 output
        ├── data-model.md     # Phase 1 output
        ├── quickstart.md     # Phase 1 output
        └── contracts/
            └── cli-interface.md  # Phase 1 output
```

**Structure Decision**: Following existing single-project Python CLI pattern. New modules (sensitive_obfuscator.py, salt_manager.py) will be added at root level alongside existing modules. CLI integration will extend analyze_plan.py's existing subcommand architecture (report, compare → add obfuscate).

## Complexity Tracking

**Status**: ✅ No Constitution violations

All Constitution principles are satisfied. No additional complexity introduced beyond necessary requirements.


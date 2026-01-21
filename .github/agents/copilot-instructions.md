# tf-plan-analyzer Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-13

## Active Technologies
- Python 3.11+ (matches existing project) (003-sensitive-obfuscation)
- File-based (input tfplan.json, output obfuscated.json, encrypted .salt file with binary format) (003-sensitive-obfuscation)
- Python 3.9.6 + Python stdlib (json, pathlib, difflib, html), pytest 8.4.2 (testing) (004-compare-enhancements)
- Filesystem (JSON plan files, HTML output files) (004-compare-enhancements)
- Python 3.9.6 + No new dependencies - pure HTML+CSS modifications (006-comparison-ui-improvements)
- HTML file output (static reports) (006-comparison-ui-improvements)
- Python 3.9+ (requires-python = ">=3.9" in pyproject.toml) + Python standard library only (json, re, pathlib) - no external packages needed for normalization (007-normalization-diff-filtering)
- JSON files (ignore_config.json, normalizations.json) - file-based configuration (007-normalization-diff-filtering)

- Python 3.8+ (matching existing codebase) (001-multi-env-comparison)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.8+ (matching existing codebase): Follow standard conventions

## Recent Changes
- 007-normalization-diff-filtering: Added Python 3.9+ (requires-python = ">=3.9" in pyproject.toml) + Python standard library only (json, re, pathlib) - no external packages needed for normalization
- 006-comparison-ui-improvements: Added Python 3.9.6 + No new dependencies - pure HTML+CSS modifications
- 004-compare-enhancements: Added Python 3.9.6 + Python stdlib (json, pathlib, difflib, html), pytest 8.4.2 (testing)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

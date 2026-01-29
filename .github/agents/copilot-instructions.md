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
- Python 3.11 (existing project constraint) + None (client-side JavaScript for LocalStorage interaction, no new Python dependencies) (008-attribute-notes)
- Browser LocalStorage (client-side only, no server-side persistence) (008-attribute-notes)
- Python 3.9+ (currently supports 3.9, 3.10, 3.11) + json5>=0.9.0 for parsing; client-side JavaScript for markdown rendering (009-qa-markdown-preview)
- LocalStorage (client-side) for Q&A notes persistence (009-qa-markdown-preview)

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
- 009-qa-markdown-preview: Added Python 3.9+ (currently supports 3.9, 3.10, 3.11) + json5>=0.9.0 for parsing; client-side JavaScript for markdown rendering
- 008-attribute-notes: Added Python 3.11 (existing project constraint) + None (client-side JavaScript for LocalStorage interaction, no new Python dependencies)
- 007-normalization-diff-filtering: Added Python 3.9+ (requires-python = ">=3.9" in pyproject.toml) + Python standard library only (json, re, pathlib) - no external packages needed for normalization


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

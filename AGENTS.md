# AGENTS.md

## Project Summary

This repository contains a command-line Python extractor for OpenDocument Spreadsheet files. Given an `.ods` file, it opens the archive, parses `content.xml` with `lxml`, and writes one `.tsv` file per sheet into a timestamped export directory created in the current working directory.

The implementation is intentionally compact, but the behavior is more careful than a naive sheet dump. It preserves merged-cell coverage, multiline cell text, manual line breaks, repeated spaces, and enough table structure to keep exported TSV output aligned and machine-readable.

## Repository Layout

- `ods_to_tsv.py` - main implementation and CLI entry point.
- `test_ods_to_tsv.py` - `unittest` suite that builds synthetic ODS fixtures and verifies extraction behavior.
- `README.md` - user-facing overview, installation, usage, and feature description.
- `COPYING.md` - GNU GPL v3 license text.
- `.github/workflows/test.yml` - CI workflow that installs `lxml` and runs the test suite on Python 3.12.

## How The Tool Works

The extractor:

1. Computes an output directory name from the input filename plus a timestamp.
2. Opens the `.ods` file as a ZIP archive.
3. Parses `content.xml` and iterates through `table:table` sheet nodes.
4. Reconstructs row and column layout, including repeated rows and columns.
5. Expands merged-cell values into covered cells so TSV columns remain aligned.
6. Preserves text paragraphs, explicit line breaks, and repeated spaces.
7. Trims trailing empty cells and skips obviously excessive trailing empty spreadsheet space.

## Key Behavioral Constraints

- The output directory is created relative to the caller's current working directory, not next to the input file.
- Each sheet becomes its own TSV file named from a sanitized version of the sheet name.
- Merged areas are flattened by repeating the source value into the covered cells.
- Output stability matters. Small changes to parsing logic can change TSV shape, whitespace, or line-break behavior.
- The current implementation is a script, not a package. Keep changes proportional to that scale unless a broader refactor is explicitly requested.

## Dependencies And Execution

- Runtime dependency: `lxml`
- Standard library modules used heavily: `zipfile`, `csv`, `datetime`, `os`, `sys`, `unittest`
- Typical local run: `python3 ods_to_tsv.py path/to/file.ods`
- Typical test run: `python3 test_ods_to_tsv.py`

## Testing Expectations

When changing extraction logic, verify at minimum:

- basic sheet-to-TSV export
- merged row spans and column spans
- multiline text preservation
- repeated-space handling
- filename sanitization

Add or update tests in `test_ods_to_tsv.py` whenever output shape or text handling changes. Prefer synthetic fixtures in tests over checking in binary spreadsheets unless the task specifically calls for real samples.

## Editing Guidance

- Read `ods_to_tsv.py` and `test_ods_to_tsv.py` before changing parsing behavior.
- Preserve CLI simplicity unless the task explicitly asks for packaging, options, or a broader interface.
- Avoid new dependencies unless they solve a concrete parsing or maintainability problem that the standard library and `lxml` cannot handle cleanly.
- Be careful with whitespace semantics. TSV output is sensitive to paragraph joins, `text:s`, and `text:line-break`.
- Keep filename sanitization predictable. Changes there affect both filesystem behavior and tests.
- Do not silently remove the timestamped export-directory behavior; it is documented and tested by workflow expectations.

## Known Gaps To Keep In Mind

- The tests are focused and useful, but not exhaustive for all ODS constructs.
- The code currently assumes `content.xml` exists and is readable inside the ODS archive.
- Error handling and CLI ergonomics are minimal because the project is currently a utility script rather than a full packaged application.

## First Files To Read

If you are new to the repository, start in this order:

1. `README.md`
2. `ods_to_tsv.py`
3. `test_ods_to_tsv.py`
4. `.github/workflows/test.yml`

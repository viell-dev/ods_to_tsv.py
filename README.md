# ODS to TSV Extractor

[![Python Test](https://github.com/viell-dev/ods_to_tsv.py/actions/workflows/test.yml/badge.svg)](https://github.com/viell-dev/ods_to_tsv.py/actions/workflows/test.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A compact Python command-line utility that exports each sheet in an `.ods` (OpenDocument Spreadsheet)
file as a separate tab-separated values (`.tsv`) file.

## Features

- **One TSV per sheet**: Creates a separate file for each spreadsheet sheet.
- **Rectangular output**: Pads each emitted row to the sheet's last populated column. Empty columns
  between values are preserved; globally trailing empty columns are omitted.
- **Grid fidelity**: Expands merged cells into their covered positions and supports repeated rows and
  columns.
- **Whitespace and text handling**: Preserves paragraphs, manual line breaks (`text:line-break`), and
  repeated spaces (`text:s`) within values, then trims leading and trailing whitespace from each cell.
- **Empty rows**: Omits leading and trailing empty rows while retaining empty rows between populated
  rows.
- **Raw value mode**: `--raw` exports stored ODF values rather than the formatted text shown by the
  spreadsheet.
- **Predictable files**: Writes to a timestamped directory in the current working directory and
  sanitizes sheet names for filenames.

## Requirements

- Python 3.x
- `lxml` library

Install the runtime dependency:

```bash
pip install lxml
```

## Usage

Export formatted cell text (the default):

```bash
python3 ods_to_tsv.py "Path/To/Your/File.ods"
```

Export raw stored values instead:

```bash
python3 ods_to_tsv.py --raw "Path/To/Your/File.ods"
```

The script creates `<filename> - <ISO-datetime>` in the current working directory and places the TSV
files inside it.

### Raw values and formulas

Without `--raw`, the exporter writes the formatted text displayed by the spreadsheet. With `--raw`, it
uses stored ODF values for numeric, percentage, currency, date, time, boolean, and string cells. For a
formula cell, this is its cached calculated result. The script does not calculate or recalculate
formulas; if a cell has no stored raw value, it falls back to its text content.

### Output shape

Each emitted row has the same number of TSV fields. The width is the last column containing a non-empty
value anywhere in the sheet, so a value beyond the header range adds empty header fields. Empty columns
inside that range remain in their original positions. Leading and trailing empty rows are omitted, while
empty rows between populated rows are retained.

## Testing

A synthetic-fixture test suite covers grid alignment, merged cells, repeated cells and rows, text and
whitespace handling, filename sanitization, and raw values.

```bash
python3 test_ods_to_tsv.py
```

## License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0-only)**. See the [COPYING.md](COPYING.md) file for details.

## How it works

The script parses `content.xml` from the ODS ZIP archive with `lxml`. It walks the table structure,
tracks merged areas and repeated rows and columns, then writes the reconstructed grid with Python's
standard `csv` writer configured for tabs.

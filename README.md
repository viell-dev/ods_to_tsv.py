# ODS to TSV Extractor

[![Python Test](https://github.com/viell-dev/ods_to_tsv.py/actions/workflows/test.yml/badge.svg)](https://github.com/viell-dev/ods_to_tsv.py/actions/workflows/test.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A robust Python script to extract individual sheets from an `.ods` (OpenDocument Spreadsheet) file into separate `.tsv` (Tab-Separated Values) files.

## Features

- **Individual Sheet Extraction**: Each sheet in the ODS file is saved as a separate `.tsv` file.
- **Merged Cell Support**: Handles row-spans and col-spans accurately, repeating the value across all spanned cells to maintain column alignment.
- **Text Fidelity**: 
  - Preserves multiple paragraphs within a single cell.
  - Handles manual line breaks (`text:line-break`).
  - Preserves repeated spaces (`text:s`) within cell values.
  - Trims leading and trailing whitespace from every cell value.
- **Timestamped Backups**: Automatically creates a directory named `<filename> - <ISO-datetime>` in the current working directory to store the exports, allowing for dated backups.
- **Efficiency**: Optimized to skip excessive trailing empty rows and columns often found in large spreadsheets, while padding every exported row to the last column containing data.
- **Sanitization**: Automatically sanitizes sheet names for use as valid filenames.

## Requirements

- Python 3.x
- `lxml` library

To install requirements:
```bash
pip install lxml
```

## Usage

Run the script from the command line, providing the path to your `.ods` file:

```bash
python3 ods_to_tsv.py "Path/To/Your/File.ods"
```

The script will create a new directory in your current location containing the extracted `.tsv` files.

## Testing

A comprehensive test suite is included to verify edge cases such as merged cells and special text formatting.

```bash
python3 test_ods_to_tsv.py
```

## License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0-only)**. See the [COPYING.md](COPYING.md) file for details.

## How it Works

The script parses the `content.xml` file inside the ODS ZIP package using `lxml`. It iterates through the table structure, tracking merged areas and repeated rows/columns to faithfully reconstruct the flat TSV format while ensuring that data usually hidden in "covered" cells is preserved for better machine readability.

import unittest
import os
import shutil
import zipfile
import csv
import glob
from datetime import datetime
from ods_to_tsv import extract_ods_to_tsv

class TestOdsToTsv(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_output"
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)
        self.cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        os.chdir(self.cwd)
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def create_fake_ods(self, filename, sheets_data):
        """
        sheets_data: list of dicts { 'name': str, 'rows': [ [cell_xml, ...], ... ] }
        cell_xml can be a string (content) or a dict with attributes.
        """
        content_xml = ['<?xml version="1.0" encoding="UTF-8"?>',
                       '<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">',
                       '<office:body><office:spreadsheet>']
        
        for sheet in sheets_data:
            content_xml.append(f'<table:table table:name="{sheet["name"]}">')
            for row in sheet['rows']:
                content_xml.append('<table:table-row>')
                for cell in row:
                    if isinstance(cell, str):
                        content_xml.append(f'<table:table-cell office:value-type="string"><text:p>{cell}</text:p></table:table-cell>')
                    elif isinstance(cell, dict):
                        attrs = " ".join([f'table:{k}="{v}"' for k, v in cell.items() if k != 'text'])
                        text = cell.get('text', '')
                        content_xml.append(f'<table:table-cell office:value-type="string" {attrs}><text:p>{text}</text:p></table:table-cell>')
                content_xml.append('</table:table-row>')
            content_xml.append('</table:table>')
            
        content_xml.append('</office:spreadsheet></office:body></office:document-content>')
        
        with zipfile.ZipFile(filename, 'w') as ods:
            ods.writestr('mimetype', 'application/vnd.oasis.opendocument.spreadsheet')
            ods.writestr('content.xml', "".join(content_xml))

    def test_basic_extraction(self):
        self.create_fake_ods("basic.ods", [
            {'name': 'Sheet1', 'rows': [['A1', 'B1'], ['A2', 'B2']]}
        ])
        extract_ods_to_tsv("basic.ods")
        
        dirs = glob.glob("basic - *")
        self.assertEqual(len(dirs), 1)
        tsv_file = os.path.join(dirs[0], "Sheet1.tsv")
        self.assertTrue(os.path.exists(tsv_file))
        
        with open(tsv_file, 'r') as f:
            reader = csv.reader(f, delimiter='\t')
            rows = list(reader)
            self.assertEqual(rows, [['A1', 'B1'], ['A2', 'B2']])

    def test_trailing_empty_cells_are_preserved(self):
        self.create_fake_ods("trailing-empty.ods", [
            {'name': 'Sheet1', 'rows': [['A1', 'B1', 'C1'], ['A2', '', '']]}
        ])
        extract_ods_to_tsv("trailing-empty.ods")

        dirs = glob.glob("trailing-empty - *")
        with open(os.path.join(dirs[0], "Sheet1.tsv"), 'r') as f:
            rows = list(csv.reader(f, delimiter='\t'))
            self.assertEqual(rows, [['A1', 'B1', 'C1'], ['A2', '', '']])

    def test_columns_empty_in_every_row_are_trimmed(self):
        self.create_fake_ods("shared-trailing-empty.ods", [
            {'name': 'Sheet1', 'rows': [['Header', '', ''], ['Value', '', '']]}
        ])
        extract_ods_to_tsv("shared-trailing-empty.ods")

        dirs = glob.glob("shared-trailing-empty - *")
        with open(os.path.join(dirs[0], "Sheet1.tsv"), 'r') as f:
            rows = list(csv.reader(f, delimiter='\t'))
            self.assertEqual(rows, [['Header'], ['Value']])

    def test_cell_whitespace_is_trimmed(self):
        self.create_fake_ods("cell-whitespace.ods", [
            {
                'name': 'Sheet1',
                'rows': [
                    ['  Header  ', '   '],
                    ['\tValue\t', '\n'],
                ],
            }
        ])
        extract_ods_to_tsv("cell-whitespace.ods")

        dirs = glob.glob("cell-whitespace - *")
        with open(os.path.join(dirs[0], "Sheet1.tsv"), 'r') as f:
            rows = list(csv.reader(f, delimiter='\t'))
            self.assertEqual(rows, [['Header'], ['Value']])

    def test_repeated_empty_cells_before_data_preserve_position(self):
        self.create_fake_ods("repeated-empty.ods", [
            {
                'name': 'Sheet1',
                'rows': [
                    ['Header'],
                    [{'number-columns-repeated': '1025', 'text': ''}, 'Value'],
                ],
            }
        ])
        extract_ods_to_tsv("repeated-empty.ods")

        dirs = glob.glob("repeated-empty - *")
        with open(os.path.join(dirs[0], "Sheet1.tsv"), 'r') as f:
            rows = list(csv.reader(f, delimiter='\t'))
            self.assertEqual(len(rows[0]), 1026)
            self.assertEqual(rows[0][0], 'Header')
            self.assertEqual(rows[1][-1], 'Value')
            self.assertTrue(all(len(row) == 1026 for row in rows))

    def test_merged_cells(self):
        # Test row-span and col-span
        content_xml = ['<?xml version="1.0" encoding="UTF-8"?>',
                       '<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">',
                       '<office:body><office:spreadsheet>',
                       '<table:table table:name="Spans">',
                       '<table:table-row>',
                       '<table:table-cell table:number-rows-spanned="2" office:value-type="string"><text:p>MergedRow</text:p></table:table-cell>',
                       '<table:table-cell office:value-type="string"><text:p>B1</text:p></table:table-cell>',
                       '</table:table-row>',
                       '<table:table-row>',
                       '<table:covered-table-cell/>',
                       '<table:table-cell office:value-type="string"><text:p>B2</text:p></table:table-cell>',
                       '</table:table-row>',
                       '<table:table-row>',
                       '<table:table-cell table:number-columns-spanned="2" office:value-type="string"><text:p>MergedCol</text:p></table:table-cell>',
                       '<table:covered-table-cell/>',
                       '<table:table-cell office:value-type="string"><text:p>C3</text:p></table:table-cell>',
                       '</table:table-row>',
                       '</table:table>',
                       '</office:spreadsheet></office:body></office:document-content>']
        
        with zipfile.ZipFile("merged.ods", 'w') as ods:
            ods.writestr('content.xml', "".join(content_xml))

        extract_ods_to_tsv("merged.ods")
        dirs = glob.glob("merged - *")
        with open(os.path.join(dirs[0], "Spans.tsv"), 'r') as f:
            rows = list(csv.reader(f, delimiter='\t'))
            # Row 1: MergedRow, B1
            self.assertEqual(rows[0], ['MergedRow', 'B1', ''])
            # Row 2: MergedRow, B2 (The covered-table-cell gets the value 'MergedRow')
            self.assertEqual(rows[1], ['MergedRow', 'B2', ''])
            # Row 3: MergedCol, MergedCol, C3
            self.assertEqual(rows[2], ['MergedCol', 'MergedCol', 'C3'])

    def test_multiline_and_spaces(self):
        content_xml = ['<?xml version="1.0" encoding="UTF-8"?>',
                       '<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">',
                       '<office:body><office:spreadsheet>',
                       '<table:table table:name="Text">',
                       '<table:table-row>',
                       '<table:table-cell office:value-type="string">',
                       '<text:p>Line 1</text:p><text:p>Line 2</text:p>',
                       '</table:table-cell>',
                       '<table:table-cell office:value-type="string">',
                       '<text:p>Space<text:s text:c="3"/>test</text:p>',
                       '</table:table-cell>',
                       '</table:table-row>',
                       '</table:table>',
                       '</office:spreadsheet></office:body></office:document-content>']
        
        with zipfile.ZipFile("text.ods", 'w') as ods:
            ods.writestr('content.xml', "".join(content_xml))

        extract_ods_to_tsv("text.ods")
        dirs = glob.glob("text - *")
        with open(os.path.join(dirs[0], "Text.tsv"), 'r') as f:
            rows = list(csv.reader(f, delimiter='\t'))
            self.assertEqual(rows[0][0], "Line 1\nLine 2")
            self.assertEqual(rows[0][1], "Space   test")

    def test_sanitization(self):
        self.create_fake_ods("dirty.ods", [
            {'name': 'Sheet/With\\Bad:Chars*', 'rows': [['data']]}
        ])
        extract_ods_to_tsv("dirty.ods")
        dirs = glob.glob("dirty - *")
        # Check if file exists with sanitized name
        files = os.listdir(dirs[0])
        self.assertTrue(any("SheetWithBadChars" in f for f in files))

if __name__ == "__main__":
    unittest.main()

import zipfile
from lxml import etree
import csv
import sys
import os
from datetime import datetime

def extract_ods_to_tsv(ods_path):
    # Determine base name and create output directory
    basename = os.path.splitext(os.path.basename(ods_path))[0]
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    output_dir = f"{basename} - {timestamp}"
    
    # Create the directory in the CWD
    os.makedirs(output_dir, exist_ok=True)
    print(f"Exporting to directory: {output_dir}")

    ns = {
        'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
        'table': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
        'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0'
    }

    with zipfile.ZipFile(ods_path, 'r') as ods:
        with ods.open('content.xml') as content:
            tree = etree.parse(content)
            root = tree.getroot()
            
            for sheet in root.xpath('//table:table', namespaces=ns):
                sheet_name = sheet.get(f"{{{ns['table']}}}name")
                print(f"  Extracting {sheet_name}...")
                
                # Sanitize sheet name for filename
                safe_name = "".join([c for c in sheet_name if c.isalnum() or c in (' ', '.', '_', '-')]).strip()
                tsv_path = os.path.join(output_dir, f"{safe_name}.tsv")
                
                merged_cells = {} # (row_idx, col_idx) -> value
                sheet_rows = []
                pending_empty_rows = 0
                rows = sheet.xpath('.//table:table-row', namespaces=ns)
                current_row_idx = 0
                
                for row in rows:
                    row_repeat = int(row.get(f"{{{ns['table']}}}number-rows-repeated", 1))
                    
                    for r_rep in range(row_repeat):
                        row_cells = {}
                        col_idx = 0
                        cells = row.xpath('*')
                            
                        for cell in cells:
                            col_repeat = int(cell.get(f"{{{ns['table']}}}number-columns-repeated", 1))
                                
                            for _ in range(col_repeat):
                                if cell.tag == f"{{{ns['table']}}}table-cell":
                                    # Extract text
                                    paragraphs = cell.xpath('.//text:p', namespaces=ns)
                                    cell_parts = []
                                    for p in paragraphs:
                                        for node in p.iter():
                                            if node.text:
                                                cell_parts.append(node.text)
                                            if node.tag == f"{{{ns['text']}}}s":
                                                num_spaces = int(node.get(f"{{{ns['text']}}}c", 1))
                                                cell_parts.append(" " * num_spaces)
                                            if node.tag == f"{{{ns['text']}}}line-break":
                                                cell_parts.append("\n")
                                            if node != p and node.tail:
                                                cell_parts.append(node.tail)
                                        if p != paragraphs[-1]:
                                            cell_parts.append("\n")

                                    cell_value = "".join(cell_parts).strip()

                                    # Handle spans
                                    rows_spanned = int(cell.get(f"{{{ns['table']}}}number-rows-spanned", 1))
                                    cols_spanned = int(cell.get(f"{{{ns['table']}}}number-columns-spanned", 1))

                                    if rows_spanned > 1 or cols_spanned > 1:
                                        for rs in range(rows_spanned):
                                            for cs in range(cols_spanned):
                                                if rs == 0 and cs == 0: continue
                                                merged_cells[(current_row_idx + rs, col_idx + cs)] = cell_value

                                    # Avoid materializing a long run of empty cells. If a later cell
                                    # contains data, col_idx still retains its correct position.
                                    if not cell_value and col_repeat > 1024:
                                        col_idx += col_repeat
                                        break

                                    if cell_value:
                                        row_cells[col_idx] = cell_value
                                    col_idx += 1
                                        
                                elif cell.tag == f"{{{ns['table']}}}covered-table-cell":
                                    val = merged_cells.get((current_row_idx, col_idx), "")
                                    if val:
                                        row_cells[col_idx] = val
                                    if (current_row_idx, col_idx) in merged_cells:
                                        del merged_cells[(current_row_idx, col_idx)]
                                    col_idx += 1
                            
                        # Final check for any remaining merged cells in this row
                        while (current_row_idx, col_idx) in merged_cells:
                            val = merged_cells[(current_row_idx, col_idx)]
                            if val:
                                row_cells[col_idx] = val
                            del merged_cells[(current_row_idx, col_idx)]
                            col_idx += 1

                        if row_cells:
                            if sheet_rows and pending_empty_rows:
                                sheet_rows.append(("empty", pending_empty_rows))
                            pending_empty_rows = 0
                            sheet_rows.append(row_cells)
                        else:
                            pending_empty_rows += 1

                        current_row_idx += 1

                sheet_width = max(
                    (max(row_cells) + 1 for row_cells in sheet_rows if isinstance(row_cells, dict)),
                    default=0,
                )
                with open(tsv_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f, delimiter='\t')
                    for row_cells in sheet_rows:
                        if isinstance(row_cells, tuple):
                            for _ in range(row_cells[1]):
                                writer.writerow([""] * sheet_width)
                        else:
                            writer.writerow([row_cells.get(col_idx, "") for col_idx in range(sheet_width)])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ods_to_tsv.py <filename.ods>")
    else:
        extract_ods_to_tsv(sys.argv[1])

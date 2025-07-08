#!/usr/bin/env python3

import sys
import os
import csv

COLUMN_1 = "Age [ka BP]"
COLUMN_2 = "TTT [°C]"
SKIP_METADATA = True

def find_data_start(file_path):
    """Find the line where actual data starts (after metadata comments)"""
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f):
            # Look for the line that starts with column headers (not metadata)
            if line.strip() and not any(line.startswith(prefix) for prefix in 
                                      ['License:', 'Status:', 'Size:', 'Event:', '*/']):
                # Check if this looks like a header line with our target columns
                if COLUMN_1 in line or COLUMN_2 in line:
                    return line_num
    return 0

def convert_tab_to_csv(input_file):
    """
    Convert .tab file to .csv, extracting specified columns
    """
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found")
        return
    
    # Generate output filename
    base_name = os.path.splitext(input_file)[0]
    output_file = f"{base_name}.csv"
    
    try:
        with open(input_file, 'r', newline='', encoding='utf-8') as infile:
            lines = infile.readlines()
            
            # Skip metadata if needed
            start_line = 0
            if SKIP_METADATA:
                start_line = find_data_start(input_file)
            
            # Parse from the data start line
            data_lines = lines[start_line:]
            
            # Create CSV reader for the data portion
            reader = csv.reader(data_lines, delimiter='\t')
            
            # Read header row
            header = next(reader)
            
            # Find target columns
            col1_idx = None
            col2_idx = None
            
            for i, col_name in enumerate(header):
                if col_name.strip() == COLUMN_1:
                    col1_idx = i
                elif col_name.strip() == COLUMN_2:
                    col2_idx = i
            
            # Check if required columns were found
            if col1_idx is None:
                print(f"Error: '{COLUMN_1}' column not found")
                print(f"Available columns: {header}")
                return
            
            if col2_idx is None:
                print(f"Error: '{COLUMN_2}' column not found")
                print(f"Available columns: {header}")
                return
            
            print(f"Found '{COLUMN_1}' at column {col1_idx + 1}")
            print(f"Found '{COLUMN_2}' at column {col2_idx + 1}")
            
            # Write CSV file
            with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
                writer = csv.writer(outfile)
                
                # Write header
                writer.writerow([COLUMN_1, COLUMN_2])
                
                # Write data rows
                row_count = 0
                for row in reader:
                    if len(row) > max(col1_idx, col2_idx):
                        writer.writerow([row[col1_idx], row[col2_idx]])
                        row_count += 1
                    else:
                        # Handle incomplete rows
                        col1_val = row[col1_idx] if len(row) > col1_idx else ""
                        col2_val = row[col2_idx] if len(row) > col2_idx else ""
                        writer.writerow([col1_val, col2_val])
                        row_count += 1
        
        print(f"Successfully converted '{input_file}' to '{output_file}'")
        print(f"Extracted {row_count} data rows")
        
    except Exception as e:
        print(f"Error processing file: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <input_file.tab>")
        print(f"Current configuration: extracting '{COLUMN_1}' and '{COLUMN_2}'")
        sys.exit(1)
    
    input_file = sys.argv[1]
    print(f"Processing: {input_file}")
    print(f"Extracting columns: '{COLUMN_1}' and '{COLUMN_2}'")
    convert_tab_to_csv(input_file)

if __name__ == "__main__":
    main()

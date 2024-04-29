import os
import pandas as pd

# Folder containing the .txt files
folder_path = '.'

# Placeholder list to collect rows before creating DataFrame
rows_list = []

# Set to hold all unique column names across files
all_columns = set()

# Collect file names
file_names = [file_name for file_name in os.listdir(folder_path) if file_name.endswith('.txt')]

# First pass: Collect all unique column names
for file_name in file_names:
    with open(os.path.join(folder_path, file_name), 'r') as file:
        num_columns = int(file.readline().strip().split(':')[1])
        columns_in_file = [file.readline().strip() for _ in range(num_columns)]
        all_columns.update(columns_in_file)

# Sort columns to maintain a consistent order across the DataFrame
all_columns = sorted(all_columns)

# Second pass: Populate the list with row dictionaries
for file_name in file_names:
    with open(os.path.join(folder_path, file_name), 'r') as file:
        num_columns = int(file.readline().strip().split(':')[1])
        columns_in_file = [file.readline().strip() for _ in range(num_columns)]
        # Initialize a dictionary to hold the order of columns for this file
        file_columns_presence = {column: (i+1 if column in columns_in_file else None) for i, column in enumerate(all_columns)}
        # Add file name to the dictionary
        file_columns_presence['File'] = file_name
        # Append this file's column presence dictionary to the list
        rows_list.append(file_columns_presence)

# Create DataFrame from the list of row dictionaries
columns_presence_df = pd.DataFrame(rows_list)

# Reorder DataFrame to have 'File' column as the first column
columns_presence_df = columns_presence_df[['File'] + all_columns]

# Save the DataFrame to an Excel file
output_excel_path = 'columns_dict.xlsx'
columns_presence_df.to_excel(output_excel_path, index=False)

print(f"Excel file has been created at {output_excel_path}")

import streamlit as st
import zipfile
import os
import pandas as pd
from io import BytesIO

# Function to process a single file based on field values from Excel
# Function to process a single file based on field values from Excel
def process_ies_file(file_content, field_values):
    updated_content = []
    lumcat_value = None

    for line in file_content:
        processed = False  # Track if line is processed
        for key, value in field_values.items():
            if line.startswith(key):
                if value == "REMOVE":
                    # Skip adding this line to updated content
                    processed = True
                    break
                elif value != "KEEP" and pd.notna(value):
                    # Update the line only if value is not "KEEP" and is not NaN
                    if key == "[LUMCAT]":
                        lumcat_value = value  # Store lumcat value for file naming
                    updated_content.append(f"{key} {value}\n")
                    processed = True
                    break
        
        if not processed:
            updated_content.append(line)

    return updated_content, lumcat_value


# Streamlit app setup
st.title("IES File Editor with Excel Configuration")

# Folder path input (simulated for Streamlit usage)
folder_path = st.text_input("Enter the folder path where your IES files are located:")

# Upload Excel file
excel_file = st.file_uploader("Upload Excel file with changes", type=["xlsx"])

# Load Excel data into a DataFrame
if excel_file:
    df_changes = pd.read_excel(excel_file)

# Download Excel template
excel_template = pd.DataFrame({
    'FileName': ['example_file.ies'],
    '[MANUFAC]': ['LEDFLEX'],
    '[LUMCAT]': ['C01181523'],
    '[LAMPCAT]': ['LAMP123'],
    '[TEST]': ['REMOVE'],
    '[TESTLAB]': ['KEEP'],
    '[TESTDATE]': ['2023-08-15'],
    '[ISSUEDATE]': ['2023-08-15 15:09:11'],
    '[NEARFIELD]': [''],
    '[LAMPPOSITION]': ['0,0'],
    '[OTHER]': ['KEEP']
})
st.download_button(
    label="Download Excel Template",
    data=excel_template.to_csv(index=False).encode('utf-8'),
    file_name="IES_template.csv",
    mime="text/csv",
    help="Download the Excel template to know the format for file editing specifications."
)

# File uploader for multiple IES files
uploaded_files = st.file_uploader("Upload IES files", type=["ies"], accept_multiple_files=True)

if uploaded_files and excel_file and folder_path:
    # Initialize a buffer for the zip file
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for uploaded_file in uploaded_files:
            # Check if there are specified changes for this file
            if uploaded_file.name in df_changes['FileName'].values:
                file_changes = df_changes[df_changes['FileName'] == uploaded_file.name].iloc[0]
                field_values = {key: file_changes[key] for key in file_changes.index if pd.notna(file_changes[key])}

                # Read file content and handle decoding
                file_data = uploaded_file.read()
                try:
                    file_content = file_data.decode("utf-8").splitlines()
                except UnicodeDecodeError:
                    # Reset read pointer and retry with a different encoding
                    file_content = file_data.decode("ISO-8859-1").splitlines()

                updated_content, lumcat_value = process_ies_file(file_content, field_values)

                # Use the LUMCAT value or original filename for the new file name
                new_file_name = f"{lumcat_value}_IES.IES" if lumcat_value else uploaded_file.name

                # Add the processed file to the ZIP
                zipf.writestr(new_file_name, "\n".join(updated_content))

    # Provide the ZIP file for download
    st.success(f"Processed {len(uploaded_files)} file(s) successfully!")
    st.download_button(
        label="Download All Processed Files",
        data=zip_buffer.getvalue(),
        file_name="Processed_IES_Files.zip",
        mime="application/zip"
    )

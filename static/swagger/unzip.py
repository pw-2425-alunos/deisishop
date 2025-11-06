import zipfile
import os

# Path to the zip file
zip_file_path = 'index.zip'  # Replace this with your zip file path

# Extracting the zip file into the current directory
with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
    zip_ref.extractall(os.getcwd())  # Extract to the current working directory

print(f"Files extracted to {os.getcwd()}")
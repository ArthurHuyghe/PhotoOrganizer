# Defines the directory where the PS1 file will be, which has the function to discover the file metadata
cd C:\Users\Arthu\Documents\Powershell_folder_automation

# Load the PS1 file
.\Get-FileMetaData.ps1

# Import the PS1 file to access the functions
Import-module .\Get-FileMetaData.ps1 

# Defines the directory where the files will be, to get their metadata
$FilePath = "bestandsadres"

# Defines the directory and name of the file to be exported to the CSV file
$Dir = "CSVadres"

# Loads photo metadata into the variable
$Metadata = Get-FileMetaData -file $FilePath

# Exports the metadata of the files found in the directory, to a CSV file
$Metadata | 
    Export-Csv -Path $Dir -NoTypeInformation -Encoding UTF8
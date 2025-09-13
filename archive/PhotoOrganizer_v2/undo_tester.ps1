$source = 'C:\Users\Arthu\Documents\GitHub\PhotoOrganizer\tests\result'
Get-ChildItem -Attributes !Directory $source -Recurse | 
Foreach-Object {
    if ($_.DirectoryName -eq $source) {
        Write-verbose "Skipping: file is already in the right folder. $_"  -Verbose  
        return
    }
    robocopy $_.DirectoryName $source $_.Name /mov /mt
}

$tailRecursion = {
    param(
        $Path
    )
    foreach ($childDirectory in Get-ChildItem -Force -LiteralPath $Path -Directory) {
        & $tailRecursion -Path $childDirectory.FullName
    }
    $currentChildren = Get-ChildItem -Force -LiteralPath $Path
    $isEmpty = $currentChildren -eq $null
    if ($isEmpty -and ($Path -ne $source)) {     
        Write-Verbose "Removing empty folder at path '${Path}'." -Verbose
        Remove-Item -Force -LiteralPath $Path
    }
    else {
        Write-Verbose "No empty folders." -Verbose
    }
}
& $tailRecursion -Path $source 
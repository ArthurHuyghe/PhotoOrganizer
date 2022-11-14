@{
    Root = 'c:\Users\Arthu\Documents\Powershell_folder_automation\PhotoOrganizerEXE.ps1'
    OutputPath = 'c:\Users\Arthu\Documents\Powershell_folder_automation\out'
    Package = @{
        Enabled = $true
        Obfuscate = $false
        HideConsoleWindow = $true
        DotNetVersion = 'net6.0'
        FileVersion = '1.0.0'
        FileDescription = ''
        ProductName = 'PhotoOrganizer'
        ProductVersion = ''
        Copyright = ''
        RequireElevation = $false
        ApplicationIconPath = 'C:\Users\Arthu\Documents\Powershell_folder_automation\PhotoOrganizer.ico'
        PackageType = 'Console'
        HighDPISupport = $true
        PowerShellVersion = '7.2.6'
        Resources = [string[]]@('PhotoOrganizer.ico', 'sortWindow.xaml', 'ProgressWindow.xaml')
    }
    Bundle = @{
        Enabled = $true
        Modules = $true
        # IgnoredModules = @()
    }
}
        
@{
    Root = 'C:\Users\Arthu\Documents\GitHub\PhotoOrganizer\PhotoOrganizer_v2.ps1'
    OutputPath = 'C:\Users\Arthu\Documents\GitHub\PhotoOrganizer'
    Package = @{
        Enabled = $true
        Obfuscate = $false
        HideConsoleWindow = $false
        DotNetVersion = 'net6.0'
        FileVersion = '2.0.0'
        FileDescription = ''
        ProductName = 'PhotoOrganizer'
        ProductVersion = 'v2'
        Copyright = 'Arthur Huyghe'
        RequireElevation = $false
        ApplicationIconPath = 'PhotoOrganizer_v2(gekleurd).ico'
        PackageType = 'Console'
        HighDPISupport = $true
        PowerShellVersion = '7.2.6'
        Resources = [string[]]@('PhotoOrganizer_v2(gekleurd).ico', 'sortWindow.xaml', 'ProgressWindow.xaml')
    }
    Bundle = @{
        Enabled = $true
        Modules = $true
        # IgnoredModules = @()
    }
}
      
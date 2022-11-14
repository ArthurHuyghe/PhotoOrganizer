#spellchecker
# // cSpell:words synchash, runspace, hashtable, endregion, sortingscript, runspacefactory, Arthu, progressbar, listbox, robocopy, nmbr, progresswindow
# // cSpell:words displaysortwindow, dateformat, psform, Borderbrush, errormessage, sortday, temphash, runspaces, pscustomobject, presentationframework
# // cSpell:words arraylist

Add-Type -AssemblyName System.Windows.Forms
$syncHash = [hashtable]::Synchronized(@{})
# toont sorting window en controleert parameters
function script:displaysortwindow {
    #Xaml importing
    Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName PresentationFramework
$xamlFile = 'C:\Users\Arthu\Documents\Powershell_folder_automation\sortWindow.xaml'
    $inputXAML = Get-Content -Path $xamlFile -Raw
    $inputXAML = $inputXAML -replace 'mc:Ignorable="d"', '' -replace 'x:N', 'N' -replace '^<Win.*', '<Window'
    [XML]$XAML = $inputXAML

    $reader = New-Object -TypeName System.Xml.XmlNodeReader -ArgumentList $XAML
    try {
        $psform = [Windows.Markup.XamlReader]::Load($reader)
    }
    catch {
        Write-Verbose -Message $_.Exception
        throw
    }

    $xaml.SelectNodes('//*[@Name]') | ForEach-Object {
        try {
            Set-Variable -Name ('var_{0}' -f $_.Name) -Value $psform.FindName($_.Name) -ErrorAction Stop
        }
        catch {
            throw
        }
    }
    #code to make the gui react to user input
    #combobox
    $var_dateformat.Items.Add('yyyy/yyyy_MM')
    $var_dateformat.Items.Add('yyyy/yyyy MM')
    $var_dateformat.Items.Add('yyyy/yyyy-MM')
    $var_dateformat.Items.Add('yyyy/MM')
    $var_dateformat.SelectedIndex = 0

    $var_Sortday.Add_Checked({
            $var_dateformat.items.clear()
            $var_dateformat.Items.Add('yyyy/yyyy_MM/yyyy_MM_dd')
            $var_dateformat.Items.Add('yyyy/yyyy MM/yyyy MM dd')
            $var_dateformat.Items.Add('yyyy/yyyy-MM/yyyy-MM-dd')
            $var_dateformat.Items.Add('yyyy/MM/dd')
            $var_dateformat.SelectedIndex = 0
        })

    $var_Sortday.Add_Unchecked({
            $var_dateformat.items.clear()
            $var_dateformat.Items.Add('yyyy/yyyy_MM')
            $var_dateformat.Items.Add('yyyy/yyyy MM')
            $var_dateformat.Items.Add('yyyy/yyyy-MM')
            $var_dateformat.Items.Add('yyyy/MM')
            $var_dateformat.SelectedIndex = 0
        })
    # prevent script from running if not checked
    $script:continue = 'nee'
    $script:error_source_folder = 'nee'
    $script:error_dest_folder = 'nee'
    # annuleer button
    $var_btn_annuleer.Add_Click({ 
            $script:continue = 'nee'
            $psform.Close()
        })

    # sorteer button
    $var_btn_sort.Add_Click({
            # get parameters
            $script:path_source_folder = $var_txt_source_folder.Text
            $script:path_dest_folder = $var_txt_dest_folder.Text
            # parameter controle
            if (
                $path_source_folder -and $path_dest_folder -and
                (Test-Path -Path $path_source_folder) -and (Test-Path -Path $path_dest_folder)
            ) {
                $script:continue = 'ja'
                $psform.Close()
            }
            else {
                $script:continue = 'nee'
                if (-not $path_source_folder) {
                    $var_txt_source_folder.Borderbrush = '#FFEA0909'
                    $var_errormessage.visibility = 'Visible'
                    $script:error_source_folder = 'ja'
                }
                if (-not $path_dest_folder) {
                    $var_txt_dest_folder.Borderbrush = '#FFEA0909'
                    $var_errormessage.visibility = 'Visible'
                    $script:error_dest_folder = 'ja'
                }
                if (-not (Test-Path -Path $path_source_folder)) {
                    $var_txt_source_folder.Borderbrush = '#FFEA0909'
                    $var_errormessage.visibility = 'Visible'
                    $script:error_source_folder = 'ja'
                }
                if (-not (Test-Path -Path $path_dest_folder)) {
                    $var_txt_dest_folder.Borderbrush = '#FFEA0909'
                    $var_errormessage.visibility = 'Visible'
                    $script:error_dest_folder = 'ja'
                }
            }
        })
    # laat error verdwijnen bij wijziging
    $var_txt_source_folder.Add_TextChanged({
            # get parameters
            $script:path_source_folder = $var_txt_source_folder.Text
            $script:path_dest_folder = $var_txt_dest_folder.Text
            # parameter controle
            if ($error_source_folder -eq 'ja') {
                $var_txt_source_folder.Borderbrush = '#FFABADB3' 
            }
            if ($error_source_folder -eq 'nee' -and $error_dest_folder -eq 'nee') {
                $var_errormessage.visibility = 'Hidden'
            }
            $script:error_source_folder = 'nee'
        })
    $var_txt_dest_folder.Add_TextChanged({
            # get parameters
            $script:path_source_folder = $var_txt_source_folder.Text
            $script:path_dest_folder = $var_txt_dest_folder.Text
            $script:dateformat_combobox = $var_dateformat.SelectedItem
            # parameter controle 
            if ($error_dest_folder -eq 'ja') {
                $var_txt_dest_folder.Borderbrush = '#FFABADB3'
            }    
            if ($error_source_folder -eq 'nee' -and $error_dest_folder -eq 'nee') {
                $var_errormessage.visibility = 'Hidden'
            } 
            $script:error_dest_folder = 'nee'
        })
    # te sorteren map button
    $var_btn_source_folder.Add_Click({
            $source_folder = New-Object -TypeName System.Windows.Forms.FolderBrowserDialog
            $source_folder.ShowDialog()
            $var_txt_source_folder.Text = $source_folder.SelectedPath
        })
    
    # map waarin gesorteerd wordt button
    $var_btn_dest_folder.Add_Click({
            $dest_folder = New-Object -TypeName System.Windows.Forms.FolderBrowserDialog
            $dest_folder.ShowDialog()
            $var_txt_dest_folder.Text = $dest_folder.SelectedPath
        })

    # show dialog
    $psform.Activate()
    $psform.ShowDialog()    
}
# display sorting window
displaysortwindow

<#
        | Script |
parameters voor in te vullen bij het script zijn:
    $path_source_folder
    $path_dest_folder
    $dateformat_combobox
#>
# controleert of script uitgevoerd mag worden
if ($continue -eq 'ja') {
    # set parameters
    $syncHash.Add('source', $path_source_folder)
    $syncHash.Add('dest', $path_dest_folder)
    $syncHash.Add('format', $dateformat_combobox)
    #progressbar script
    #region runspace1 : GUI
    $Runspace1 = [runspacefactory]::CreateRunspace()
    $Runspace1.Name = 'progressGUI'
    $Runspace1.ApartmentState = 'STA'
    $Runspace1.ThreadOptions = 'ReuseThread'
    $Runspace1.Open()
    $Runspace1.SessionStateProxy.SetVariable('syncHash', $syncHash)
    $code = {
 
        # Build the GUI
        Add-Type -AssemblyName PresentationFramework
      $xamlFile = 'C:\Users\Arthu\Documents\Powershell_folder_automation\ProgressWindow.xaml'
        $inputXAML = Get-Content -Path $xamlFile -Raw
        $inputXAML = $inputXAML -replace 'mc:Ignorable="d"', '' -replace 'x:N', 'N' -replace '^<Win.*', '<Window'
        [XML]$XAML = $inputXAML

    
        $reader = (New-Object -TypeName System.Xml.XmlNodeReader -ArgumentList $xaml)
        $syncHash.Window = [Windows.Markup.XamlReader]::Load( $reader )
        # Load al the variables in the hashtable
        $xaml.SelectNodes('//*[@Name]') | ForEach-Object {
            # Find all of the form types and add them as members to the syncHash
            $syncHash.Add(('var_{0}' -f $_.Name), $syncHash.Window.FindName($_.Name) )

        }
    
        # Set the progress variables
        # bereken de hoeveelheid bestanden en zet instellingen progressbar en listbox
        $syncHash.files_in_folder = Get-ChildItem -Attributes !Directory -Path $syncHash.source -Recurse | Measure-Object | ForEach-Object { $_.Count }
        $syncHash.progress_made_nmbr = 0
        $syncHash.progress_made_percentage = [math]::Round(($synchash.progress_made_nmbr / $synchash.files_in_folder) * 100) 
        $synchash.var_txt_progress.Text = '{0} van de {1}:    {2}%' -f $synchash.progress_made_nmbr, $synchash.files_in_folder, $synchash.progress_made_percentage
        $syncHash.var_Progressbar.Maximum = $syncHash.files_in_folder
        $syncHash.var_Progressbar.Value = 0
        $syncHash.var_Progress_output.Items.Clear()
            
        
        # shows the form and cleans the runspace after its closed
        $syncHash.window.Activate()
        $syncHash.Window.ShowDialog()
        $syncHash.Error = $Error
        $job1_done = $Runspace1.EndInvoke()
        $Runspace1.Close()
        $Runspace1.Dispose()
 
    }
    $PSinstance1 = [powershell]::Create().AddScript($Code)
    $PSinstance1.Runspace = $Runspace1
    $job1 = $PSinstance1.BeginInvoke()
    #endregion Runspace1 
    #moving script
    #region runspace2: sortingscript
    $Runspace2 = [runspacefactory]::CreateRunspace()
    $Runspace2.Name = 'MovingScript'
    $Runspace2.ApartmentState = 'STA'
    $Runspace2.ThreadOptions = 'ReuseThread'
    $Runspace2.Open()
    $Runspace2.SessionStateProxy.SetVariable('syncHash', $syncHash)
    $code = {

        $shell = New-Object -ComObject Shell.Application

        function script:Get-File-Date {
            [CmdletBinding()]
            Param (
                $object
            )

            $dir = $shell.NameSpace( $object.Directory.FullName )
            $file = $dir.ParseName( $object.Name )

            # First see if we have Date Taken, which is at index 12
            $date = Get-Date-Property-Value -dir $dir -file $file -index 12

            if ($null -eq $date) {
                # If we don't have Date Taken, then find the oldest date from all date properties
                0..287 | ForEach-Object {
                    $name = $dir.GetDetailsOf($dir.items, $_)

                    if ( $name -match '(date)|(created)') {
            
                        # Only get value if date field because the GetDetailsOf call is expensive
                        $tmp = Get-Date-Property-Value -dir $dir -file $file -index $_
                        if ( ($null -ne $tmp) -and (($null -eq $date) -or ($tmp -lt $date))) {
                            $date = $tmp
                        }
                    }
                }
            }
            return $date
        }

        function script:Get-Date-Property-Value {
            [CmdletBinding()]

            Param (
                $dir,
                $file,
                $index
            )

            $value = ($dir.GetDetailsOf($file, $index) -replace "`u{200e}") -replace "`u{200f}"
            if ($value -and $value -ne '') {
                return [DateTime]::ParseExact($value, 'g', $null)
            }
            return $null
        }

        function script:UpdateProgressBar {
            # update progress bar
            $syncHash.progress_made_nmbr += 1
            $syncHash.progress_made_percentage = [math]::Round(($syncHash.progress_made_nmbr / $syncHash.files_in_folder) * 100)
            $syncHash.Window.Dispatcher.invoke(
                [action] {
                    $synchash.var_txt_progress.Text = '{0} van de {1}:    {2}%' -f $syncHash.progress_made_nmbr, $syncHash.files_in_folder, $syncHash.progress_made_percentage
                    $syncHash.var_Progressbar.Value = $synchash.progress_made_nmbr
                },
                'Normal'
            )            
        }
        # start moving proces 
        Get-ChildItem -Attributes !Directory -Path $syncHash.source -Recurse | Foreach-Object {
            $syncHash.Window.Dispatcher.invoke(
                [action] { 
                    $syncHash.var_Progress_output.AppendText(("Processing {0} `r`n" -f $_))
                    $syncHash.var_Progress_output.ScrollToEnd()
                },
                'Normal'
            )
            $date = Get-File-Date -object $_

            if ($date) {
    
                $destinationFolder = Get-Date -Date $date -Format $syncHash.format
                $destinationPath = Join-Path -Path $syncHash.dest -ChildPath $destinationFolder   

                # See if the destination file exists and rename until we get a unique name
                $newFullName = Join-Path -Path $destinationPath -ChildPath $_.Name
                if ($_.FullName -eq $newFullName) {
                    $syncHash.Window.Dispatcher.invoke(
                        [action] { 
                            $syncHash.var_Progress_output.AppendText(("Skipping:   {0}, Source file and destination files are at the same location. `r`n" -f $_))
                            $syncHash.var_Progress_output.ScrollToEnd()
                        },
                        'Normal'
                    )
                    UpdateProgressBar  
                    return
                }

                $newNameIndex = 1
                $newName = $_.Name

                while (Test-Path -Path $newFullName) {
                    $newName = ($_.BaseName + ('_{0}' -f $newNameIndex) + $_.Extension) 
                    $newFullName = Join-Path -Path $destinationPath -ChildPath $newName  
                    $newNameIndex += 1   
                }

                # If we have a new name, then we need to rename in current location before moving it.
                if ($newNameIndex -gt 1) {
                    Rename-Item -Path $_.FullName -NewName $newName
                }

                $syncHash.Window.Dispatcher.invoke(
                    [action] { 
                        $syncHash.var_Progress_output.AppendText(("Moving      {0} to {1} `r`n" -f $_, $newFullName))
                        $syncHash.var_Progress_output.ScrollToEnd()
                    },
                    'Normal'
                )
                # Create the destination directory if it doesn't exist
                if (!(Test-Path -Path $destinationPath)) {
                    New-Item -ItemType Directory -Force -Path $destinationPath
                }

                & "$env:windir\system32\robocopy.exe" $_.DirectoryName $destinationPath $newName /mov
                UpdateProgressBar
            }
        }
        $syncHash.Window.Dispatcher.invoke(
            [action] {
                $syncHash.var_task_preforming.Text = 'Klaar!'                 
            },
            'Normal'
        )
        # cleans the runspace after its closed
        $syncHash.Error = $Error
        $job2_done = $Runspace2.EndInvoke()
        $Runspace2.Close()
        $Runspace2.Dispose()

    }
    $PSinstance2 = [powershell]::Create().AddScript($Code)
    $PSinstance2.Runspace = $Runspace2
    $job2 = $PSinstance2.BeginInvoke()
}

# SIG # Begin signature block
# MIIGvwYJKoZIhvcNAQcCoIIGsDCCBqwCAQExCzAJBgUrDgMCGgUAMGkGCisGAQQB
# gjcCAQSgWzBZMDQGCisGAQQBgjcCAR4wJgIDAQAABBAfzDtgWUsITrck0sYpfvNR
# AgEAAgEAAgEAAgEAAgEAMCEwCQYFKw4DAhoFAAQU/p4la57jbHrx/AFh8Sv3sB8v
# XUagggPZMIID1TCCAr2gAwIBAgIQ2RhYSwKRotOlyN+pFZWpsTANBgkqhkiG9w0B
# AQwFADAbMRkwFwYDVQQDExBTb2xhcldpbmRzLU9yaW9uMCAXDTIyMDEwNDE0MDY0
# N1oYDzIwNTIwMTA2MTUwNjQ0WjBMMUowSAYDVQQDE0FTb2xhcldpbmRzIEFnZW50
# IFByb3Zpc2lvbiAtIGRjY2Q5NDM3LTNhZTAtNDBhYy1iZGVkLTViMmQ0OTM1MTdm
# NDCCAaIwDQYJKoZIhvcNAQEBBQADggGPADCCAYoCggGBAMwonG+Oege418lNfzIe
# 4kfhILNZVq458VlXnguXpyAG7l4xAlryenugdbPkHwBzK1/HGq8BeTSIYjMBNLvN
# +eIbXgMs01VrbPV59n/ygOIUv8vj8JQtq1BWB0pr9/2yVpanQi/Eyj2/8W9+OWP/
# ptKIaAtu6aFrkA/v9qLDg2Xancc4RkUv/0+aOLLXWkBbFrBkUS4Qag1OXoNA5Ssn
# 5EZdNRI1DPhv1k/A4pQMTwGJYIE69poPUPcOweOLFsvGS9plvNfzWwrApSyWH6PS
# gZAxgMuToB9YNooRxRM9v1pIYQeQNWutNejsbyhTKcvmMHs3E0rs/HpuFgJloMMt
# sixVw64xvAXqZYDpKai8rC/fxRzODn3ttnp1g1i6rwp1HCEb94odKQ5iv0OQXLMz
# aJNZYFQSQ3sKjOQ34vYE0pL5M8ZkyvRUqwJ4GV8PWRamLJBC5YlV8NjcNkrZAZ1K
# dl6pvQnbMGC3SiLWm9+ymjtGXOpto2DQRuWawCpSqRbLMQIDAQABo2IwYDAdBgNV
# HQ4EFgQUnmdwd6R819X4sw2elZGIpWlTmwYwCwYDVR0PBAQDAgO4MCcGA1UdJQQg
# MB4GCCsGAQUFBwMBBggrBgEFBQcDAgYIKwYBBQUHAwMwCQYDVR0TBAIwADANBgkq
# hkiG9w0BAQsFAAOCAQEAdwVIELZ2bf1Si7Vkn/+ft5uI7818I4QgiQG3r2/k9HhU
# JxLc4JfgFI02hIUhEkUJF43M9EXFyB/Z1uSK5ua+X54aO/FFFD47DzsTK4yxB5Cq
# cUSFKVlWZV3gQcC1ocshbBUH9ISgVRe0DMvMO+NxAsXm5zgC/OdUgkju00jG00Tw
# vadZfzjjSM35+UUX5McW6qEvE9kHUhKGclNfVIyuTrad5Cr0qYrhjXTDlZCQMC8p
# TJN06oggucF1lp0YBTkjLz+5uzDD5O71mluv99tTrYexyXAaMqCFL5oSAHasMMnR
# WG9HcDJOGDsGHDs93HNL2mepv204C7u5eRcz1d/j1TGCAlAwggJMAgEBMC8wGzEZ
# MBcGA1UEAxMQU29sYXJXaW5kcy1PcmlvbgIQ2RhYSwKRotOlyN+pFZWpsTAJBgUr
# DgMCGgUAoHgwGAYKKwYBBAGCNwIBDDEKMAigAoAAoQKAADAZBgkqhkiG9w0BCQMx
# DAYKKwYBBAGCNwIBBDAcBgorBgEEAYI3AgELMQ4wDAYKKwYBBAGCNwIBFTAjBgkq
# hkiG9w0BCQQxFgQUeIFVtGiatq+23Z2NcW0ATcpWy9gwDQYJKoZIhvcNAQEBBQAE
# ggGAYwmsQ90D5JqHLGoTMM9dw2OxU/A+9yF3SXNAxReFqVgE8kJpcL1dWCtKot/a
# 0meK/PeqAOdWwLzp819FFef4jIDq68o4xZEgGV2+LaZv1MKg7qbi8bhnEkzw8K/8
# 4Ynhvu5W7x6a4KYW6yNAY0kkG4nSmv6X7GH4/4E4hDvYyU1Tqarl/asuA6chK3mW
# ozJVem2oehdm67DwG4h2YWGyVAjtEJN/hN05XdfMLqZCcaUVkHSm362tYjwrn+xF
# S9m0rcKEUmn04ApiHFF0N+QoM7XimbWWGdIGJq6MAaSRUlNz1jNY9sKKOC8zAP5P
# VOsPOcEpmWlnyvuLgE0mHoZoQiFX1XgSWACqMItJwKhsDOUnkJmmkWIBj1YWwwds
# F7Y+jhqFGwwkhiVCVGVUJHz2rkfmXq1cUlSP4QNZ4HZ6APvckcvhojZLBFQor5UJ
# wMS+6DYPrLm4DAO7aqVJzXnzx9u2PaBfyx/LLvdz2KRuKSkAGjHcWNM7MFaewjpv
# CdBC
# SIG # End signature block

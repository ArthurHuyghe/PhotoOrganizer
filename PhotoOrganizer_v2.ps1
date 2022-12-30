#spellchecker
# // cSpell:words synchash, runspace, hashtable, endregion, sortingscript, runspacefactory, Arthu, progressbar, listbox, robocopy, nmbr, progresswindow
# // cSpell:words displaysortwindow, dateformat, psform, Borderbrush, errormessage, sortday, temphash, runspaces, pscustomobject, presentationframework
# // cSpell:words arraylist

Add-Type -AssemblyName System.Windows.Forms, PresentationFramework
$syncHash = [hashtable]::Synchronized(@{})
function Get-Resource {
    param($Name)
    
    $ProcessName = (Get-Process -Id $PID).Name
    try {
        $Stream = [System.Reflection.Assembly]::GetEntryAssembly().GetManifestResourceStream("$ProcessName.g.resources")
        $KV = [System.Resources.ResourceReader]::new($Stream) | Where-Object Key -EQ $Name
        $Stream = $KV.Value
    }
    catch {}

    if (-not $Stream) {
        $Stream = [IO.File]::OpenRead("$PSScriptRoot\$Name")
    }

    $Stream
}
# toont sorting window en controleert parameters
function script:displaysortwindow {
    #Xaml importing
    $xamlFile = Get-Resource -Name 'sortWindow.xaml'
    $xamlFile = $xamlFile.Name
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
    $var_dateformat.items.clear()
    $var_dateformat.Items.Add('yyyy/MM_yyyy')
    $var_dateformat.Items.Add('yyyy/MM-yyyy')
    $var_dateformat.Items.Add('yyyy/MM yyyy')
    $var_dateformat.Items.Add('yyyy/MM')
    $var_dateformat.SelectedIndex = 0

    $var_Sortday.Add_Checked({
            $current_selection = $var_dateformat.SelectedIndex
            $var_dateformat.items.clear()
            $var_dateformat.Items.Add('yyyy/MM_yyyy/dd_MM yyyy')
            $var_dateformat.Items.Add('yyyy/MM-yyyy/dd-MM-yyyy')
            $var_dateformat.Items.Add('yyyy/MM yyyy/dd MM yyyy')
            $var_dateformat.Items.Add('yyyy/MM/dd')
            $var_dateformat.SelectedIndex = $current_selection
        })

    $var_Sortday.Add_Unchecked({
            $current_selection = $var_dateformat.SelectedIndex
            $var_dateformat.items.clear()
            $var_dateformat.Items.Add('yyyy/MM_yyyy')
            $var_dateformat.Items.Add('yyyy/MM-yyyy')
            $var_dateformat.Items.Add('yyyy/MM yyyy')
            $var_dateformat.Items.Add('yyyy/MM')
            $var_dateformat.SelectedIndex = $current_selection
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
            $script:dateformat_combobox = $var_dateformat.SelectedItem
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
            $script:dateformat_combobox = $var_dateformat.SelectedItem
            # parameter controle
            if ($error_source_folder -eq 'ja') {
                $var_txt_source_folder.Borderbrush = '#FFABADB3' 
            }
            if (($error_source_folder -eq 'nee') -and { $error_dest_folder -eq 'nee' }) {
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
    # clean up checkbox
    $Script:CleanFolders = 'nee'
    $var_clean_up.Add_Checked({ $Script:CleanFolders = 'ja' })
    $var_clean_up.Add_UnChecked({ $Script:CleanFolders = 'nee' })
    # add icon
    $bitmap = New-Object System.Windows.Media.Imaging.BitmapImage
    $bitmap.BeginInit()
    $bitmap.StreamSource = Get-Resource -Name "PhotoOrganizer_v2(gekleurd).ico"
    $bitmap.EndInit()
    $bitmap.Freeze()
    $psform.icon = $bitmap
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
    $CleanFolders
#>
# controleert of script uitgevoerd mag worden
if ($continue -eq 'ja') {
    # set parameters
    $syncHash.Add('source', $path_source_folder)
    $syncHash.Add('dest', $path_dest_folder)
    $syncHash.Add('format', $dateformat_combobox)
    # add icon and xaml to synchash
    $bitmap = New-Object System.Windows.Media.Imaging.BitmapImage
    $bitmap.BeginInit()
    $bitmap.StreamSource = Get-Resource -Name "PhotoOrganizer_v2(gekleurd).ico"
    $bitmap.EndInit()
    $bitmap.Freeze()
    $syncHash.Add('bitmap', $bitmap)
    $xamlFile = Get-Resource -Name 'ProgressWindow.xaml'
    $xamlFile = $xamlFile.Name
    $syncHash.Add('xamlFile', $xamlFile)

    #gui to different thread
    $Runspace = [runspacefactory]::CreateRunspace()
    $Runspace.ApartmentState = "STA"
    $Runspace.ThreadOptions = "ReuseThread"         
    $Runspace.Open()
    $Runspace.SessionStateProxy.SetVariable("syncHash", $syncHash)          
    $PowerShell = [PowerShell]::Create().AddScript({
            try {
                #progressbar script
                # Build the GUI
                $inputXAML = Get-Content -Path $syncHash.xamlFile -Raw
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
                
                # add icon
                $syncHash.Window.icon = $syncHash.bitmap
                # shows the form 
                $syncHash.window.Activate()
                $syncHash.Window.ShowDialog()
            }
            finally {
                # save all the errors that have happend
                $syncHash.Error = $Error
            }
        })
    $PowerShell.Runspace = $Runspace
    $Job = $PowerShell.BeginInvoke()

    # sorting script
    $shell = New-Object -ComObject Shell.Application

    function Get-File-Date {
        [CmdletBinding()]
        Param (
            $object
        )

        $dir = $shell.NameSpace( $object.Directory.FullName )
        $file = $dir.ParseName( $object.Name )

        # First see if we have Date Taken, which is at index 12
        $date = Get-Date-Property-Value $dir $file 12

        if ($null -eq $date) {
            # If we don't have Date Taken, then find the oldest date from all date properties
            0..287 | ForEach-Object {
                $name = $dir.GetDetailsof($dir.items, $_)

                if ( $name -match '(date)|(created)') {
            
                    # Only get value if date field because the GetDetailsOf call is expensive
                    $tmp = Get-Date-Property-Value $dir $file $_
                    if ( ($null -ne $tmp) -and (($null -eq $date) -or ($tmp -lt $date))) {
                        $date = $tmp
                    }
                }
            }
        }
        return $date
    }

    function Get-Date-Property-Value {
        [CmdletBinding()]

        Param (
            $dir,
            $file,
            $index
        )

        $value = ($dir.GetDetailsof($file, $index) -replace "`u{200e}") -replace "`u{200f}"
        if ($value -and $value -ne '') {
            return [DateTime]::ParseExact($value, "g", $null)
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
    Get-ChildItem -Attributes !Directory $syncHash.source -Recurse | 
    Foreach-Object {

        $syncHash.Window.Dispatcher.invoke(
            [action] {
                $syncHash.var_Progress_output.AppendText(("Processing {0} `r`n" -f $_))
                $syncHash.var_Progress_output.ScrollToEnd()   
            },
            'Normal'
        )

        $date = Get-File-Date $_

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
                $newName = ($_.BaseName + "_$newNameIndex" + $_.Extension) 
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
            if (!(Test-Path $destinationPath)) {
                New-Item -ItemType Directory -Force -Path $destinationPath
            }

            robocopy $_.DirectoryName $destinationPath $newName /mov /mt
            UpdateProgressBar
        }
    }
    if ($CleanFolders -eq 'ja') {
        $syncHash.Window.Dispatcher.invoke(
            [action] {
                $syncHash.var_task_preforming.Text = 'Cleaning up empty folders...' 
                $syncHash.Window.Title = 'Cleaning up empty folders...'                
            },
            'Normal'
        )
        if ($path_source_folder -ne $path_dest_folder) {
            Get-ChildItem -Attributes !Directory $path_source_folder -Recurse | 
            Foreach-Object {
                if ($_.DirectoryName -eq $path_source_folder) {
                    Write-verbose "Skipping: file is already in the right folder. $_"  -Verbose 
                    $syncHash.Window.Dispatcher.invoke(
                        [action] {
                            $syncHash.var_Progress_output.AppendText(("Skipping: file is already in the right folder. $_ `r`n"))
                            $syncHash.var_Progress_output.ScrollToEnd()
                        },
                        'Normal'
                    )
                    return
                }
                robocopy $_.DirectoryName $path_source_folder $_.Name /mov /mt
            }
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
            if ($isEmpty -and ($Path -ne $path_source_folder)) {     
                Write-Verbose "Removing empty folder at path '${Path}'." -Verbose
                $syncHash.Window.Dispatcher.invoke(
                    [action] {
                        $syncHash.var_Progress_output.AppendText(("Removing empty folder at path '${Path}'.`r`n"))
                        $syncHash.var_Progress_output.ScrollToEnd()
                    },
                    'Normal'
                )
                Remove-Item -Force -LiteralPath $Path
            }
            else {
                Write-Verbose "Not an empty folder: $Path" -Verbose
                $syncHash.Window.Dispatcher.invoke(
                    [action] {
                        $syncHash.var_Progress_output.AppendText(("Not an empty folder: $Path`r`n"))
                        $syncHash.var_Progress_output.ScrollToEnd()
                    },
                    'Normal'
                )
            }
        }
        & $tailRecursion -Path $path_source_folder 
    }
    $syncHash.Window.Dispatcher.invoke(
        [action] {
            $syncHash.var_task_preforming.Text = 'Klaar!' 
            $syncHash.Window.Title = 'PhotoOrganizer - Klaar!'                
        },
        'Normal'
    )
    $PowerShell.EndInvoke($Job)
    $Runspace.Dispose()
    $PowerShell.Dispose()
}
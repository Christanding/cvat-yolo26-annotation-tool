param([Parameter(Mandatory = $true)][string]$InstallDir)

. (Join-Path $PSScriptRoot 'Common.ps1')

Start-DockerEngine | Out-Null
Invoke-AppCompose -InstallDir $InstallDir -Arguments @('up', '-d')
Wait-AppReady
Open-AppBrowser

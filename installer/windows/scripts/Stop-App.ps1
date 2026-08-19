param(
    [Parameter(Mandatory = $true)][string]$InstallDir,
    [switch]$RemoveContainers
)

. (Join-Path $PSScriptRoot 'Common.ps1')

try {
    Start-DockerEngine | Out-Null
    if ($RemoveContainers) {
        Invoke-AppCompose -InstallDir $InstallDir -Arguments @('down', '--remove-orphans')
    } else {
        Invoke-AppCompose -InstallDir $InstallDir -Arguments @('stop')
    }
} catch {
    if (-not $RemoveContainers) {
        throw
    }
}

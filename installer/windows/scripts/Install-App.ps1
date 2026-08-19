param(
    [Parameter(Mandatory = $true)][string]$InstallDir,
    [Parameter(Mandatory = $true)][string]$WorkspaceRoot,
    [Parameter(Mandatory = $true)][string]$AppVersion
)

. (Join-Path $PSScriptRoot 'Common.ps1')

function Assert-MinimumFreeSpace {
    param([string]$Path, [long]$RequiredBytes, [string]$Description)

    $root = [IO.Path]::GetPathRoot([IO.Path]::GetFullPath($Path))
    $drive = [IO.DriveInfo]::new($root)
    if ($drive.AvailableFreeSpace -lt $RequiredBytes) {
        $requiredGB = [Math]::Ceiling($RequiredBytes / 1GB)
        throw "$Description 所在磁盘至少需要 $requiredGB GB 可用空间。"
    }
}

function Assert-SystemRequirements {
    if (-not [Environment]::Is64BitOperatingSystem -or $env:PROCESSOR_ARCHITECTURE -ne 'AMD64') {
        throw '仅支持 Windows 10/11 x64。'
    }

    $version = [Environment]::OSVersion.Version
    if ($version.Major -ne 10 -or $version.Build -lt 19045 -or
        ($version.Build -ge 22000 -and $version.Build -lt 22631)) {
        throw '系统版本不符合 Docker Desktop 当前要求：Windows 10 22H2 或 Windows 11 23H2 及以上。'
    }

    $computer = Get-CimInstance Win32_ComputerSystem
    if ([long]$computer.TotalPhysicalMemory -lt 8GB) {
        throw '物理内存不足 8 GB。'
    }

    $processors = Get-CimInstance Win32_Processor
    if ($processors -and ($processors | Where-Object { $_.VirtualizationFirmwareEnabled -eq $false })) {
        throw '未检测到 BIOS/UEFI 硬件虚拟化，请启用后重试。'
    }

    $wslVersionOutput = (& wsl.exe --version 2>&1) | Out-String
    if ($LASTEXITCODE -ne 0 -or $wslVersionOutput -notmatch 'WSL.*?([0-9]+\.[0-9]+\.[0-9]+)') {
        throw '未检测到可用的 WSL 2，请先完成 WSL 安装或更新。'
    }
    if ([Version]$Matches[1] -lt [Version]'2.1.5') {
        throw 'WSL 版本低于 2.1.5，请先更新 WSL。'
    }

    New-Item -ItemType Directory -Path $WorkspaceRoot -Force | Out-Null
    $probe = Join-Path $WorkspaceRoot ('.cvat-write-test-' + [Guid]::NewGuid().ToString('N'))
    try {
        [IO.File]::WriteAllText($probe, 'ok')
    } finally {
        if (Test-Path -LiteralPath $probe) {
            Remove-Item -LiteralPath $probe -Force
        }
    }

    $archive = Join-Path $InstallDir 'runtime\images.tar'
    if (-not (Test-Path -LiteralPath $archive -PathType Leaf)) {
        throw '离线镜像归档缺失，请使用完整的安装包。'
    }
    Assert-MinimumFreeSpace -Path $env:SystemDrive -RequiredBytes ((Get-Item $archive).Length * 2 + 5GB) -Description '系统盘'
    Assert-MinimumFreeSpace -Path $WorkspaceRoot -RequiredBytes 5GB -Description '工作区'
}

Assert-SystemRequirements
$docker = Start-DockerEngine

$stateDir = Join-Path $WorkspaceRoot '.cvat-local'
foreach ($directory in @('data', 'keys', 'logs', 'postgres', 'redis')) {
    New-Item -ItemType Directory -Path (Join-Path $stateDir $directory) -Force | Out-Null
}

$composeWorkspace = ([IO.Path]::GetFullPath($WorkspaceRoot)).Replace('\', '/')
$composeState = ([IO.Path]::GetFullPath($stateDir)).Replace('\', '/')
function ConvertTo-DotEnvLiteral([string]$Value) {
    return "'" + $Value.Replace("'", "\'") + "'"
}
$environment = @(
    'CVAT_HOST=localhost',
    "APP_VERSION=$AppVersion",
    "CVAT_WORKSPACE_ROOT=$(ConvertTo-DotEnvLiteral $composeWorkspace)",
    "CVAT_STATE_DIR=$(ConvertTo-DotEnvLiteral $composeState)"
)
[IO.File]::WriteAllLines(
    (Join-Path $InstallDir '.env'),
    $environment,
    [Text.UTF8Encoding]::new($false)
)

& $docker load --input (Join-Path $InstallDir 'runtime\images.tar')
if ($LASTEXITCODE -ne 0) {
    throw '离线容器镜像导入失败。'
}

Invoke-AppCompose -InstallDir $InstallDir -Arguments @('up', '-d')
Wait-AppReady

$installStateFile = Join-Path $stateDir 'install-state.json'
if (-not (Test-Path -LiteralPath $installStateFile)) {
    $username = $env:CVAT_LOCAL_USERNAME
    $password = $env:CVAT_LOCAL_PASSWORD
    if (-not $username -or -not $password) {
        throw '安装程序未提供本地账户信息。'
    }
    $password | & $docker exec -i cvat_server python manage.py create_local_account --username $username
    if ($LASTEXITCODE -ne 0) {
        throw '本地账户创建失败。'
    }
    @{
        account = $username
        version = $AppVersion
    } | ConvertTo-Json | Set-Content -LiteralPath $installStateFile -Encoding UTF8
} else {
    $installState = Get-Content -LiteralPath $installStateFile -Raw | ConvertFrom-Json
    $installState.version = $AppVersion
    $installState | ConvertTo-Json | Set-Content -LiteralPath $installStateFile -Encoding UTF8
}

Open-AppBrowser

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$script:ComposeProject = 'yolo26-local-annotator'
$script:AppUrl = 'http://localhost:8080'

function Resolve-DockerExecutable {
    $command = Get-Command 'docker.exe' -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $candidates = @(
        (Join-Path $env:ProgramFiles 'Docker\Docker\resources\bin\docker.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\resources\bin\docker.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Docker\Docker\resources\bin\docker.exe')
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return $candidate
        }
    }
    throw '未检测到 Docker Desktop。请先使用官方安装程序完成安装并接受许可条款。'
}

function Test-DockerEngine {
    param([Parameter(Mandatory = $true)][string]$DockerExecutable)

    & $DockerExecutable info *> $null
    if ($LASTEXITCODE -ne 0) {
        return $false
    }
    $engineType = (& $DockerExecutable info --format '{{.OSType}}').Trim()
    if ($engineType -ne 'linux') {
        throw 'Docker Desktop 当前使用 Windows 容器。请切换到 Linux 容器后重试。'
    }
    return $true
}

function Start-DockerEngine {
    param([int]$TimeoutSeconds = 180)

    $docker = Resolve-DockerExecutable
    if (Test-DockerEngine -DockerExecutable $docker) {
        return $docker
    }

    $desktopCandidates = @(
        (Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\Docker Desktop.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Docker\Docker\Docker Desktop.exe')
    )
    $desktop = $desktopCandidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
    if (-not $desktop) {
        throw '已找到 Docker 命令，但未找到 Docker Desktop 主程序。'
    }

    Start-Process -FilePath $desktop | Out-Null
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    do {
        Start-Sleep -Seconds 2
        if (Test-DockerEngine -DockerExecutable $docker) {
            return $docker
        }
    } while ([DateTime]::UtcNow -lt $deadline)

    throw 'Docker Desktop 未能在 3 分钟内就绪。请打开 Docker Desktop，确认已接受许可条款并使用 WSL 2 后重试。'
}

function Invoke-AppCompose {
    param(
        [Parameter(Mandatory = $true)][string]$InstallDir,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    $docker = Resolve-DockerExecutable
    $runtime = Join-Path $InstallDir 'runtime'
    $composeArguments = @(
        'compose', '--env-file', (Join-Path $InstallDir '.env'),
        '-p', $script:ComposeProject,
        '-f', (Join-Path $runtime 'docker-compose.yml'),
        '-f', (Join-Path $runtime 'docker-compose.local.yml')
    ) + $Arguments
    & $docker @composeArguments
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose 执行失败，退出码：$LASTEXITCODE"
    }
}

function Wait-AppReady {
    param([int]$TimeoutSeconds = 300)

    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    do {
        try {
            $response = Invoke-WebRequest -Uri "$script:AppUrl/api/server/about" -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                return
            }
        } catch {
            Start-Sleep -Seconds 2
        }
    } while ([DateTime]::UtcNow -lt $deadline)

    throw '服务未能在 5 分钟内就绪，请检查 Docker Desktop 状态。'
}

function Open-AppBrowser {
    $edgeCandidates = @(
        (Join-Path ${env:ProgramFiles(x86)} 'Microsoft\Edge\Application\msedge.exe'),
        (Join-Path $env:ProgramFiles 'Microsoft\Edge\Application\msedge.exe')
    )
    $chromeCandidates = @(
        (Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe'),
        (Join-Path ${env:ProgramFiles(x86)} 'Google\Chrome\Application\chrome.exe'),
        (Join-Path $env:LOCALAPPDATA 'Google\Chrome\Application\chrome.exe')
    )
    $browser = (@($edgeCandidates) + @($chromeCandidates)) |
        Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) } |
        Select-Object -First 1

    if ($browser) {
        Start-Process -FilePath $browser -ArgumentList $script:AppUrl | Out-Null
    } else {
        Start-Process $script:AppUrl | Out-Null
    }
}

param(
    [string]$Version = '1.0.0',
    [string]$InnoCompiler = '',
    [switch]$SkipPull
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$outputRoot = Join-Path $repositoryRoot 'dist\windows'
$stagingRoot = Join-Path $outputRoot 'staging'
$runtimeRoot = Join-Path $stagingRoot 'runtime'

if (Test-Path -LiteralPath $stagingRoot) {
    Remove-Item -LiteralPath $stagingRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $runtimeRoot -Force | Out-Null

if (-not $InnoCompiler) {
    $compilerCandidates = @(
        (Join-Path $env:ProgramFiles 'Inno Setup 7\ISCC.exe'),
        (Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 7\ISCC.exe')
    )
    $InnoCompiler = $compilerCandidates |
        Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) } |
        Select-Object -First 1
}
if (-not $InnoCompiler -or -not (Test-Path -LiteralPath $InnoCompiler -PathType Leaf)) {
    throw '未找到 Inno Setup 7.1.0 的 ISCC.exe。请安装官方 x64 版本或使用 -InnoCompiler 指定路径。'
}

$env:APP_VERSION = $Version
$env:CVAT_HOST = 'localhost'
$env:CVAT_WORKSPACE_ROOT = $repositoryRoot.Replace('\', '/')
$env:CVAT_STATE_DIR = (Join-Path $env:TEMP 'cvat-offline-build-state').Replace('\', '/')

$composeFiles = @(
    '-f', (Join-Path $repositoryRoot 'docker-compose.yml'),
    '-f', (Join-Path $repositoryRoot 'docker-compose.local.yml')
)
$runtimeServices = @(
    'cvat_db',
    'cvat_redis_inmem',
    'cvat_redis_ondisk',
    'cvat_server',
    'cvat_worker_utils',
    'cvat_worker_import',
    'cvat_worker_export',
    'cvat_worker_annotation',
    'cvat_worker_chunks',
    'cvat_ui',
    'traefik',
    'cvat_opa'
)

if (-not $SkipPull) {
    & docker compose @composeFiles pull --ignore-buildable @runtimeServices
    if ($LASTEXITCODE -ne 0) { throw '基础镜像拉取失败。' }
}
& docker compose @composeFiles build --pull cvat_server cvat_ui
if ($LASTEXITCODE -ne 0) { throw '应用镜像构建失败。' }

$configJson = & docker compose @composeFiles config --format json
if ($LASTEXITCODE -ne 0) { throw 'Docker Compose 配置解析失败。' }
$config = $configJson | ConvertFrom-Json
$images = foreach ($service in $runtimeServices) {
    $serviceConfig = $config.services.PSObject.Properties[$service]
    if (-not $serviceConfig -or -not $serviceConfig.Value.image) {
        throw "服务 $service 没有可导出的镜像。"
    }
    $serviceConfig.Value.image
}
$images = $images | Sort-Object -Unique

foreach ($image in $images) {
    & docker image inspect $image *> $null
    if ($LASTEXITCODE -ne 0) { throw "镜像不存在：$image" }
}
& docker save --output (Join-Path $runtimeRoot 'images.tar') @images
if ($LASTEXITCODE -ne 0) { throw '离线镜像归档生成失败。' }

$images | Set-Content -LiteralPath (Join-Path $runtimeRoot 'image-list.txt') -Encoding UTF8
Copy-Item -LiteralPath (Join-Path $repositoryRoot 'docker-compose.yml') -Destination $runtimeRoot
Copy-Item -LiteralPath (Join-Path $repositoryRoot 'docker-compose.local.yml') -Destination $runtimeRoot
Copy-Item -LiteralPath (Join-Path $repositoryRoot 'LICENSE') -Destination $runtimeRoot
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'THIRD_PARTY.md') -Destination $runtimeRoot

New-Item -ItemType Directory -Path $outputRoot -Force | Out-Null
& $InnoCompiler "/DAppVersion=$Version" "/DStagingDir=$stagingRoot" "/DOutputDir=$outputRoot" (Join-Path $PSScriptRoot 'installer.iss')
if ($LASTEXITCODE -ne 0) { throw '安装程序编译失败。' }

Write-Host "已生成：$(Join-Path $outputRoot '标注软件-Setup.exe')"

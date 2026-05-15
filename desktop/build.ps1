# Build pipeline do app desktop roll3d6.
#
# Uso (PowerShell, do project root, com .venv ativada):
#   .\desktop\build.ps1
#
# Saídas:
#   dist\roll3d6\roll3d6.exe       - bundle PyInstaller (pasta de ~150 MB)
#   dist\roll3d6-setup.exe         - instalador único (se Inno Setup presente)

# Native commands (pyinstaller, iscc) escrevem INFO em stderr; com 'Stop'
# o PS 5.1 trata isso como erro fatal. Mantemos 'Continue' e checamos
# $LASTEXITCODE explicitamente depois de cada chamada.
$ErrorActionPreference = 'Continue'
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Push-Location $ProjectRoot
try {
    Write-Host "==> 1/4  collectstatic" -ForegroundColor Cyan
    & .\.venv\Scripts\python.exe manage.py collectstatic --noinput --clear
    if ($LASTEXITCODE -ne 0) { throw "collectstatic falhou" }

    Write-Host ""
    Write-Host "==> 2/4  pyinstaller (--clean, 1-3 min)" -ForegroundColor Cyan
    & .\.venv\Scripts\pyinstaller.exe desktop\roll3d6.spec --clean --noconfirm
    if ($LASTEXITCODE -ne 0) { throw "pyinstaller falhou" }

    $exe = Join-Path $ProjectRoot 'dist\roll3d6\roll3d6.exe'
    if (-not (Test-Path $exe)) { throw "roll3d6.exe não foi gerado" }
    $bundleSize = (Get-ChildItem 'dist\roll3d6' -Recurse | Measure-Object -Sum Length).Sum / 1MB
    Write-Host "   bundle: dist\roll3d6\ ($('{0:N1} MB' -f $bundleSize))"

    # Procura Inno Setup nas localizações padrão.
    Write-Host ""
    Write-Host "==> 3/4  Inno Setup (instalador único)" -ForegroundColor Cyan
    $isccCandidates = @(
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",   # instalação per-user (winget default)
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles(x86)}\Inno Setup 5\ISCC.exe"
    )
    $iscc = $isccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

    if (-not $iscc) {
        Write-Warning "ISCC.exe não encontrado. Pule esta etapa ou instale Inno Setup:"
        Write-Warning "    winget install -e --id JRSoftware.InnoSetup"
        Write-Host "   (build do bundle terminado em dist\roll3d6\)"
    }
    else {
        & $iscc 'desktop\installer.iss'
        if ($LASTEXITCODE -ne 0) { throw "iscc.exe falhou" }
        $setup = Join-Path $ProjectRoot 'dist\roll3d6-setup.exe'
        if (Test-Path $setup) {
            $setupSize = (Get-Item $setup).Length / 1MB
            Write-Host "   instalador: dist\roll3d6-setup.exe ($('{0:N1} MB' -f $setupSize))"
        }
    }

    Write-Host ""
    Write-Host "==> 4/4  pronto" -ForegroundColor Green
    Write-Host "Distribuir: dist\roll3d6-setup.exe (se gerado) — dois cliques, instala em %LOCALAPPDATA%\Programs\roll3d6"
}
finally {
    Pop-Location
}

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$docguardPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $docguardPython)) {
    throw 'Create .venv and install requirements-app.txt first. See README.md.'
}
& $docguardPython -m streamlit run app.py

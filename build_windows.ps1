Write-Host "Building PhotoConverter for Windows..." -ForegroundColor Cyan

python -m PyInstaller `
    --onefile `
    --windowed `
    --icon="PhotoConverter.ico" `
    --name="PhotoConverter" `
    --clean `
    main.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Build successful!" -ForegroundColor Green
    Write-Host "Executable: dist\PhotoConverter.exe" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Build failed." -ForegroundColor Red
    exit 1
}

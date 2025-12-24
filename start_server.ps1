# Script untuk start web interface server
# Kill semua process yang menggunakan port 5000

Write-Host "Checking port 5000..." -ForegroundColor Yellow

# Kill semua process di port 5000
$processes = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique

if ($processes) {
    Write-Host "Found processes using port 5000: $($processes -join ', ')" -ForegroundColor Red
    foreach ($pid in $processes) {
        try {
            Stop-Process -Id $pid -Force -ErrorAction Stop
            Write-Host "Killed process $pid" -ForegroundColor Green
        } catch {
            Write-Host "Could not kill process $pid: $_" -ForegroundColor Red
        }
    }
    Start-Sleep -Seconds 2
} else {
    Write-Host "Port 5000 is free" -ForegroundColor Green
}

# Verify port is free
$check = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
if ($check) {
    Write-Host "WARNING: Port 5000 is still in use!" -ForegroundColor Red
    Write-Host "Please manually kill processes or use a different port" -ForegroundColor Yellow
    exit 1
}

Write-Host "`nStarting web interface server..." -ForegroundColor Cyan
Write-Host "Server will be available at:" -ForegroundColor Cyan
Write-Host "  - http://localhost:5000" -ForegroundColor White
Write-Host "  - http://127.0.0.1:5000" -ForegroundColor White
Write-Host "  - http://10.22.10.131:5000" -ForegroundColor White
Write-Host "`nPress Ctrl+C to stop the server`n" -ForegroundColor Yellow

# Start server
python -m api.web_interface



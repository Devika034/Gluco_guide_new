# RunGlucoGuide.ps1
# This script automates starting the backend and frontend for GlucoGuide.

Write-Host "Starting GlucoGuide..." -ForegroundColor Cyan

# 1. Kill stale processes
Write-Host "Cleaning up stale processes..." -ForegroundColor Yellow
Stop-Process -Name "python" -ErrorAction SilentlyContinue
Stop-Process -Name "uvicorn" -ErrorAction SilentlyContinue

# 2. Start Backend
Write-Host "Starting Backend Server on Port 8005..." -ForegroundColor Green
$backendPath = Join-Path $PSScriptRoot "lib\backend\Gluco-guide-main"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; py -3.12 main_server.py"

# 3. Wait for backend to initialize
Write-Host "Waiting for backend to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# 4. Start Flutter Web
Write-Host "Launching Flutter Web on Port 8080..." -ForegroundColor Green
flutter run -d chrome --web-port 8080

Write-Host "GlucoGuide is now running!" -ForegroundColor Cyan

# NetReaper Installer for Windows - by 09azo14 | MIT License

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  NetReaper v1.0.0 - Windows Installer" -ForegroundColor Cyan
Write-Host "  Author: 09azo14 | License: MIT" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# Check Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "[ERROR] Python 3 is required but not found." -ForegroundColor Red
    Write-Host "Please install Python 3 from https://www.python.org/downloads/"
    exit 1
}

# Create directories
$dirs = @("reports", "logs", "wordlists", "data")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
}

# Basic wordlists
if (-not (Test-Path "wordlists/router_defaults.txt")) {
    Write-Host "Creating basic wordlist..."
    @("admin", "password", "123456", "root", "test", "admin123", "router") | Set-Content "wordlists/router_defaults.txt"
}

# Install Python dependencies
Write-Host "Installing Python dependencies..."
python -m pip install --quiet -r requirements.txt

# Optional nmap check
$nmap = Get-Command nmap -ErrorAction SilentlyContinue
if (-not $nmap) {
    Write-Host "nmap not found. Install it manually or via: winget install --id nmap" -ForegroundColor Yellow
} else {
    Write-Host "nmap found." -ForegroundColor Green
}

Write-Host ""
Write-Host "NetReaper installed! Run with: python netreaper.py" -ForegroundColor Green

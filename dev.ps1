param (
    [Parameter(Position=0, Mandatory=$false)]
    [string]$Service = "help"
)

function Show-Help {
    Write-Host "Book My Venue - Local Development Helper" -ForegroundColor Cyan
    Write-Host "-----------------------------------------"
    Write-Host "Usage: .\dev.ps1 [command]"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  infra       - Start ONLY Redis (and Gateway if needed) for native Django development."
    Write-Host "  auth        - Start Auth Service in Docker (plus infra)."
    Write-Host "  venue       - Start Venue Service in Docker (plus infra)."
    Write-Host "  booking     - Start Booking Service in Docker (plus infra)."
    Write-Host "  workers     - Start Celery Workers for testing async jobs."
    Write-Host "  down        - Stop all containers."
    Write-Host "  native      - Start Django runserver for Venue Service locally on port 8002."
    Write-Host ""
}

switch ($Service) {
    "infra" {
        Write-Host "Starting Infrastructure (Redis, Gateway)..." -ForegroundColor Green
        docker compose up -d redis gateway
    }
    "auth" {
        Write-Host "Starting Auth Service..." -ForegroundColor Green
        docker compose --profile auth up -d
    }
    "venue" {
        Write-Host "Starting Venue Service..." -ForegroundColor Green
        docker compose --profile venue up -d
    }
    "booking" {
        Write-Host "Starting Booking Service..." -ForegroundColor Green
        docker compose --profile booking up -d
    }
    "workers" {
        Write-Host "Starting Celery Workers..." -ForegroundColor Green
        docker compose --profile workers up -d
    }
    "down" {
        Write-Host "Stopping all services..." -ForegroundColor Yellow
        docker compose --profile auth --profile venue --profile booking --profile workers down
    }
    "native" {
        Write-Host "Starting Venue Service Locally (Native)..." -ForegroundColor Green
        Write-Host "Make sure you have activated your virtual environment!" -ForegroundColor Yellow
        cd "services\venue-service"
        python manage.py runserver 8002
    }
    "help" {
        Show-Help
    }
    default {
        Write-Host "Unknown command: $Service" -ForegroundColor Red
        Show-Help
    }
}

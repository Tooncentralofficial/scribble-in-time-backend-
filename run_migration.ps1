Write-Host "Running Django migration..." -ForegroundColor Green
Write-Host ""

# Wait a moment to ensure any existing Python processes are done
Start-Sleep -Seconds 3

try {
    # Try to run the migration
    python manage.py migrate
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "Migration completed successfully!" -ForegroundColor Green
    } else {
        throw "Migration failed with exit code $LASTEXITCODE"
    }
} catch {
    Write-Host ""
    Write-Host "Migration failed. Trying alternative approach..." -ForegroundColor Yellow
    Write-Host ""
    
    try {
        # Try with python -m
        python -m django manage.py migrate
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "Migration completed successfully with alternative method!" -ForegroundColor Green
        } else {
            throw "Alternative migration also failed"
        }
    } catch {
        Write-Host ""
        Write-Host "Migration still failed. Please try:" -ForegroundColor Red
        Write-Host "1. Close any running Python processes" -ForegroundColor Yellow
        Write-Host "2. Restart your terminal/PowerShell" -ForegroundColor Yellow
        Write-Host "3. Run: python manage.py migrate" -ForegroundColor Yellow
    }
}

Write-Host ""
Read-Host "Press Enter to continue" 
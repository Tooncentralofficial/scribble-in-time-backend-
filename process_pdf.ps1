Write-Host "Processing PDF file..." -ForegroundColor Green
Write-Host ""

# Check if PDF exists
$pdfPath = "knowledge_base\Uche AI Full Training Data Set.pdf"
if (-not (Test-Path $pdfPath)) {
    Write-Host "PDF file not found at: $pdfPath" -ForegroundColor Red
    Read-Host "Press Enter to continue"
    exit 1
}

Write-Host "Found PDF file: $pdfPath" -ForegroundColor Yellow
$fileSize = (Get-Item $pdfPath).Length
Write-Host "File size: $fileSize bytes" -ForegroundColor Yellow

# Try to run the Python script
Write-Host "Running PDF processing script..." -ForegroundColor Yellow
try {
    python simple_process.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "PDF processing completed successfully!" -ForegroundColor Green
        Write-Host "The AI should now be able to answer questions based on the PDF content." -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "PDF processing failed!" -ForegroundColor Red
        Write-Host "Check the error messages above." -ForegroundColor Red
    }
} catch {
    Write-Host "Error running Python script: $_" -ForegroundColor Red
}

Read-Host "Press Enter to continue" 
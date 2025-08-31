@echo off
echo Running Django migration...
echo.

REM Wait a moment to ensure any existing Python processes are done
timeout /t 3 /nobreak > nul

REM Try to run the migration
python manage.py migrate

if %errorlevel% equ 0 (
    echo.
    echo Migration completed successfully!
) else (
    echo.
    echo Migration failed. Trying alternative approach...
    echo.
    
    REM Try with python -m
    python -m django manage.py migrate
    
    if %errorlevel% equ 0 (
        echo.
        echo Migration completed successfully with alternative method!
    ) else (
        echo.
        echo Migration still failed. Please try:
        echo 1. Close any running Python processes
        echo 2. Restart your terminal/command prompt
        echo 3. Run: python manage.py migrate
    )
)

echo.
pause 
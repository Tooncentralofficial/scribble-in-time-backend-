@echo off
echo Processing PDF file...
echo.

REM Check if PDF exists
if not exist "knowledge_base\Uche AI Full Training Data Set.pdf" (
    echo PDF file not found!
    pause
    exit /b 1
)

echo Found PDF file: knowledge_base\Uche AI Full Training Data Set.pdf

REM Try to run the Python script
echo Running PDF processing script...
python simple_process.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo PDF processing completed successfully!
    echo The AI should now be able to answer questions based on the PDF content.
) else (
    echo.
    echo PDF processing failed!
    echo Check the error messages above.
)

pause 
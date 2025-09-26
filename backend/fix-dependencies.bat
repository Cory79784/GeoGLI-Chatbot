@echo off
echo ========================================
echo   GeoGLI Dependency Fix Script
echo ========================================
echo.

echo Checking for dependency issues...

REM Activate virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo No virtual environment found. Creating one...
    python -m venv .venv
    call .venv\Scripts\activate.bat
)

echo.
echo Testing sentence-transformers import...
python -c "import sentence_transformers; print('✅ sentence-transformers works!')" 2>nul && (
    echo Dependencies are working correctly!
    goto :end
)

echo ❌ ImportError detected. Fixing compatibility issue...
echo.

echo Option 1: Installing compatible huggingface_hub version...
pip install huggingface_hub==0.13.4 --force-reinstall

echo.
echo Testing fix...
python -c "import sentence_transformers; print('✅ Fix successful!')" 2>nul && (
    echo Dependencies fixed successfully!
    goto :end
)

echo Option 1 failed. Trying Option 2: Updated versions...
pip install -r requirements-updated.txt --force-reinstall

echo.
echo Testing updated versions...
python -c "import sentence_transformers; print('✅ Updated versions work!')" 2>nul && (
    echo Dependencies updated successfully!
    goto :end
)

echo ❌ Both options failed. Please check the error messages above.
echo You may need to:
echo 1. Update Python to 3.11+
echo 2. Clear pip cache: pip cache purge
echo 3. Reinstall in a fresh virtual environment

:end
echo.
echo ========================================
echo   Dependency check complete
echo ========================================
pause











@echo off
echo Starting UNCCD GeoGLI Chatbot...

echo.
echo === Backend Setup ===
cd backend

echo Creating virtual environment...
python -m venv .venv
call .venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo Checking for dependency compatibility issues...
python -c "import sentence_transformers" 2>nul || (
    echo WARNING: Dependency issue detected. Fixing huggingface_hub compatibility...
    pip install huggingface_hub==0.13.4 --force-reinstall
)

echo Setting up environment...
if not exist .env copy env.example .env

echo Initializing database...
python init_db.py

echo Building vector index with OpenAI embeddings...
python -m app.rag.ingest_openai

echo.
echo === Starting Backend Server ===
start "GeoGLI Backend" cmd /k "call .venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

cd ..

echo.
echo === Starting Frontend ===
start "GeoGLI Frontend" frontend\index.html

echo.
echo Setup complete!
echo Backend: http://localhost:8000
echo Frontend: Open frontend\index.html in your browser
echo.
echo Press any key to exit...
pause >nul

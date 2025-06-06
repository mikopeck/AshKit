@echo off
setlocal

REM --- Configuration ---
set VENV_NAME=ashkit_env
set PYTHON_EXE=python
set REQUIREMENTS_FILE=requirements.txt
set APP_TO_RUN=app.py

REM --- Script Start ---
echo Initializing AshKit LLM Red Teaming Toolkit Environment...

REM Check if Python is available
%PYTHON_EXE% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not found in your PATH.
    echo Please install Python and ensure it's added to your PATH.
    goto :eof
)

REM Check if the virtual environment directory exists
if not exist "%VENV_NAME%\Scripts\activate.bat" (
    echo Creating virtual environment: %VENV_NAME%...
    %PYTHON_EXE% -m venv %VENV_NAME%
    if %errorlevel% neq 0 (
        echo Error: Failed to create virtual environment.
        goto :eof
    )
    echo Virtual environment created.
) else (
    echo Virtual environment %VENV_NAME% already exists.
)

REM Activate the virtual environment
echo Activating virtual environment...
call "%VENV_NAME%\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo Error: Failed to activate virtual environment.
    goto :eof
)

REM Install/update requirements
echo Installing/Updating dependencies from %REQUIREMENTS_FILE%...
pip install -r %REQUIREMENTS_FILE%
if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies.
    goto :eof
)
echo Dependencies are up to date.

REM Run the Streamlit application
echo Starting Streamlit application: %APP_TO_RUN%...
echo If the app doesn't open, check your browser or the console for a URL (usually http://localhost:8501)
streamlit run %APP_TO_RUN%

echo Script finished.
endlocal
pause
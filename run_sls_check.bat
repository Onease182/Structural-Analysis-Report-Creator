@echo off
setlocal
cd /d "%~dp0"
title SLS / ULS drift check - NBC 105:2025

REM ======================================================================
REM  SETTINGS - edit if needed
REM ======================================================================
set "PY=python"
set "ULS_DIR=tables"
set "SLS_DIR=sls_tables"
set "OUT_IMG=report\SLS_Drift_Check.jpg"
set "RMU=4"
REM Leave HEIGHT empty to take H from the ETABS story data (metres if set)
set "HEIGHT="
REM ======================================================================

%PY% --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python or edit PY at the top of this file.
    goto :fail
)

for %%F in (etabs_extract_tables.py etabs_extract_sls_drifts.py generate_sls_drift_report.py) do (
    if not exist "%%F" (
        echo [ERROR] Missing script: %%F
        goto :fail
    )
)

echo.
echo ==========================================================
echo  STEP 1 of 3 : ULS extraction
echo ==========================================================
echo  In ETABS, open the model with ULS stiffness
echo  (beams 0.35, columns 0.70 - Table 3-1), SAVE it,
echo  and make sure EQX-ULS and EQY-ULS exist.
echo.
pause
%PY% etabs_extract_tables.py
if errorlevel 1 (
    echo [ERROR] ULS extraction failed.
    goto :fail
)
if not exist "%ULS_DIR%\31_Joint_Drifts.csv" (
    echo [ERROR] %ULS_DIR%\31_Joint_Drifts.csv was not written. Check the ULS case names.
    goto :fail
)

echo.
echo ==========================================================
echo  STEP 2 of 3 : SLS extraction
echo ==========================================================
echo  Now in ETABS, open the SLS model, SAVE it,
echo  and make sure EQX-SLS and EQY-SLS exist.
echo.
pause
%PY% etabs_extract_sls_drifts.py --out "%SLS_DIR%"
if errorlevel 1 (
    echo [WARN] SLS extraction reported problems. Read the messages above.
    choice /M "Continue to report generation anyway"
    if errorlevel 2 goto :fail
)

echo.
echo ==========================================================
echo  STEP 3 of 3 : Generate the 4 images
echo ==========================================================
if not exist report mkdir report

set "ARGS=--tables "%SLS_DIR%" --uls-tables "%ULS_DIR%" --output "%OUT_IMG%" --uls-scale %RMU%"
if defined HEIGHT set "ARGS=%ARGS% --height %HEIGHT%"
if exist report_context.json set "ARGS=%ARGS% --context report_context.json"

%PY% generate_sls_drift_report.py %ARGS%
if errorlevel 1 (
    echo [ERROR] Report generation failed.
    goto :fail
)

echo.
echo ==========================================================
echo  DONE. Images in the report folder:
echo    SLS_Drift_Check.jpg
echo    Displacement_Drift_Criteria.jpg
echo    Torsional_Irregularity_Check.jpg
echo    Column_Reinforcement_Details.jpg
echo ==========================================================
start "" "report"
pause
exit /b 0

:fail
echo.
echo Process stopped.
pause
exit /b 1
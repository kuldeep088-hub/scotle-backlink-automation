@echo off
REM ============================================================
REM  schedule_daily.bat
REM  Sets up Windows Task Scheduler to run big_poster.py daily
REM  Posts 5 backlinks per day across rotating platforms
REM ============================================================

SET SCRIPT_DIR=%~dp0
SET PYTHON=python
SET POSTER=%SCRIPT_DIR%big_poster.py
SET LOG_DIR=%SCRIPT_DIR%logs
SET LOG_FILE=%LOG_DIR%\daily_poster.log
SET TASK_NAME=Scotle_Daily_Backlinks

IF NOT EXIST "%LOG_DIR%" mkdir "%LOG_DIR%"

echo.
echo  ============================================================
echo   Scotle.org Daily Backlink Scheduler
echo   Posts 5 backlinks per day at 10:00 AM
echo  ============================================================
echo.

REM ── Option 1: Run RIGHT NOW (test) ───────────────────────────
IF "%1"=="run" (
    echo  [RUN] Posting backlinks now ...
    echo  Output: %LOG_FILE%
    echo.
    %PYTHON% "%POSTER%" --count 1 >> "%LOG_FILE%" 2>&1
    echo  Done. Check %LOG_FILE% for results.
    goto END
)

REM ── Option 2: Setup Task Scheduler ──────────────────────────
IF "%1"=="setup" (
    echo  [SETUP] Creating Windows Task Scheduler job ...
    echo.

    REM Delete old task if exists
    schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

    REM Create new daily task at 10:00 AM
    schtasks /create ^
        /tn "%TASK_NAME%" ^
        /tr "\"%PYTHON%\" \"%POSTER%\" --count 1 >> \"%LOG_FILE%\" 2>&1" ^
        /sc daily ^
        /st 10:00 ^
        /f ^
        /rl HIGHEST

    IF %ERRORLEVEL%==0 (
        echo  [OK] Task created successfully!
        echo.
        echo  Task Name : %TASK_NAME%
        echo  Runs      : Daily at 10:00 AM
        echo  Log file  : %LOG_FILE%
        echo.
        echo  To view task: schtasks /query /tn "%TASK_NAME%"
        echo  To remove  : schtasks /delete /tn "%TASK_NAME%" /f
    ) ELSE (
        echo  [ERROR] Task creation failed. Run as Administrator.
    )
    goto END
)

REM ── Option 3: Remove Task ────────────────────────────────────
IF "%1"=="remove" (
    echo  [REMOVE] Deleting scheduled task ...
    schtasks /delete /tn "%TASK_NAME%" /f
    echo  Task removed.
    goto END
)

REM ── Option 4: View logs ───────────────────────────────────────
IF "%1"=="logs" (
    echo  [LOGS] Last 50 lines of %LOG_FILE%:
    echo.
    powershell "Get-Content '%LOG_FILE%' -Tail 50"
    goto END
)

REM ── Option 5: Status ─────────────────────────────────────────
IF "%1"=="status" (
    echo  [STATUS] Scheduled task info:
    schtasks /query /tn "%TASK_NAME%" /fo LIST 2>nul || echo  Task not found. Run: schedule_daily.bat setup
    goto END
)

REM ── Default: Show help ────────────────────────────────────────
echo  USAGE:
echo.
echo    schedule_daily.bat setup    ^<-- Create daily scheduled task (run once)
echo    schedule_daily.bat run      ^<-- Post backlinks right now (test)
echo    schedule_daily.bat status   ^<-- Check if task is scheduled
echo    schedule_daily.bat logs     ^<-- View recent log output
echo    schedule_daily.bat remove   ^<-- Delete the scheduled task
echo.
echo  SCHEDULE: Posts 5 links daily at 10:00 AM
echo  LOG FILE: %LOG_DIR%\daily_poster.log
echo.

:END
pause

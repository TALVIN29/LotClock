@echo off
REM LotClock daily collection - invoked by Windows Task Scheduler.
REM Logs every run so gaps are visible later; the model needs to know which
REM days were actually observed, not just which listings were seen.

cd /d "%~dp0"

if not exist logs mkdir logs

echo. >> logs\scrape.log
echo ================================================== >> logs\scrape.log
echo RUN STARTED %DATE% %TIME% >> logs\scrape.log

".venv\Scripts\python.exe" -m scraper.run >> logs\scrape.log 2>&1
set EXITCODE=%ERRORLEVEL%

echo RUN FINISHED %DATE% %TIME% exit=%EXITCODE% >> logs\scrape.log

exit /b %EXITCODE%

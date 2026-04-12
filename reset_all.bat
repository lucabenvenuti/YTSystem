@echo off
echo ===============================
echo YT SYSTEM FULL RESET STARTED
echo ===============================

echo.
echo [1/6] Stopping scheduled tasks...

schtasks /End /TN "YT Transcript Collector" >nul 2>&1
schtasks /End /TN "YT Summary PDF Generator" >nul 2>&1

echo Tasks stopped (if running).

echo.
echo [2/6] Killing Python processes...

taskkill /F /IM python.exe >nul 2>&1

echo Python processes terminated.

echo.
echo [3/6] Deleting data files...

del /q /f C:\YTSystem\data\transcripts\* >nul 2>&1
del /q /f C:\YTSystem\data\summaries\* >nul 2>&1
del /q /f C:\YTSystem\data\audio_cache\* >nul 2>&1
del /q /f C:\YTSystem\data\pdf\* >nul 2>&1

del /q /f C:\YTSystem\data\reports\collector\* >nul 2>&1
del /q /f C:\YTSystem\data\reports\summary\* >nul 2>&1

del /q /f C:\YTSystem\data\plots\collector\* >nul 2>&1
del /q /f C:\YTSystem\data\plots\summary\* >nul 2>&1

del /q /f C:\YTSystem\data\logs\collector\* >nul 2>&1
del /q /f C:\YTSystem\data\logs\summary\* >nul 2>&1

del /q /f C:\YTSystem\temp\* >nul 2>&1

echo Files deleted.

echo.
echo [4/6] Removing subfolders...

for /d %%d in (C:\YTSystem\data\audio_cache\*) do @rmdir /s /q "%%d"
for /d %%d in (C:\YTSystem\data\transcripts\*) do @rmdir /s /q "%%d"
for /d %%d in (C:\YTSystem\data\summaries\*) do @rmdir /s /q "%%d"
for /d %%d in (C:\YTSystem\data\pdf\*) do @rmdir /s /q "%%d"
for /d %%d in (C:\YTSystem\data\reports\collector\*) do @rmdir /s /q "%%d"
for /d %%d in (C:\YTSystem\data\reports\summary\*) do @rmdir /s /q "%%d"
for /d %%d in (C:\YTSystem\data\plots\collector\*) do @rmdir /s /q "%%d"
for /d %%d in (C:\YTSystem\data\plots\summary\*) do @rmdir /s /q "%%d"
for /d %%d in (C:\YTSystem\data\logs\collector\*) do @rmdir /s /q "%%d"
for /d %%d in (C:\YTSystem\data\logs\summary\*) do @rmdir /s /q "%%d"
for /d %%d in (C:\YTSystem\temp\*) do @rmdir /s /q "%%d"

echo Subfolders removed.

echo.
echo [5/6] Deleting database...

del /q /f C:\YTSystem\db\yt_pipeline.db >nul 2>&1

echo Database removed.

echo.
echo [6/6] Cleaning __pycache__...

for /d /r C:\YTSystem %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"

echo Cache cleaned.

echo.
echo ===============================
echo RESET COMPLETE
echo ===============================
echo.
echo NOTE:
echo - config.yaml and channels.yaml were NOT touched
echo - schema.sql is still present
echo - system will rebuild everything on next run
echo.

pause
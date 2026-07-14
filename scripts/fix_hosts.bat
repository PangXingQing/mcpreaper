@echo off
REM Fix localhost resolution in Windows hosts file
REM Must be run as Administrator

set "hosts=%SystemRoot%\System32\drivers\etc\hosts"
set "temp=%TEMP%\hosts_fixed.tmp"

REM Read hosts file, uncomment localhost line if present, add if missing
set "found="
set "added="

for /f "usebackq delims=" %%i in ("%hosts%") do (
    echo %%i | findstr /r "^#.*127\.0\.0\.1.*localhost$" >nul
    if not errorlevel 1 (
        echo 127.0.0.1 localhost>>"%temp%"
        set found=1
    ) else (
        echo %%i>>"%temp%"
    )
)

REM Check if localhost entry exists at all (commented or not)
findstr /r "^127\.0\.0\.1.*localhost$" "%temp%" >nul
if errorlevel 1 (
    REM No uncommented localhost entry, add it
    echo 127.0.0.1 localhost>>"%temp%"
    set added=1
)

copy /y "%temp%" "%hosts%"
del "%temp%"

if defined found (
    echo Fixed: Uncommented 127.0.0.1 localhost in hosts file
) else if defined added (
    echo Fixed: Added 127.0.0.1 localhost to hosts file
) else (
    echo OK: localhost resolution is already correct
)

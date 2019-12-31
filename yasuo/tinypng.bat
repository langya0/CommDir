@echo off

setlocal EnableDelayedExpansion

set root_dir=%~dp0
set root_dir=%root_dir:~0,-1%
for /r release\web\ %%i in (*-fs8.png) do (
    del /f /a /q "%%i"
)

set /a total=0
set /a progress=0

for /r release\web\ %%i in (*.png) do (
    set /a total+=1
)

for /r release\web\ %%i in (*.png) do (
    set /a progress+=1
    echo Progress !progress!/!total!
    @call %root_dir%\tools\pngquant.exe -f %%i
    @call move /y "%%~dpi%%~ni-fs8.png" "%%i"
)
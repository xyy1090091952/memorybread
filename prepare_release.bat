@echo off
echo Preparing MemoryBread v0.1.6 Windows package...

:: Create temp directory
rmdir /s /q temp_release 2>nul
mkdir temp_release

:: Copy files
copy save_words_server.py temp_release\
copy index.html temp_release\
copy start_app.bat temp_release\
copy README.md temp_release\

:: Copy database and images
xcopy /E /I database temp_release\database\
xcopy /E /I images temp_release\images\

:: Create zip file
powershell -Command "Compress-Archive -Path temp_release\* -DestinationPath releases\memorybread-v0.1.6-windows.zip -Force"

:: Clean up
rmdir /s /q temp_release

echo Package created successfully!
echo Location: releases\memorybread-v0.1.6-windows.zip
pause
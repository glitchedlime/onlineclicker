@echo off
git fetch origin
git reset --hard origin/HEAD
echo.
echo Your server has been updated. Press ENTER to close this window.
pause > nul
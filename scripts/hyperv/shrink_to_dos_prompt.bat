@echo off
REM ==================================================================
REM  MXC Windows 11 DOS-Style Command Prompt Dev Box Shrink Script
REM ==================================================================
echo [*] Transforming Windows 11 into a Pure DOS / CMD Prompt Dev Box...

REM 1. Set Shell to classic CMD.EXE prompt
echo [1/6] Setting Winlogon Shell to CMD.EXE...
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v Shell /t REG_SZ /d "cmd.exe /k color 0A" /f

REM 2. Disable OS Hibernation (Saves 4GB-8GB disk immediately)
echo [2/6] Disabling Hibernation...
powercfg -h off

REM 3. Disable Heavy Background Services (Search Indexer, Windows Update)
echo [3/6] Disabling WSearch and wuauserv...
sc config WSearch start= disabled
net stop WSearch >nul 2>&1
sc config wuauserv start= disabled
net stop wuauserv >nul 2>&1

REM 4. Purge Component Store Backups
echo [4/6] Running DISM Component Cleanup...
dism.exe /Online /Cleanup-Image /StartComponentCleanup /ResetBase /NoRestart

REM 5. Enable CompactOS Transparent Compression
echo [5/6] Enabling CompactOS LZX Compression...
compact.exe /CompactOS:always

REM 6. Enable RDP & Enhanced Session
echo [6/6] Enabling RDP Listener...
reg add "HKLM\System\CurrentControlSet\Control\Terminal Server" /v fDenyTSConnections /t REG_DWORD /d 0 /f

echo.
echo [+] Transformation Complete! Rebooting to DOS Prompt...
shutdown /r /t 3


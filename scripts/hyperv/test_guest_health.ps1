$out = powershell -File C:\workspace\scripts\hyperv\guest_health.ps1 | ConvertFrom-Json
if ($out.Status -eq 'Healthy' -and $out.FreeMemoryMB -gt 0 -and $out.ActiveVmicCount -gt 0) {
    Write-Output "ALL ASSERTIONS PASSED: Guest is healthy (Memory: $($out.FreeMemoryMB)MB free, VMIC Services: $($out.ActiveVmicCount))"
    exit 0
} else {
    Write-Error "ASSERTIONS FAILED!"
    exit 1
}

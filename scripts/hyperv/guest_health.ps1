<#
.SYNOPSIS
    Queries guest diagnostic health metrics in structured JSON format.
#>
function Get-MxcGuestHealth {
    $os = Get-CimInstance Win32_OperatingSystem
    $disk = Get-PSDrive C
    $services = Get-Service vmic* | Where-Object Status -eq 'Running' | Select-Object -ExpandProperty Name
    
    [PSCustomObject]@{
        Status           = 'Healthy'
        OsVersion        = $os.Caption
        FreeMemoryMB     = [Math]::Round($os.FreePhysicalMemory / 1024, 2)
        TotalMemoryMB    = [Math]::Round($os.TotalVisibleMemorySize / 1024, 2)
        FreeDiskGB       = [Math]::Round($disk.Free / 1GB, 2)
        ActiveVmicCount  = $services.Count
    } | ConvertTo-Json -Compress
}

Get-MxcGuestHealth

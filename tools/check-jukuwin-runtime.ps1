param(
    [Parameter(Mandatory=$true)][string]$Executable,
    [Parameter(Mandatory=$true)][string]$Media,
    [Parameter(Mandatory=$true)][string]$OutputDirectory
)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$root = (Resolve-Path $OutputDirectory).Path
Copy-Item $Executable "$root/JUKUWIN.EXE"
Copy-Item $Media "$root/CPM3.IMG"
$exe = "$root/JUKUWIN.EXE"
$log = "$root/JUKUWIN.LOG"
if (Test-Path $log) { throw 'Runtime check needs a fresh output directory' }

function Wait-Log([string]$Pattern, [int]$Count = 1) {
    $deadline = [DateTime]::UtcNow.AddSeconds(30)
    do {
        if (Test-Path $log) {
            $text = Get-Content $log -Raw
            if ([regex]::Matches($text, $Pattern).Count -ge $Count) { return }
        }
        Start-Sleep -Milliseconds 100
    } while ([DateTime]::UtcNow -lt $deadline)
    throw "Missing log record ($Count occurrences): $Pattern"
}
function Stop-Gui($Process) {
    if (!$Process.CloseMainWindow()) { throw 'Cannot close Juku Host window' }
    if (!$Process.WaitForExit(10000)) { throw 'Juku Host did not exit cleanly' }
    if ($Process.ExitCode -ne 0) { throw "GUI exited $($Process.ExitCode)" }
}
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class JukuWinSmoke {
    [DllImport("user32.dll")]
    public static extern IntPtr GetDlgItem(IntPtr window, int id);
    [DllImport("user32.dll", CharSet = CharSet.Ansi)]
    public static extern int GetWindowText(IntPtr window, System.Text.StringBuilder text, int capacity);
    [DllImport("user32.dll")]
    public static extern bool PostMessage(IntPtr window, uint message, IntPtr wparam, IntPtr lparam);
}
'@

$process = $null
try {
    $process = Start-Process -FilePath $exe -ArgumentList '--selftest' -PassThru
    if (!$process.WaitForExit(60000)) { throw 'Threaded selftest timed out' }
    if ($process.ExitCode -ne 0) { throw "Threaded selftest exited $($process.ExitCode)" }
    Wait-Log 'Selftest worker started' 2
    Wait-Log 'Threaded selftest passed'
    Wait-Log 'Juku Host exiting'

    # Exercise the actual Listen path, including failure before session evidence
    # opens. Repeat Listen in the same GUI to catch thread cleanup/restart faults.
    $config = @'
[juku]
mode=stock
serial=COM256
serial_id=
auto_listen=yes
[drive_a]
image=MISSING.IMG
mode=snapshot
working=
[drive_b]
image=
[evidence]
directory=logs
capture=yes
verbose=no
keep_sessions=0
'@
    Set-Content "$root/JUKUWIN.INI" $config -Encoding ascii
    $process = Start-Process -FilePath $exe -PassThru
    Wait-Log 'Host worker stopped: result' 1
    $deadline = [DateTime]::UtcNow.AddSeconds(10)
    do {
        $process.Refresh()
        $button = [JukuWinSmoke]::GetDlgItem($process.MainWindowHandle, 110)
        $label = New-Object System.Text.StringBuilder 32
        [void][JukuWinSmoke]::GetWindowText($button, $label, 32)
        if ($label.ToString() -eq 'Listen') { break }
        Start-Sleep -Milliseconds 100
    } while ([DateTime]::UtcNow -lt $deadline)
    if ($label.ToString() -ne 'Listen') { throw 'GUI did not finish worker cleanup' }
    if (![JukuWinSmoke]::PostMessage($process.MainWindowHandle, 0x111, [IntPtr]110, [IntPtr]::Zero)) {
        throw 'Cannot press Listen'
    }
    Wait-Log 'Host worker stopped: result' 2
    Wait-Log 'Host worker started' 2
    Wait-Log 'Drive A must be a readable 409600-byte image' 2
    if (Test-Path "$root/logs") { throw 'Missing-media case unexpectedly created session evidence' }
    Stop-Gui $process

    # Reach the runner and its session log; COM256 is deliberately unavailable.
    Set-Content "$root/JUKUWIN.INI" ($config.Replace('MISSING.IMG', 'CPM3.IMG')) -Encoding ascii
    $process = Start-Process -FilePath $exe -PassThru
    Wait-Log 'Host worker stopped: result' 3
    $sessions = @(Get-ChildItem "$root/logs" -Recurse -Filter JUKUHOST.LOG)
    if ($sessions.Count -ne 1 -or $sessions[0].Length -eq 0) {
        throw 'Serial-open failure did not leave a session log'
    }
    Stop-Gui $process
    $text = Get-Content $log -Raw
    if ($text.Contains('Cannot start host worker')) { throw 'Listen failed to create a worker' }
    Write-Output 'JUKUWIN-WINDOWS-RUNTIME: PASS (threaded selftest, repeated GUI Listen, early failure log, session log)'
} finally {
    if ($null -ne $process -and !$process.HasExited) {
        $process.Kill()
        $process.WaitForExit()
    }
}

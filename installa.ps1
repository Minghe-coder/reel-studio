# Installer di Reel Studio (doppio clic su INSTALLA.cmd). Si puo' rilanciare quante volte vuoi.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$Root = $PSScriptRoot

function Step($t) { Write-Host ""; Write-Host "==> $t" -ForegroundColor Cyan }
function Has($cmd) { return [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }
function RefreshPath {
  $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
}

Step "Controllo i programmi necessari"
$apps = @(
  @{ cmd = "git";    id = "Git.Git" },
  @{ cmd = "python"; id = "Python.Python.3.12" },
  @{ cmd = "ffmpeg"; id = "Gyan.FFmpeg" }
)
foreach ($a in $apps) {
  if (Has $a.cmd) { Write-Host "  OK  $($a.cmd)" }
  else {
    Write-Host "  installo $($a.id)..."
    winget install --id $a.id -e --accept-source-agreements --accept-package-agreements
    RefreshPath
  }
}
if (-not (Has "claude")) {
  Write-Host "  installo Claude Code..."
  Invoke-RestMethod https://claude.ai/install.ps1 | Invoke-Expression
  RefreshPath
} else { Write-Host "  OK  claude" }

Step "Preparo l'ambiente Python (qualche minuto la prima volta)"
if (-not (Test-Path "$Root\.venv\Scripts\python.exe")) { python -m venv "$Root\.venv" }
& "$Root\.venv\Scripts\python.exe" -m pip install --upgrade pip -q
& "$Root\.venv\Scripts\python.exe" -m pip install -r "$Root\requirements.txt" -q

Step "Creo la cartella Reel Studio sul Desktop"
$Desktop = [Environment]::GetFolderPath("Desktop")
$Studio = Join-Path $Desktop "Reel Studio"
$Inbox = Join-Path $Studio "1 - Video da montare"
$Outbox = Join-Path $Studio "2 - Video pronti"
New-Item -ItemType Directory -Force -Path $Inbox, $Outbox | Out-Null
Copy-Item "$Root\GUIDA-FACILE.html" (Join-Path $Studio "Guida - cosa posso dire.html") -Force
$yaml = "# Creato da installa.ps1: cartelle di questo PC`r`nstudio_dir: '$Studio'`r`ninbox: '$Inbox'`r`noutbox: '$Outbox'`r`n"
[IO.File]::WriteAllText("$Root\config\local.yaml", $yaml, (New-Object Text.UTF8Encoding $false))

Step "Creo l'icona 'Reel Studio' sul Desktop"
$sh = New-Object -ComObject WScript.Shell
foreach ($lnkPath in @((Join-Path $Desktop "Reel Studio.lnk"), (Join-Path $Studio "Avvia Reel Studio.lnk"))) {
  $lnk = $sh.CreateShortcut($lnkPath)
  $lnk.TargetPath = "$Root\avvia.cmd"
  $lnk.WorkingDirectory = $Root
  $lnk.IconLocation = "$Root\assets\icon.ico"
  $lnk.Description = "Monta i tuoi reel con Claude"
  $lnk.Save()
}

Step "Effetti sonori di base e controllo finale"
& "$Root\.venv\Scripts\python.exe" -m reel sfx-base
& "$Root\.venv\Scripts\python.exe" -m reel doctor

Write-Host ""
Write-Host "FATTO! Sul Desktop trovi l'icona 'Reel Studio' e la cartella 'Reel Studio'." -ForegroundColor Green
Write-Host "La prima volta che avvii Claude ti chiedera' di accedere con il tuo account."

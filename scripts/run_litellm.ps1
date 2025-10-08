Param(
  [string]$Config = "litellm_config.yaml",
  [int]$Port = 4000
)

$RunDir = ".run"
$PidFile = Join-Path $RunDir "litellm.pid"

# Ensure dev requirements are installed (includes litellm[proxy])
if (Test-Path "requirements-dev.txt") {
  try { pip install -r requirements-dev.txt | Out-Null } catch { Write-Warning $_ }
}

New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

if (Test-Path $PidFile) {
  try {
    $pid = Get-Content $PidFile | Select-Object -First 1
    if ($pid -and (Get-Process -Id $pid -ErrorAction SilentlyContinue)) {
      Write-Host "LiteLLM already running (PID $pid)"
      exit 0
    }
  } catch {}
  Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

$resolved = Resolve-Path $Config -ErrorAction SilentlyContinue
if (-not $resolved) { throw "Config file not found: $Config" }
$env:LITELLM_CONFIG = $resolved.Path

# Prefer workspace venv python if present
$venvPy = Join-Path ".venv" "Scripts/python.exe"
if (Test-Path $venvPy) { $python = $venvPy } else { $python = "python" }

$argsList = @("-m","litellm","--host","127.0.0.1","--port=$Port","--config","$env:LITELLM_CONFIG")
$p = Start-Process -NoNewWindow -PassThru -FilePath $python -ArgumentList $argsList
$p.Id | Set-Content $PidFile
Write-Host "LiteLLM proxy started on http://127.0.0.1:$Port using $Config (pid $($p.Id))"

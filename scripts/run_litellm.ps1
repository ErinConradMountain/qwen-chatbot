Param(
  [string]$Config = "litellm_config.yaml",
  [int]$Port = 4000
)
$RunDir = ".run"
$PidFile = Join-Path $RunDir "litellm.pid"

function Ensure-Package {
  param([string]$pkg)
  python - <<PY
import importlib, sys
sys.exit(0 if importlib.util.find_spec('$pkg') else 1)
PY
  if ($LASTEXITCODE -ne 0) {
    pip install $pkg
  }
}

try {
  pip install -r requirements-dev.txt | Out-Null
} catch {
  Ensure-Package -pkg "litellm[proxy]"
}

New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

if (Test-Path $PidFile) {
  $pid = Get-Content $PidFile
  if (Get-Process -Id $pid -ErrorAction SilentlyContinue) {
    Write-Host "LiteLLM already running (PID $pid)"
    exit 0
  } else {
    Remove-Item $PidFile -Force
  }
}

$env:LITELLM_CONFIG = (Resolve-Path $Config)
$p = Start-Process -NoNewWindow -PassThru -FilePath "python" -ArgumentList "-m","litellm","--host","127.0.0.1","--port=$Port","--config","`"$env:LITELLM_CONFIG`""
$p.Id | Set-Content $PidFile
Write-Host "LiteLLM proxy started on http://127.0.0.1:$Port using $Config (pid $($p.Id))"

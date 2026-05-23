param(
  [string]$PluginRoot = (Split-Path -Parent (Split-Path -Parent $PSCommandPath))
)

$ErrorActionPreference = "Stop"

$VenvDir = Join-Path $PluginRoot ".venv"
$Requirements = Join-Path $PluginRoot "requirements.txt"

function Get-VenvPython {
  $candidates = @(
    (Join-Path $VenvDir "Scripts\python.exe"),
    (Join-Path $VenvDir "bin\python.exe"),
    (Join-Path $VenvDir "bin\python")
  )

  foreach ($candidate in $candidates) {
    if (Test-Path $candidate) {
      return $candidate
    }
  }

  return $null
}

function Get-BasePython {
  $candidates = @(
    "C:\Python313\python.exe",
    "py -3",
    "python"
  )

  foreach ($candidate in $candidates) {
    try {
      if ($candidate -eq "py -3") {
        & py -3 --version *> $null
        if ($LASTEXITCODE -eq 0) {
          return @("py", "-3")
        }
      } else {
        & $candidate --version *> $null
        if ($LASTEXITCODE -eq 0) {
          return @($candidate)
        }
      }
    } catch {
      continue
    }
  }

  throw "Unable to find Python 3. Install Python 3.10+ and rerun the installer."
}

$VenvPython = Get-VenvPython
if (!$VenvPython -or !(Test-Path $VenvPython)) {
  $python = Get-BasePython
  & $python -m venv $VenvDir
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to create virtual environment at $VenvDir"
  }
  $VenvPython = Get-VenvPython
  if (!$VenvPython -or !(Test-Path $VenvPython)) {
    throw "Virtual environment created without a Python executable at $VenvDir"
  }
}

if (Test-Path $Requirements) {
  & $VenvPython -m pip install --disable-pip-version-check -r $Requirements
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to install Python requirements into $VenvDir"
  }
}

Write-Output $VenvPython

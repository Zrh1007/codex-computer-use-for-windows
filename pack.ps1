$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSCommandPath
$ZipPath = Join-Path $RepoRoot "windows-computer-use-github.zip"
$StageDir = Join-Path $RepoRoot ".pack-tmp"

if (Test-Path $StageDir) {
  Remove-Item -LiteralPath $StageDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $StageDir | Out-Null

Get-ChildItem -LiteralPath $RepoRoot -Force | Where-Object {
  $_.Name -notin @(".git", ".github", ".pack-tmp", ".test-home", "windows-computer-use-github.zip")
} | ForEach-Object {
  $destination = Join-Path $StageDir $_.Name
  if ($_.PSIsContainer) {
    Copy-Item -LiteralPath $_.FullName -Destination $destination -Recurse -Force
  } else {
    Copy-Item -LiteralPath $_.FullName -Destination $destination -Force
  }
}

Get-ChildItem -LiteralPath $StageDir -Recurse -Force | Where-Object {
  $_.Name -eq "__pycache__" -or $_.Extension -eq ".pyc"
} | Remove-Item -Recurse -Force

if (Test-Path $ZipPath) {
  Remove-Item -LiteralPath $ZipPath -Force
}

Compress-Archive -Path (Join-Path $StageDir "*") -DestinationPath $ZipPath -CompressionLevel Optimal
Remove-Item -LiteralPath $StageDir -Recurse -Force

Write-Host "Created $ZipPath"

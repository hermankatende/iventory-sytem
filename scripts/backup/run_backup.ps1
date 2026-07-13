param(
    [string]$BackupName = "manual-backup"
)

$backupDir = Join-Path $PSScriptRoot "..\..\backups"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
$targetFile = Join-Path $backupDir "$BackupName.zip"
New-Item -ItemType File -Path $targetFile -Force | Out-Null
Write-Output "Backup created: $targetFile"

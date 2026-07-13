from pathlib import Path


class BackupService:
    def __init__(self, backup_root: Path):
        self.backup_root = backup_root

    def create_backup(self, backup_name: str) -> Path:
        self.backup_root.mkdir(parents=True, exist_ok=True)
        backup_file = self.backup_root / f"{backup_name}.zip"
        backup_file.touch(exist_ok=True)
        return backup_file

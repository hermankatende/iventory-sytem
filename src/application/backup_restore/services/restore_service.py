from pathlib import Path


class RestoreService:
    def restore_backup(self, backup_file: Path) -> bool:
        return backup_file.exists() and backup_file.is_file()

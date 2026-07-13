#!/usr/bin/env python
import os
import sys


def _normalize_settings_module(argv: list[str]) -> None:
    legacy_map = {
        "config.settings.offline": "offline",
        "config.settings.online": "online",
        "config.settings.test": "test",
        "config.settings.base": "offline",
    }

    for idx, arg in enumerate(argv):
        if arg.startswith("--settings="):
            value = arg.split("=", 1)[1]
            if value in legacy_map:
                os.environ["DJANGO_ENV"] = legacy_map[value]
                argv[idx] = "--settings=config.settings"
                if legacy_map[value] == "online":
                    os.environ.setdefault("USE_SQLITE", "0")
                else:
                    os.environ.setdefault("USE_SQLITE", "1")
        elif arg == "--settings" and idx + 1 < len(argv):
            value = argv[idx + 1]
            if value in legacy_map:
                os.environ["DJANGO_ENV"] = legacy_map[value]
                argv[idx + 1] = "config.settings"
                if legacy_map[value] == "online":
                    os.environ.setdefault("USE_SQLITE", "0")
                else:
                    os.environ.setdefault("USE_SQLITE", "1")

    current = os.getenv("DJANGO_SETTINGS_MODULE", "").strip()

    if current in legacy_map:
        os.environ["DJANGO_ENV"] = legacy_map[current]
        os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
        if legacy_map[current] == "online":
            os.environ.setdefault("USE_SQLITE", "0")
        else:
            os.environ.setdefault("USE_SQLITE", "1")
        return

    if not current:
        os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"


def main() -> None:
    _normalize_settings_module(sys.argv)
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Django is not installed or unavailable in this environment.") from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

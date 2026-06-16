from __future__ import annotations


def backup_status_record(
    target: str,
    schedule: str,
    last_backup_at: str,
    last_verified_at: str,
    status: str,
) -> dict[str, str]:
    return {
        "target": target,
        "schedule": schedule,
        "last_backup_at": last_backup_at,
        "last_verified_at": last_verified_at,
        "status": status,
        "recovery_note": "Use the latest verified Venus backup before restoring.",
    }

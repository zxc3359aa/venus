from venus.approvals import create_approval_record, requires_manual_approval
from venus.backups import backup_status_record


def test_approval_policy_requires_manual_review_for_public_reply():
    assert requires_manual_approval(3) is True
    assert requires_manual_approval(1) is False


def test_create_approval_record_defaults_to_pending():
    record = create_approval_record(
        action_type="douyin_comment_reply",
        approval_level=3,
        draft="姐妹们，先看屏障状态。",
        evidence_ids=["comment-c1"],
        reviewer="user",
        created_at="2026-06-14T12:00:00+08:00",
    )

    assert record["status"] == "pending"
    assert record["approval_level"] == 3


def test_backup_status_record_tracks_verification():
    record = backup_status_record(
        target="./backups/venus",
        schedule="daily",
        last_backup_at="2026-06-14T03:00:00+08:00",
        last_verified_at="2026-06-14T03:05:00+08:00",
        status="verified",
    )

    assert record["target"] == "./backups/venus"
    assert record["status"] == "verified"
    assert record["recovery_note"] == "Use the latest verified Venus backup before restoring."

import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, Any

ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "personal" / "visual_profile.json"

SYNC_ENABLED = os.getenv("PROFILE_GITHUB_SYNC", "true").lower() in {"1","true","yes","on"}
SYNC_INTERVAL_SECONDS = int(os.getenv("PROFILE_GITHUB_SYNC_INTERVAL", "300"))

_lock = threading.Lock()
_last_sync = 0.0
_last_status: Dict[str, Any] = {
    "enabled": SYNC_ENABLED,
    "ok": None,
    "message": "尚未同步",
    "last_sync_epoch": None,
}


def _run_git(args):
    return subprocess.run(
        ["git", *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=45,
    )


def _working_tree_has_profile_change():
    r = _run_git(["status", "--porcelain", "--", "personal/visual_profile.json"])
    return r.returncode == 0 and bool(r.stdout.strip())


def get_sync_status():
    return dict(_last_status)


def sync_profile_to_github(force: bool = False):
    global _last_sync, _last_status

    if not SYNC_ENABLED:
        _last_status = {
            "enabled": False,
            "ok": None,
            "message": "GitHub 自动同步已关闭",
            "last_sync_epoch": _last_sync or None,
        }
        return _last_status

    now = time.time()
    if not force and now - _last_sync < SYNC_INTERVAL_SECONDS:
        return _last_status

    if not PROFILE_PATH.exists():
        _last_status = {
            "enabled": True,
            "ok": False,
            "message": "本地视觉档案尚不存在",
            "last_sync_epoch": _last_sync or None,
        }
        return _last_status

    if not _lock.acquire(blocking=False):
        return _last_status

    try:
        if not _working_tree_has_profile_change():
            _last_sync = now
            _last_status = {
                "enabled": True,
                "ok": True,
                "message": "档案无变化，无需同步",
                "last_sync_epoch": now,
            }
            return _last_status

        add = _run_git(["add", "personal/visual_profile.json"])
        if add.returncode != 0:
            raise RuntimeError(add.stderr.strip() or "git add failed")

        commit = _run_git([
            "commit",
            "-m",
            "data: sync personal visual profile",
        ])
        if commit.returncode != 0 and "nothing to commit" not in (commit.stdout + commit.stderr).lower():
            raise RuntimeError(commit.stderr.strip() or commit.stdout.strip() or "git commit failed")

        push = _run_git(["push", "origin", "HEAD:main"])
        if push.returncode != 0:
            raise RuntimeError(push.stderr.strip() or "git push failed")

        _last_sync = now
        _last_status = {
            "enabled": True,
            "ok": True,
            "message": "个人档案已同步到 GitHub",
            "last_sync_epoch": now,
        }
        return _last_status
    except Exception as exc:
        _last_status = {
            "enabled": True,
            "ok": False,
            "message": f"GitHub 同步失败：{exc}",
            "last_sync_epoch": _last_sync or None,
        }
        return _last_status
    finally:
        _lock.release()


def sync_profile_async(force: bool = False):
    thread = threading.Thread(
        target=sync_profile_to_github,
        kwargs={"force": force},
        daemon=True,
    )
    thread.start()
    return get_sync_status()

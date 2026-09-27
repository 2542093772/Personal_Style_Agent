import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "orchestrator" / "agent_registry.json"
RUN_LOG = ROOT / "reports" / "orchestrator_runs.json"


def _load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_registry() -> Dict[str, Any]:
    return _load_json(REGISTRY_PATH, {"agents": {}})


def _github_token() -> str:
    return (
        os.getenv("GITHUB_ORCHESTRATOR_TOKEN", "").strip()
        or os.getenv("GITHUB_LOCATION_TOKEN", "").strip()
    )


def dispatch(agent: str, task: str, source: str = "orchestrator") -> Dict[str, Any]:
    registry = get_registry()
    agent_cfg = (registry.get("agents") or {}).get(agent)
    if not agent_cfg:
        raise ValueError(f"unknown agent: {agent}")

    task_cfg = (agent_cfg.get("tasks") or {}).get(task)
    if not task_cfg:
        raise ValueError(f"unknown task: {agent}.{task}")

    if agent_cfg.get("executor") != "github_actions":
        raise ValueError(f"unsupported executor: {agent_cfg.get('executor')}")

    token = _github_token()
    if not token:
        raise RuntimeError("GITHUB_ORCHESTRATOR_TOKEN is not configured")

    repo = os.getenv(
        "ORCHESTRATOR_GITHUB_REPO",
        "2542093772/Personal_Style_Agent",
    ).strip()
    workflow = agent_cfg["workflow"]
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow}/dispatches"
    payload = {
        "ref": "main",
        "inputs": {"job": task_cfg["workflow_input"]},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "Personal-Life-Orchestrator",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST",
    )

    started_at = datetime.now(timezone.utc).isoformat()
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            status = resp.status
        result = {
            "ok": status in (200, 201, 204),
            "agent": agent,
            "task": task,
            "source": source,
            "workflow": workflow,
            "workflow_input": task_cfg["workflow_input"],
            "dispatched_at_utc": started_at,
            "http_status": status,
        }
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        result = {
            "ok": False,
            "agent": agent,
            "task": task,
            "source": source,
            "dispatched_at_utc": started_at,
            "http_status": exc.code,
            "error": body[:800],
        }
    except Exception as exc:
        result = {
            "ok": False,
            "agent": agent,
            "task": task,
            "source": source,
            "dispatched_at_utc": started_at,
            "error": repr(exc),
        }

    history = _load_json(RUN_LOG, [])
    history.append(result)
    _save_json(RUN_LOG, history[-200:])
    return result

#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timedelta
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from build_demand_intelligence_payload import build_payload, read_jsonl
from build_study_entity_store import build_and_write_store
from hot_thread_policy import rank_hot_threads, summarize_hot_threads


STUDY_ID = "fishgoo-us-dropshipping"
DEFAULT_TEMPLATE = {
    "business_lines": [
        "Dropshipping 供应链服务",
        "Shopify 品牌履约优化",
        "中国采购与风险控制",
    ],
    "regions": ["美国", "欧洲", "全球"],
    "primary_goals": [
        "选客群 + 定产品包装",
        "监控行业趋势",
        "寻找高价值销售线索",
    ],
    "sources": ["Reddit"],
    "recommended_outputs": [
        "Dashboard 每日看板",
        "Weekly Brief 周会简报",
        "Segment Explorer 客群深挖",
        "Packaging Studio 产品包装建议",
    ],
}

SERVER_ROOT = Path(__file__).resolve().parent.parent
STUDIES_DIR = SERVER_ROOT / "data" / "studies"
STUDY_CONFIG_DIR = SERVER_ROOT / "config" / "studies"
STUDY_PRODUCT_DATA_DIR = SERVER_ROOT / "docs" / "product" / "data" / "studies"
STUDY_RAW_DIR = SERVER_ROOT / "data" / "raw" / "studies"
STUDY_REPORT_DIR = SERVER_ROOT / "docs" / "reports" / "studies"
STUDY_ENTITY_DIR = SERVER_ROOT / "data" / "entities" / "studies"
JOBS_DIR = SERVER_ROOT / "data" / "jobs"
RUNTIME_STATE_DIR = SERVER_ROOT / "data" / "runtime" / "state"
WORKER_STATE_DIR = RUNTIME_STATE_DIR / "workers"
USERS_FILE = SERVER_ROOT / "config" / "users.json"
WORKERS_FILE = SERVER_ROOT / "config" / "workers.json"
DEFAULT_INPUT = Path("/Users/perrilee/raddit/data/raw/fishgoo_dropshipping_expanded.jsonl")
ROLE_ORDER = {"viewer": 1, "analyst": 2, "admin": 3}
BROWSER_JOB_MODES = {"browser", "hot_threads"}
ALL_JOB_MODES = {"seeded", "browser", "hot_threads", "adaptive"}
REMOTE_STAGE_KINDS = {"discover", "harvest", "refresh_hot"}
LOCAL_STAGE_KINDS = {"rebuild_aggregates", "publish_brief"}
QUEUE_LANE_ORDER = {"realtime": 0, "discovery": 1, "maintenance": 2}
PIPELINE_STAGE_SEQUENCE = {
    "seeded": ["rebuild_aggregates", "publish_brief"],
    "browser": ["discover", "harvest", "rebuild_aggregates", "publish_brief"],
    "hot_threads": ["refresh_hot", "rebuild_aggregates", "publish_brief"],
}
STAGE_QUEUE_LANE = {
    "discover": "discovery",
    "harvest": "realtime",
    "refresh_hot": "realtime",
    "rebuild_aggregates": "maintenance",
    "publish_brief": "maintenance",
}
STAGE_PRIORITY_OFFSET = {
    "discover": 3,
    "harvest": 10,
    "refresh_hot": 12,
    "rebuild_aggregates": -4,
    "publish_brief": -8,
}
STAGE_LABELS = {
    "discover": "discover",
    "harvest": "harvest",
    "refresh_hot": "refresh_hot",
    "rebuild_aggregates": "rebuild_aggregates",
    "publish_brief": "publish_brief",
}
JOB_DISPLAY_COMPLETED_WINDOW_HOURS = 24
ACTIVE_JOB_STATUSES = {"queued", "running", "canceling"}
WORKER_HEARTBEAT_STALE_SECONDS = 90
RUNTIME_ALERT_FAILURE_WINDOW_HOURS = 12
RUNTIME_ALERT_MAX_FAILURES = 3
LEGACY_SERVER_ROOTS = [
    Path("/Users/perrilee/Desktop/探索/raddit"),
    Path.home() / "raddit-service",
]
SOURCE_PATH_KEYS = ("input_path", "browser_config_path")
ARTIFACT_PATH_KEYS = (
    "config_path",
    "payload_json_path",
    "payload_js_path",
    "raw_output_path",
    "discovery_output_path",
    "report_output_path",
    "entity_root_path",
    "manifest_path",
    "threads_path",
    "thread_snapshots_path",
    "comments_path",
    "comment_snapshots_path",
    "signals_path",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Serve the Demand Intelligence MVP with a minimal JSON API."
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT),
        help="Path to the Reddit JSONL dataset.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port to bind.",
    )
    parser.add_argument(
        "--study-title",
        default="美国 dropshipping / 履约与 supplier 问题",
        help="Study title for the dashboard.",
    )
    parser.add_argument(
        "--market",
        default="美国 dropshipping",
        help="Market label shown in the app.",
    )
    parser.add_argument(
        "--date-range",
        default="最新 564 条定向采样",
        help="Study date range label.",
    )
    parser.add_argument(
        "--cors-origins",
        default=os.environ.get("DEMAND_INTEL_CORS_ORIGINS", ""),
        help="Comma-separated allowed CORS origins for the public API.",
    )
    parser.add_argument(
        "--cookie-secure",
        action="store_true",
        default=os.environ.get("DEMAND_INTEL_COOKIE_SECURE", "").lower() in {"1", "true", "yes"},
        help="Mark auth cookies as Secure; recommended when serving behind HTTPS.",
    )
    return parser.parse_args()


def build_dataset(input_path: Path, study_title: str, market: str, date_range: str) -> dict:
    records = read_jsonl(input_path)
    return build_payload(records, study_title, market, date_range)


def build_dataset_from_records(
    records: list[dict[str, Any]],
    study_title: str,
    market: str,
    date_range: str,
    entity_bundle: dict[str, Any] | None = None,
) -> dict:
    return build_payload(records, study_title, market, date_range, entity_bundle=entity_bundle)


def slugify(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value or "study"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def read_users() -> list[dict[str, Any]]:
    if not USERS_FILE.exists():
        return []
    payload = json.loads(USERS_FILE.read_text(encoding="utf-8"))
    return payload.get("users", [])


def read_workers() -> list[dict[str, Any]]:
    if not WORKERS_FILE.exists():
        return []
    payload = json.loads(WORKERS_FILE.read_text(encoding="utf-8"))
    return payload.get("workers", [])


def find_user_by_token(token: str | None) -> dict[str, Any] | None:
    if not token:
        return None
    for user in read_users():
        if user.get("token") == token:
            return user
    return None


def find_user_by_credentials(email: str, password: str) -> dict[str, Any] | None:
    for user in read_users():
        if user.get("email") == email and user.get("password") == password:
            return user
    return None


def find_worker_by_token(token: str | None) -> dict[str, Any] | None:
    if not token:
        return None
    for worker in read_workers():
        if worker.get("enabled", True) and worker.get("token") == token:
            return worker
    return None


def worker_capabilities(worker: dict[str, Any] | None) -> set[str]:
    if not worker:
        return set()
    capabilities = worker.get("capabilities") or list(REMOTE_STAGE_KINDS)
    return {str(item) for item in capabilities if str(item)}


def worker_state_file(worker_id: str) -> Path:
    return WORKER_STATE_DIR / f"{worker_id}.json"


def load_worker_runtime_state(worker_id: str) -> dict[str, Any]:
    return load_json_file(worker_state_file(worker_id), {})


def save_worker_runtime_state(worker_id: str, payload: dict[str, Any]) -> None:
    ensure_support_dirs()
    worker_state_file(worker_id).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def record_worker_heartbeat(worker: dict[str, Any], event: str = "heartbeat") -> dict[str, Any]:
    worker_id = str(worker.get("id", "")).strip()
    if not worker_id:
        return {}
    state = load_worker_runtime_state(worker_id)
    state.update(
        {
            "worker_id": worker_id,
            "worker_name": worker.get("name", worker_id),
            "capabilities": sorted(worker_capabilities(worker)),
            "enabled": bool(worker.get("enabled", True)),
            "last_seen_at": now_iso(),
            "last_event": event,
        }
    )
    save_worker_runtime_state(worker_id, state)
    return state


def worker_summary(worker: dict[str, Any]) -> dict[str, Any]:
    worker_id = str(worker.get("id", "")).strip()
    capabilities = sorted(worker_capabilities(worker))
    state = load_worker_runtime_state(worker_id) if worker_id else {}
    last_seen_at = state.get("last_seen_at")
    last_seen = parse_iso(last_seen_at)
    seconds_since_last_seen = None
    status = "offline"
    if last_seen:
        seconds_since_last_seen = max(int((datetime.now() - last_seen).total_seconds()), 0)
        status = "connected" if seconds_since_last_seen <= WORKER_HEARTBEAT_STALE_SECONDS else "stale"
    running_job = running_remote_job_for_worker(worker_id) if worker_id else None
    return {
        "id": worker_id,
        "name": worker.get("name", worker_id),
        "enabled": bool(worker.get("enabled", True)),
        "capabilities": capabilities,
        "last_seen_at": last_seen_at,
        "seconds_since_last_seen": seconds_since_last_seen,
        "status": status,
        "last_event": state.get("last_event"),
        "running_job_id": (running_job or {}).get("id"),
        "running_stage_kind": (running_job or {}).get("stage_kind"),
    }


def list_worker_summaries() -> list[dict[str, Any]]:
    return [worker_summary(worker) for worker in read_workers() if worker.get("enabled", True)]


def has_available_remote_worker(stage_kind: str | None = None) -> bool:
    for summary in list_worker_summaries():
        if summary.get("status") != "connected":
            continue
        capabilities = set(summary.get("capabilities", []))
        if stage_kind:
            if stage_kind in capabilities:
                return True
        elif capabilities & REMOTE_STAGE_KINDS:
            return True
    return False


def hybrid_runtime_summary() -> dict[str, Any]:
    workers = list_worker_summaries()
    connected_workers = [worker for worker in workers if worker.get("status") == "connected"]
    summary = {
        "mode": "hybrid_solution_a",
        "hybrid_ready": bool(connected_workers),
        "dispatch_model": "cloud_api_dispatch",
        "browser_execution": "mac_worker",
        "aggregation_execution": "api_local_worker",
        "recommended_first_run_mode": "browser",
        "recommended_schedule_mode": "adaptive",
        "workflow_summary": "云上发任务，Mac 自动执行浏览器采集；默认仅在你手动触发时运行，除非你明确开启自动调度。",
        "connected_worker_count": len(connected_workers),
        "worker_count": len(workers),
        "workers": workers,
    }
    summary.update(runtime_alerts_summary(workers))
    return summary


def parse_cookie_header(raw_cookie: str | None) -> dict[str, str]:
    if not raw_cookie:
        return {}
    result = {}
    for chunk in raw_cookie.split(";"):
        if "=" not in chunk:
            continue
        key, value = chunk.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def parse_bearer_token(value: str | None) -> str | None:
    if not value:
        return None
    if not value.lower().startswith("bearer "):
        return None
    token = value[7:].strip()
    return token or None


def parse_allowed_origins(raw: str) -> set[str]:
    values = {item.strip() for item in (raw or "").split(",") if item.strip()}
    return values


def ensure_role(user: dict[str, Any] | None, minimum_role: str) -> bool:
    current = ROLE_ORDER.get((user or {}).get("role", "viewer"), 0)
    required = ROLE_ORDER.get(minimum_role, 99)
    return current >= required


def sanitize_user(user: dict[str, Any] | None) -> dict[str, Any] | None:
    if not user:
        return None
    return {
        "id": user.get("id"),
        "name": user.get("name"),
        "email": user.get("email"),
        "role": user.get("role"),
    }


def study_file(study_id: str) -> Path:
    return STUDIES_DIR / f"{study_id}.json"


def study_config_file(study_id: str) -> Path:
    return STUDY_CONFIG_DIR / f"{study_id}.json"


def study_payload_json_file(study_id: str) -> Path:
    return STUDY_PRODUCT_DATA_DIR / f"{study_id}-payload.json"


def study_payload_js_file(study_id: str) -> Path:
    return STUDY_PRODUCT_DATA_DIR / f"{study_id}-payload.js"


def study_raw_file(study_id: str) -> Path:
    return STUDY_RAW_DIR / f"{study_id}.jsonl"


def study_report_file(study_id: str) -> Path:
    return STUDY_REPORT_DIR / f"{study_id}.md"


def study_entity_root(study_id: str) -> Path:
    return STUDY_ENTITY_DIR / study_id


def study_entity_file(study_id: str, name: str) -> Path:
    return study_entity_root(study_id) / f"{name}.json"


def job_file(job_id: str) -> Path:
    return JOBS_DIR / f"{job_id}.json"


def summarize_record(record: dict[str, Any]) -> dict[str, Any]:
    payload = record["payload"]
    jobs = list_jobs_for_study(record["id"])
    active_job_count = sum(1 for job in jobs if job_is_active(job))
    active_jobs = sorted(
        [job for job in jobs if job_is_active(job)],
        key=queued_job_sort_key,
    )
    lead_job = active_jobs[0] if active_jobs else {}
    queue_lane_summary = {
        lane: sum(1 for job in active_jobs if job.get("queue_lane") == lane)
        for lane in QUEUE_LANE_ORDER
    }
    data_foundation = record.get("data_foundation", {})
    freshness = data_foundation.get("freshness", {})
    coverage = data_foundation.get("coverage", {})
    hot_refresh = data_foundation.get("hot_refresh", {})
    runtime = hybrid_runtime_summary()
    return {
        "id": record["id"],
        "title": record["study"]["title"],
        "market": record["study"]["market"],
        "business_line": record["study"].get("business_line", ""),
        "primary_goal": record["study"].get("primary_goal", ""),
        "updated_at": record["updated_at"],
        "status": record["status"],
        "lead_package": payload.get("weeklyBrief", {}).get("leadPackage", ""),
        "headline": payload.get("summary", {}).get("headline", ""),
        "source_type": record.get("source", {}).get("type", ""),
        "config_path": record.get("artifacts", {}).get("config_path", ""),
        "schedule": record.get("schedule", {}),
        "active_job_count": active_job_count,
        "thread_count": data_foundation.get("thread_count", 0),
        "comment_count": data_foundation.get("comment_count", 0),
        "comment_capture_state": data_foundation.get("comment_capture_state", "thread_only"),
        "comment_capture_rate": coverage.get("comment_coverage", 0),
        "freshness_score": freshness.get("freshness_score", 0),
        "last_entity_refresh_at": freshness.get("last_entity_refresh_at"),
        "build_number": data_foundation.get("refresh", {}).get("build_number", 0),
        "incremental_mode": data_foundation.get("refresh", {}).get("incremental_mode", "bootstrap"),
        "new_threads": data_foundation.get("refresh", {}).get("new_threads", 0),
        "refreshed_threads": data_foundation.get("refresh", {}).get("refreshed_threads", 0),
        "new_comments": data_foundation.get("refresh", {}).get("new_comments", 0),
        "active_queue_lane": lead_job.get("queue_lane"),
        "active_priority_label": lead_job.get("priority_label"),
        "active_priority_score": lead_job.get("priority_score"),
        "active_requested_mode": lead_job.get("requested_mode"),
        "active_resolved_mode": lead_job.get("resolved_mode") or lead_job.get("mode"),
        "active_strategy_reason": lead_job.get("strategy_reason"),
        "active_stage_kind": lead_job.get("stage_kind"),
        "active_stage_label": lead_job.get("stage_label"),
        "active_pipeline_progress": lead_job.get("pipeline_progress"),
        "queue_lane_summary": queue_lane_summary,
        "hot_thread_candidate_count": hot_refresh.get("candidate_count", 0),
        "hot_thread_selected_count": hot_refresh.get("selected_count", 0),
        "hot_thread_stale_count": hot_refresh.get("stale_candidate_count", 0),
        "hot_thread_recommended_mode": hot_refresh.get("recommended_mode", "browser"),
        "workflow": {
            "dispatch_model": runtime.get("dispatch_model"),
            "browser_execution": runtime.get("browser_execution"),
            "aggregation_execution": runtime.get("aggregation_execution"),
            "recommended_schedule_mode": runtime.get("recommended_schedule_mode"),
            "hybrid_ready": runtime.get("hybrid_ready", False),
            "connected_worker_count": runtime.get("connected_worker_count", 0),
            "description": runtime.get("workflow_summary"),
        },
    }


def save_study_record(record: dict[str, Any]) -> None:
    STUDIES_DIR.mkdir(parents=True, exist_ok=True)
    study_file(record["id"]).write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def resolve_server_path(path_value: str | None) -> Path | None:
    if not path_value:
        return None

    raw_path = Path(path_value)
    remapped_candidates: list[Path] = []

    for legacy_root in LEGACY_SERVER_ROOTS:
        try:
            relative = raw_path.relative_to(legacy_root)
            remapped_candidates.append(SERVER_ROOT / relative)
        except ValueError:
            continue

    candidates: list[Path] = list(remapped_candidates)
    if raw_path.is_absolute():
        candidates.append(raw_path)
    else:
        candidates.append(SERVER_ROOT / raw_path)

    for candidate in candidates:
        try:
            if candidate.exists():
                return candidate
        except OSError:
            continue

    return candidates[-1]


def rewrite_record_paths(record: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    changed = False
    source = record.setdefault("source", {})
    artifacts = record.setdefault("artifacts", {})

    for key in SOURCE_PATH_KEYS:
        current = source.get(key)
        resolved = resolve_server_path(current)
        if resolved and str(resolved) != current:
            source[key] = str(resolved)
            changed = True

    for key in ARTIFACT_PATH_KEYS:
        current = artifacts.get(key)
        resolved = resolve_server_path(current)
        if resolved and str(resolved) != current:
            artifacts[key] = str(resolved)
            changed = True

    return record, changed


def maybe_upgrade_record(record: dict[str, Any]) -> dict[str, Any]:
    record, path_rewritten = rewrite_record_paths(record)
    schedule_rewritten = False
    if "schedule" not in record:
        record["schedule"] = {
            "enabled": False,
            "mode": "adaptive",
            "interval_hours": 24,
            "last_run_at": None,
            "next_run_at": None,
        }
    schedule = record.get("schedule", {})
    supports_remote_browser = bool(
        record.get("artifacts", {}).get("config_path")
        or record.get("source", {}).get("browser_config_path")
    )
    if (
        schedule.get("enabled")
        and schedule.get("mode") == "seeded"
        and supports_remote_browser
        and has_available_remote_worker("discover")
    ):
        schedule["mode"] = "adaptive"
        if not has_active_job(record["id"]):
            foundation = record.get("data_foundation", {}) or {}
            if foundation.get("comment_capture_state") in {"thread_only", "partial"} or int(foundation.get("comment_count", 0) or 0) == 0:
                schedule["next_run_at"] = now_iso()
        record["schedule"] = schedule
        schedule_rewritten = True
    artifacts = record.get("artifacts", {})
    source = record.get("source", {})
    if artifacts.get("manifest_path") and not record.get("data_foundation"):
        record["data_foundation"] = load_json_file(Path(artifacts["manifest_path"]), {})
    if record.get("data_foundation") and not record.get("data_foundation", {}).get("hot_refresh"):
        input_path = Path(source.get("input_path") or str(DEFAULT_INPUT))
        if input_path.exists():
            record = materialize_record(record, input_path)
            save_study_record(record)
        else:
            config = load_study_config(record)
            entity_bundle = load_study_entity_bundle(record["id"])
            if entity_bundle.get("threads"):
                entity_bundle = attach_hot_refresh_summary(entity_bundle, config)
                manifest_path = artifacts.get("manifest_path")
                if manifest_path:
                    Path(manifest_path).write_text(
                        json.dumps(entity_bundle["manifest"], ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )
                record["data_foundation"] = entity_bundle["manifest"]
                save_study_record(record)
    if (
        artifacts.get("config_path")
        and artifacts.get("payload_json_path")
        and artifacts.get("manifest_path")
        and source.get("input_path")
    ):
        if path_rewritten or schedule_rewritten:
            save_study_record(record)
        return record

    input_path = Path(source.get("input_path") or str(DEFAULT_INPUT))
    if not input_path.exists():
        if path_rewritten or schedule_rewritten:
            save_study_record(record)
        return record

    record = materialize_record(record, input_path)
    save_study_record(record)
    return record


def load_study_record(study_id: str) -> dict[str, Any] | None:
    path = study_file(study_id)
    if not path.exists():
        return None
    record = json.loads(path.read_text(encoding="utf-8"))
    return maybe_upgrade_record(record)


def list_study_records() -> list[dict[str, Any]]:
    if not STUDIES_DIR.exists():
        return []
    records = []
    for path in sorted(STUDIES_DIR.glob("*.json")):
        try:
            records.append(maybe_upgrade_record(json.loads(path.read_text(encoding="utf-8"))))
        except json.JSONDecodeError:
            continue
    records.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return records


def build_study_record(study_id: str, study_form: dict[str, Any], draft: dict[str, Any], payload: dict[str, Any], status: str) -> dict[str, Any]:
    return {
        "id": study_id,
        "status": status,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "study": draft["study"],
        "draft": draft,
        "payload": payload,
        "source": {},
        "artifacts": {},
        "data_foundation": {},
        "schedule": {
            "enabled": False,
            "mode": "adaptive",
            "interval_hours": 24,
            "last_run_at": None,
            "next_run_at": None,
        },
    }


def build_reddit_config(draft: dict[str, Any]) -> dict[str, Any]:
    return {
        "subreddits": draft.get("recommended_subreddits", ["dropship", "dropshipping"]),
        "search_terms": draft.get("recommended_keywords", ["3PL", "fulfillment service", "private supplier"]),
        "listing_sort": "new",
        "time_filter": "month",
        "limit_per_request": 25,
        "pages_per_term": 1,
        "include_listing_fetch": True,
        "request_delay_seconds": 1.5,
        "browser_wait_seconds": 12,
        "browser_scroll_rounds": 1,
        "browser_scroll_delay_seconds": 1.0,
        "browser_between_pages_seconds": 1.0,
        "thread_max_comments": 40,
        "thread_expand_rounds": 2,
        "thread_scroll_rounds": 3,
        "thread_delay_seconds": 1.0,
        "hot_thread_max_count": 10,
        "hot_thread_min_comments": 5,
        "hot_thread_min_score": 3,
        "hot_thread_max_age_hours": 168,
        "hot_thread_stale_after_hours": 8,
        "hot_thread_min_refresh_gap_minutes": 45,
    }


def ensure_support_dirs() -> None:
    for path in [
        STUDIES_DIR,
        STUDY_CONFIG_DIR,
        STUDY_PRODUCT_DATA_DIR,
        STUDY_RAW_DIR,
        STUDY_REPORT_DIR,
        STUDY_ENTITY_DIR,
        JOBS_DIR,
        RUNTIME_STATE_DIR,
        WORKER_STATE_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def write_study_config(study_id: str, config: dict[str, Any]) -> Path:
    ensure_support_dirs()
    path = study_config_file(study_id)
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def write_study_payload_files(study_id: str, payload: dict[str, Any]) -> tuple[Path, Path]:
    ensure_support_dirs()
    json_path = study_payload_json_file(study_id)
    js_path = study_payload_js_file(study_id)
    json_text = json.dumps(payload, ensure_ascii=False, indent=2)
    json_path.write_text(json_text + "\n", encoding="utf-8")
    js_path.write_text(f"window.__MVP_PAYLOAD__ = {json_text};\n", encoding="utf-8")
    return json_path, js_path


def load_json_file(path: Path, default: Any) -> Any:
    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    path.write_text(body, encoding="utf-8")


def load_study_entity_bundle(study_id: str) -> dict[str, Any]:
    return {
        "manifest": load_json_file(study_entity_file(study_id, "manifest"), {}),
        "threads": load_json_file(study_entity_file(study_id, "threads"), []),
        "thread_snapshots": load_json_file(study_entity_file(study_id, "thread_snapshots"), []),
        "comments": load_json_file(study_entity_file(study_id, "comments"), []),
        "comment_snapshots": load_json_file(study_entity_file(study_id, "comment_snapshots"), []),
        "signals": load_json_file(study_entity_file(study_id, "signals"), []),
    }


def canonical_row_key(row: dict[str, Any]) -> str:
    url = str(row.get("url", "")).split("?")[0].strip()
    if url:
        return url
    record_id = str(row.get("id", "")).strip()
    if record_id:
        return f"id:{record_id}"
    thread_id = str(row.get("thread_id", "")).strip()
    if thread_id:
        return f"thread:{thread_id}"
    return str(row.get("title", "")).strip()


def merge_stage_rows(existing_rows: list[dict[str, Any]], incoming_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def merge_row(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
        merged = dict(existing)
        for key, value in incoming.items():
            if key == "comments":
                existing_comments = existing.get("comments") or []
                incoming_comments = value or []
                merged[key] = incoming_comments if len(incoming_comments) >= len(existing_comments) else existing_comments
                continue
            if key in {"score", "num_comments"}:
                try:
                    merged[key] = max(int(existing.get(key, 0) or 0), int(value or 0))
                except (TypeError, ValueError):
                    merged[key] = value
                continue
            if key == "search_term":
                terms = {
                    term.strip()
                    for item in [existing.get("search_term", ""), value]
                    for term in str(item).split("|")
                    if term.strip()
                }
                merged[key] = " | ".join(sorted(terms))
                continue
            if value not in (None, "", []):
                merged[key] = value
        return merged

    merged: dict[str, dict[str, Any]] = {canonical_row_key(row): dict(row) for row in existing_rows}
    for row in incoming_rows:
        key = canonical_row_key(row)
        if key in merged:
            merged[key] = merge_row(merged[key], row)
        else:
            merged[key] = dict(row)
    return list(merged.values())


def build_hot_seed_rows(record: dict[str, Any], config: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    entity_bundle = load_study_entity_bundle(record["id"])
    threads = entity_bundle.get("threads", [])
    selection = summarize_hot_threads(threads, config)
    selected = rank_hot_threads(threads, config)[: int((selection.get("thresholds") or {}).get("max_count", 10))]
    if not selected:
        return [], selection

    existing_rows = read_jsonl(Path(record.get("source", {}).get("input_path") or study_raw_file(record["id"])))
    existing_lookup = {canonical_row_key(row): row for row in existing_rows}
    seeds: list[dict[str, Any]] = []
    for candidate in selected:
        existing = existing_lookup.get(candidate["url"]) or existing_lookup.get(f"thread:{candidate['thread_id']}") or {}
        seed = dict(existing)
        seed.update(
            {
                "thread_id": candidate["thread_id"],
                "subreddit": seed.get("subreddit") or candidate.get("subreddit", ""),
                "title": seed.get("title") or candidate.get("title", ""),
                "url": candidate["url"],
                "score": max(int(seed.get("score", 0) or 0), int(candidate.get("current_score", 0) or 0)),
                "num_comments": max(
                    int(seed.get("num_comments", 0) or 0),
                    int(candidate.get("current_comment_count", 0) or 0),
                ),
                "search_term": " | ".join(candidate.get("search_terms", [])).strip() or seed.get("search_term", ""),
                "refresh_reason": (
                    "missing_comments" if candidate.get("needs_comments")
                    else "stale_hot_thread" if candidate.get("stale")
                    else "active_hot_thread"
                ),
                "hot_score": candidate.get("hot_score", 0),
            }
        )
        seeds.append(seed)
    return seeds, selection


def load_study_config(record: dict[str, Any]) -> dict[str, Any]:
    config_path = record.get("artifacts", {}).get("config_path") or record.get("source", {}).get("browser_config_path")
    fallback = build_reddit_config(record["draft"])
    if not config_path:
        return fallback
    resolved = resolve_server_path(config_path)
    if not resolved:
        return fallback
    return load_json_file(resolved, fallback)


def attach_hot_refresh_summary(entity_bundle: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    manifest = entity_bundle.setdefault("manifest", {})
    manifest["hot_refresh"] = summarize_hot_threads(entity_bundle.get("threads", []), config)
    return entity_bundle


def worker_can_execute(worker: dict[str, Any], stage_kind: str) -> bool:
    return stage_kind in worker_capabilities(worker)


def running_remote_job_for_worker(worker_id: str) -> dict[str, Any] | None:
    for job in list_jobs():
        if (
            job.get("status") == "running"
            and job.get("execution_target") == "mac_worker"
            and job.get("claimed_by_worker_id") == worker_id
        ):
            return job
    return None


def next_claimable_remote_job(worker: dict[str, Any]) -> dict[str, Any] | None:
    queued_jobs = sorted(
        [
            job
            for job in list_jobs()
            if job.get("status") == "queued"
            and (job.get("execution_target") or stage_execution_target(job.get("stage_kind", ""))) == "mac_worker"
            and worker_can_execute(worker, job.get("stage_kind", ""))
        ],
        key=queued_job_sort_key,
    )
    return queued_jobs[0] if queued_jobs else None


def build_worker_task_payload(job: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    config = load_study_config(record)
    task: dict[str, Any] = {
        "job": enrich_job(job),
        "study": summarize_record(record),
        "config": config,
        "stage_kind": job.get("stage_kind"),
    }
    stage_kind = job.get("stage_kind")
    if stage_kind == "discover":
        task["output_kind"] = "discovery_rows"
        return task
    if stage_kind == "harvest":
        task["output_kind"] = "harvest_rows"
        task["input_rows"] = read_jsonl(discovery_output_path(record))
        return task
    if stage_kind == "refresh_hot":
        seeds, selection = build_hot_seed_rows(record, config)
        task["output_kind"] = "hot_refresh_rows"
        task["input_rows"] = seeds
        task["selection"] = selection
        return task
    raise RuntimeError(f"Unsupported worker stage: {stage_kind}")


def claim_remote_job(worker: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    running = running_remote_job_for_worker(worker.get("id", ""))
    if running:
        record = load_study_record(running.get("study_id", ""))
        if record:
            return running, build_worker_task_payload(running, record)
    job = next_claimable_remote_job(worker)
    if not job:
        return None, None
    job["status"] = "running"
    job["started_at"] = job.get("started_at") or now_iso()
    job["updated_at"] = now_iso()
    job["claimed_by_worker_id"] = worker.get("id")
    job["claimed_by_worker_name"] = worker.get("name", worker.get("id", ""))
    job["worker_claimed_at"] = now_iso()
    save_job(job)
    record = load_study_record(job.get("study_id", ""))
    if not record:
        raise RuntimeError(f"Study not found: {job.get('study_id')}")
    return job, build_worker_task_payload(job, record)


def apply_worker_stage_result(job: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    record = load_study_record(job["study_id"])
    if not record:
        raise RuntimeError(f"Study not found: {job['study_id']}")

    stage_kind = job.get("stage_kind")
    rows = payload.get("rows") or []
    summary = payload.get("summary") or {}

    if stage_kind == "discover":
        output_path = discovery_output_path(record)
        write_jsonl(output_path, rows)
        record.setdefault("source", {})["last_discovery_at"] = now_iso()
        record.setdefault("source", {})["last_discovery_summary"] = summary
        record.setdefault("artifacts", {})["discovery_output_path"] = str(output_path)
        save_study_record(record)
        return record

    if stage_kind == "harvest":
        output_path = Path(record.get("artifacts", {}).get("raw_output_path") or study_raw_file(record["id"]))
        write_jsonl(output_path, rows)
        record.setdefault("source", {})["type"] = "browser_reddit_thread_pipeline"
        record["source"]["input_path"] = str(output_path)
        record["source"]["last_harvest_at"] = now_iso()
        record["source"]["last_harvest_summary"] = summary
        save_study_record(record)
        return record

    if stage_kind == "refresh_hot":
        output_path = Path(record.get("artifacts", {}).get("raw_output_path") or study_raw_file(record["id"]))
        existing_rows = read_jsonl(Path(record.get("source", {}).get("input_path") or output_path))
        merged_rows = merge_stage_rows(existing_rows, rows)
        write_jsonl(output_path, merged_rows)
        record.setdefault("source", {})["type"] = "browser_reddit_thread_pipeline"
        record["source"]["input_path"] = str(output_path)
        record["source"]["last_hot_refresh_at"] = now_iso()
        record["source"]["last_hot_refresh_summary"] = summary
        save_study_record(record)
        return record

    raise RuntimeError(f"Unsupported worker stage result: {stage_kind}")


def save_job(job: dict[str, Any]) -> None:
    ensure_support_dirs()
    job_file(job["id"]).write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_job(job_id: str) -> dict[str, Any] | None:
    path = job_file(job_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def enrich_job(job: dict[str, Any]) -> dict[str, Any]:
    record = load_study_record(job.get("study_id", ""))
    enriched = dict(job)
    enriched["execution_target"] = enriched.get("execution_target") or stage_execution_target(enriched.get("stage_kind", ""))
    enriched["study_title"] = (record or {}).get("study", {}).get("title", job.get("study_id", ""))
    enriched["study_market"] = (record or {}).get("study", {}).get("market", "")
    enriched["schedule_enabled"] = (record or {}).get("schedule", {}).get("enabled", False)
    enriched["stage_label"] = stage_label(enriched.get("stage_kind", ""))
    stage_total = int(enriched.get("pipeline_stage_total", 0) or 0)
    stage_index = int(enriched.get("pipeline_stage_index", 0) or 0)
    if stage_total and not enriched.get("pipeline_progress"):
        enriched["pipeline_progress"] = f"{stage_index + 1}/{stage_total}"
    return enriched


def list_jobs() -> list[dict[str, Any]]:
    ensure_support_dirs()
    jobs = []
    for path in sorted(JOBS_DIR.glob("*.json")):
        try:
            jobs.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    jobs.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return jobs


def job_is_active(job: dict[str, Any]) -> bool:
    return job.get("status") in ACTIVE_JOB_STATUSES


def job_visible_in_operations(job: dict[str, Any]) -> bool:
    status = job.get("status")
    if status in ACTIVE_JOB_STATUSES:
        return True
    if status != "completed":
        return False
    finished_at = parse_iso(job.get("finished_at") or job.get("updated_at") or job.get("created_at"))
    if finished_at is None:
        return True
    return finished_at >= datetime.now() - timedelta(hours=JOB_DISPLAY_COMPLETED_WINDOW_HOURS)


def list_visible_jobs(study_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    jobs = list_jobs()
    if study_id:
        jobs = [job for job in jobs if job.get("study_id") == study_id]
    jobs = [job for job in jobs if job_visible_in_operations(job)]
    return jobs[:limit]


def list_jobs_for_study(study_id: str) -> list[dict[str, Any]]:
    return [job for job in list_jobs() if job.get("study_id") == study_id]


def recent_failed_jobs(window_hours: int = RUNTIME_ALERT_FAILURE_WINDOW_HOURS, limit: int = RUNTIME_ALERT_MAX_FAILURES) -> list[dict[str, Any]]:
    cutoff = datetime.now() - timedelta(hours=window_hours)
    failures = []
    for job in list_jobs():
        if job.get("status") != "failed":
            continue
        finished_at = parse_iso(job.get("finished_at") or job.get("updated_at") or job.get("created_at"))
        if finished_at and finished_at < cutoff:
            continue
        failures.append(enrich_job(job))
    return failures[:limit]


def runtime_alerts_summary(workers: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    worker_summaries = workers if workers is not None else list_worker_summaries()
    connected_workers = [worker for worker in worker_summaries if worker.get("status") == "connected"]
    stale_workers = [worker for worker in worker_summaries if worker.get("status") == "stale"]
    offline_workers = [worker for worker in worker_summaries if worker.get("status") == "offline"]
    active_jobs = [enrich_job(job) for job in list_jobs() if job_is_active(job)]
    canceling_jobs = [job for job in active_jobs if job.get("status") == "canceling"]
    failed_jobs = recent_failed_jobs()
    alerts: list[dict[str, Any]] = []

    if not connected_workers:
        alerts.append(
            {
                "id": "worker-offline",
                "level": "error",
                "title": "Mac Worker 离线",
                "message": "云上可以继续查看数据，但 browser / hot_threads 任务当前无法执行。",
                "action": "检查 Mac Worker LaunchAgent、登录状态和 Chrome 权限。",
            }
        )
    elif stale_workers:
        alerts.append(
            {
                "id": "worker-stale",
                "level": "warn",
                "title": f"{len(stale_workers)} 台 Worker 心跳陈旧",
                "message": "Worker 没有在心跳窗口内继续上报，可能休眠、断网或被系统暂停。",
                "action": "先看 Worker 状态卡和本机 LaunchAgent 状态脚本。",
            }
        )

    if offline_workers and connected_workers:
        alerts.append(
            {
                "id": "worker-partial-offline",
                "level": "warn",
                "title": f"{len(offline_workers)} 台 Worker 当前离线",
                "message": "仍有在线 Worker，可以继续执行，但容量和稳定性会下降。",
                "action": "必要时检查离线节点是否需要重启。",
            }
        )

    if failed_jobs:
        latest_failed = failed_jobs[0]
        alerts.append(
            {
                "id": "recent-failures",
                "level": "error",
                "title": f"最近 {len(failed_jobs)} 条任务失败",
                "message": f"最近失败任务：{latest_failed.get('study_title') or latest_failed.get('study_id')} · {latest_failed.get('stage_label') or latest_failed.get('stage_kind') or latest_failed.get('mode')}",
                "action": "打开 Operations 查看详情，并优先重跑最近失败任务。",
                "job_id": latest_failed.get("id"),
                "retryable": True,
            }
        )

    if canceling_jobs:
        alerts.append(
            {
                "id": "jobs-canceling",
                "level": "warn",
                "title": f"{len(canceling_jobs)} 条任务正在停止中",
                "message": "系统已经收到停止指令，正在等待 Worker 杀掉浏览器子进程并回写状态。",
                "action": "几秒后刷新一次；如果长期停留在 canceling，再检查 Worker 日志。",
            }
        )

    if not alerts:
        alerts.append(
            {
                "id": "runtime-healthy",
                "level": "success",
                "title": "运行稳定",
                "message": "Worker 在线，最近没有新的失败任务，当前可以继续发起研究和刷新。",
                "action": "默认保持手动运行；只有你明确需要定时刷新时再开启自动调度。",
            }
        )

    return {
        "alerts": alerts,
        "recent_failed_jobs": failed_jobs,
        "recent_failed_job_count": len(failed_jobs),
        "active_job_count": len(active_jobs),
        "canceling_job_count": len(canceling_jobs),
        "worker_status_summary": {
            "connected": len(connected_workers),
            "stale": len(stale_workers),
            "offline": len(offline_workers),
        },
    }


def priority_label(priority_score: int) -> str:
    if priority_score >= 90:
        return "urgent"
    if priority_score >= 70:
        return "high"
    if priority_score >= 45:
        return "normal"
    return "low"


def mode_requires_admin(mode: str) -> bool:
    return mode in BROWSER_JOB_MODES or mode == "adaptive"


def pipeline_stages_for_mode(resolved_mode: str) -> list[str]:
    return list(PIPELINE_STAGE_SEQUENCE.get(resolved_mode, PIPELINE_STAGE_SEQUENCE["seeded"]))


def stage_label(stage_kind: str) -> str:
    return STAGE_LABELS.get(stage_kind, stage_kind or "unknown")


def stage_lane(stage_kind: str) -> str:
    return STAGE_QUEUE_LANE.get(stage_kind, "maintenance")


def stage_priority_score(base_priority: int, stage_kind: str) -> int:
    return max(1, min(int(base_priority) + int(STAGE_PRIORITY_OFFSET.get(stage_kind, 0)), 99))


def stage_execution_target(stage_kind: str) -> str:
    if stage_kind in REMOTE_STAGE_KINDS:
        return "mac_worker"
    return "local"


def choose_adaptive_mode(record: dict[str, Any]) -> tuple[str, str]:
    foundation = record.get("data_foundation", {}) or {}
    hot_refresh = foundation.get("hot_refresh", {}) or {}
    if not has_available_remote_worker():
        return "seeded", "远程 Mac Worker 未连接，暂时回退为 seeded 重建；连接后会自动恢复 thread/comment 刷新。"
    if hot_refresh.get("selected_count", 0) > 0 and hot_refresh.get("recommended_mode") == "hot_threads":
        return "hot_threads", "存在高价值 stale thread，优先增量刷新评论和热度。"
    if foundation.get("comment_capture_state") in {"thread_only", "partial"}:
        return "browser", "评论覆盖不足，优先做一次完整 thread 发现与 harvest。"
    if foundation.get("freshness", {}).get("freshness_score", 0) < 70:
        return "browser", "整体新鲜度偏低，优先做一次完整浏览器刷新。"
    return "seeded", "当前没有热点 thread，先做轻量 seeded 重建。"


def build_job_plan(record: dict[str, Any], requested_mode: str, trigger: str) -> dict[str, Any]:
    foundation = record.get("data_foundation", {}) or {}
    hot_refresh = foundation.get("hot_refresh", {}) or {}
    comment_state = foundation.get("comment_capture_state", "thread_only")
    freshness_score = int((foundation.get("freshness", {}) or {}).get("freshness_score", 0) or 0)

    if requested_mode == "adaptive":
        resolved_mode, strategy_reason = choose_adaptive_mode(record)
    else:
        resolved_mode = requested_mode
        strategy_reason = "按用户指定模式执行。"

    if resolved_mode == "hot_threads":
        priority_score = 78
        priority_score += min(int(hot_refresh.get("selected_count", 0) or 0), 12)
        priority_score += min(int(hot_refresh.get("stale_candidate_count", 0) or 0), 8)
        if comment_state != "full":
            priority_score += 4
    elif resolved_mode == "browser":
        priority_score = 56
        if comment_state != "full":
            priority_score += 8
        if freshness_score < 70:
            priority_score += 6
    else:
        priority_score = 28
        if freshness_score < 60:
            priority_score += 4

    if trigger == "manual":
        priority_score += 6
    elif trigger.startswith("retry:"):
        priority_score += 4
    elif trigger == "schedule":
        priority_score += 1

    priority_score = max(1, min(priority_score, 99))
    pipeline_stages = pipeline_stages_for_mode(resolved_mode)
    first_stage = pipeline_stages[0]
    stage_score = stage_priority_score(priority_score, first_stage)
    return {
        "requested_mode": requested_mode,
        "resolved_mode": resolved_mode,
        "pipeline_stages": pipeline_stages,
        "stage_kind": first_stage,
        "stage_label": stage_label(first_stage),
        "execution_target": stage_execution_target(first_stage),
        "queue_lane": stage_lane(first_stage),
        "base_priority_score": priority_score,
        "priority_score": stage_score,
        "priority_label": priority_label(stage_score),
        "strategy_reason": strategy_reason,
    }


def active_jobs_for_study(study_id: str) -> list[dict[str, Any]]:
    return [
        job
        for job in list_jobs_for_study(study_id)
        if job_is_active(job)
    ]


def enqueue_job(study_id: str, mode: str, actor: dict[str, Any] | None, trigger: str = "manual") -> dict[str, Any]:
    record = load_study_record(study_id)
    if not record:
        raise RuntimeError(f"Study not found: {study_id}")
    plan = build_job_plan(record, mode, trigger)
    active_jobs = active_jobs_for_study(study_id)
    running_job = next((job for job in active_jobs if job.get("status") == "running"), None)
    if running_job:
        raise RuntimeError("job_already_running")
    queued_job = next((job for job in active_jobs if job.get("status") == "queued"), None)
    if queued_job:
        should_upgrade = (
            int(plan["priority_score"]) > int(queued_job.get("priority_score", 0) or 0)
            or plan["resolved_mode"] != queued_job.get("resolved_mode")
        )
        if should_upgrade:
            queued_job["requested_mode"] = plan["requested_mode"]
            queued_job["mode"] = plan["resolved_mode"]
            queued_job["resolved_mode"] = plan["resolved_mode"]
            queued_job["pipeline_stages"] = plan["pipeline_stages"]
            queued_job["stage_kind"] = plan["stage_kind"]
            queued_job["stage_label"] = plan["stage_label"]
            queued_job["execution_target"] = plan["execution_target"]
            queued_job["pipeline_stage_index"] = 0
            queued_job["pipeline_stage_total"] = len(plan["pipeline_stages"])
            queued_job["pipeline_progress"] = f"1/{len(plan['pipeline_stages'])}"
            queued_job["queue_lane"] = plan["queue_lane"]
            queued_job["base_priority_score"] = plan["base_priority_score"]
            queued_job["priority_score"] = plan["priority_score"]
            queued_job["priority_label"] = plan["priority_label"]
            queued_job["strategy_reason"] = plan["strategy_reason"]
            queued_job["trigger"] = trigger
            queued_job["actor_id"] = (actor or {}).get("id", "system")
            queued_job["actor_role"] = (actor or {}).get("role", "system")
            queued_job["updated_at"] = now_iso()
            save_job(queued_job)
            queued_job["queue_action"] = "upgraded"
            return queued_job
        queued_job["queue_action"] = "coalesced"
        return queued_job

    job = {
        "id": f"job-{uuid.uuid4().hex[:10]}",
        "study_id": study_id,
        "pipeline_id": f"pipe-{uuid.uuid4().hex[:10]}",
        "requested_mode": plan["requested_mode"],
        "mode": plan["resolved_mode"],
        "resolved_mode": plan["resolved_mode"],
        "pipeline_stages": plan["pipeline_stages"],
        "stage_kind": plan["stage_kind"],
        "stage_label": plan["stage_label"],
        "execution_target": plan["execution_target"],
        "pipeline_stage_index": 0,
        "pipeline_stage_total": len(plan["pipeline_stages"]),
        "pipeline_progress": f"1/{len(plan['pipeline_stages'])}",
        "queue_lane": plan["queue_lane"],
        "base_priority_score": plan["base_priority_score"],
        "priority_score": plan["priority_score"],
        "priority_label": plan["priority_label"],
        "strategy_reason": plan["strategy_reason"],
        "trigger": trigger,
        "status": "queued",
        "actor_id": (actor or {}).get("id", "system"),
        "actor_role": (actor or {}).get("role", "system"),
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "started_at": None,
        "finished_at": None,
        "error": None,
        "queue_action": "queued",
    }
    save_job(job)
    return job


def has_active_job(study_id: str) -> bool:
    return any(job_is_active(job) and job.get("study_id") == study_id for job in list_jobs_for_study(study_id))


def request_job_cancellation(job: dict[str, Any], actor: dict[str, Any] | None = None) -> dict[str, Any]:
    status = job.get("status")
    timestamp = now_iso()
    actor = actor or {}
    if status == "queued":
        job["status"] = "canceled"
        job["finished_at"] = timestamp
        job["updated_at"] = timestamp
        job["cancel_requested_at"] = timestamp
    elif status in {"running", "canceling"}:
        job["status"] = "canceling"
        job["updated_at"] = timestamp
        job["cancel_requested_at"] = timestamp
    else:
        raise ValueError(f"job_not_cancelable:{status}")
    if actor:
        job["cancel_requested_by"] = actor.get("id") or actor.get("email") or actor.get("name") or "unknown"
        job["cancel_requested_role"] = actor.get("role") or "unknown"
    save_job(job)
    return job


def cancel_active_jobs_for_study(study_id: str, actor: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    canceled_jobs = []
    for job in list_jobs_for_study(study_id):
        if not job_is_active(job):
            continue
        canceled_jobs.append(enrich_job(request_job_cancellation(job, actor=actor)))
    return canceled_jobs


def queued_job_sort_key(job: dict[str, Any]) -> tuple[int, int, str]:
    lane = job.get("queue_lane", "maintenance")
    lane_rank = QUEUE_LANE_ORDER.get(lane, 99)
    priority = int(job.get("priority_score", 0) or 0)
    return (lane_rank, -priority, job.get("created_at", ""))


def next_stage_job(completed_job: dict[str, Any]) -> dict[str, Any] | None:
    stages = list(completed_job.get("pipeline_stages") or [])
    if not stages:
        return None
    current_index = int(completed_job.get("pipeline_stage_index", 0) or 0)
    next_index = current_index + 1
    if next_index >= len(stages):
        return None

    stage_kind = stages[next_index]
    base_priority = int(completed_job.get("base_priority_score", completed_job.get("priority_score", 0)) or 0)
    score = stage_priority_score(base_priority, stage_kind)
    return {
        "id": f"job-{uuid.uuid4().hex[:10]}",
        "study_id": completed_job["study_id"],
        "pipeline_id": completed_job.get("pipeline_id") or f"pipe-{uuid.uuid4().hex[:10]}",
        "requested_mode": completed_job.get("requested_mode", completed_job.get("resolved_mode", "seeded")),
        "mode": completed_job.get("resolved_mode", completed_job.get("mode", "seeded")),
        "resolved_mode": completed_job.get("resolved_mode", completed_job.get("mode", "seeded")),
        "pipeline_stages": stages,
        "stage_kind": stage_kind,
        "stage_label": stage_label(stage_kind),
        "execution_target": stage_execution_target(stage_kind),
        "pipeline_stage_index": next_index,
        "pipeline_stage_total": len(stages),
        "pipeline_progress": f"{next_index + 1}/{len(stages)}",
        "queue_lane": stage_lane(stage_kind),
        "base_priority_score": base_priority,
        "priority_score": score,
        "priority_label": priority_label(score),
        "strategy_reason": completed_job.get("strategy_reason", ""),
        "trigger": f"followup:{completed_job.get('stage_kind', 'pipeline')}",
        "status": "queued",
        "actor_id": "system",
        "actor_role": "system",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "started_at": None,
        "finished_at": None,
        "error": None,
        "queue_action": "pipeline_follow_up",
        "parent_job_id": completed_job.get("id"),
    }


def attach_study_runtime(
    record: dict[str, Any],
    input_path: Path,
    entity_paths: dict[str, Path] | None = None,
    entity_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = build_reddit_config(record["draft"])
    config_path = write_study_config(record["id"], config)
    payload_json, payload_js = write_study_payload_files(record["id"], record["payload"])
    entity_root = study_entity_root(record["id"])
    raw_output = study_raw_file(record["id"])
    discovered_output = raw_output.with_name(f"{raw_output.stem}_discovered{raw_output.suffix or '.jsonl'}")
    entity_paths = entity_paths or {
        "manifest": study_entity_file(record["id"], "manifest"),
        "threads": study_entity_file(record["id"], "threads"),
        "thread_snapshots": study_entity_file(record["id"], "thread_snapshots"),
        "comments": study_entity_file(record["id"], "comments"),
        "comment_snapshots": study_entity_file(record["id"], "comment_snapshots"),
        "signals": study_entity_file(record["id"], "signals"),
    }
    record["source"] = {
        "type": "seeded_jsonl",
        "input_path": str(input_path),
        "browser_config_path": str(config_path),
        "recommended_subreddits": record["draft"].get("recommended_subreddits", []),
        "recommended_keywords": record["draft"].get("recommended_keywords", []),
    }
    record["artifacts"] = {
        "config_path": str(config_path),
        "payload_json_path": str(payload_json),
        "payload_js_path": str(payload_js),
        "raw_output_path": str(raw_output),
        "discovery_output_path": str(discovered_output),
        "report_output_path": str(study_report_file(record["id"])),
        "entity_root_path": str(entity_root),
        "manifest_path": str(entity_paths["manifest"]),
        "threads_path": str(entity_paths["threads"]),
        "thread_snapshots_path": str(entity_paths["thread_snapshots"]),
        "comments_path": str(entity_paths["comments"]),
        "comment_snapshots_path": str(entity_paths["comment_snapshots"]),
        "signals_path": str(entity_paths["signals"]),
    }
    record["data_foundation"] = entity_manifest or load_json_file(entity_paths["manifest"], {})
    record["updated_at"] = now_iso()
    return record


def materialize_record(record: dict[str, Any], input_path: Path) -> dict[str, Any]:
    records = read_jsonl(input_path)
    entity_bundle, entity_paths = build_and_write_store(input_path, record["id"], study_entity_root(record["id"]))
    config = load_study_config(record)
    entity_bundle = attach_hot_refresh_summary(entity_bundle, config)
    entity_paths["manifest"].write_text(
        json.dumps(entity_bundle["manifest"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    payload = build_dataset_from_records(
        records,
        record["study"]["title"],
        record["study"]["market"],
        record["study"].get("time_window", "近 30 天"),
        entity_bundle=entity_bundle,
    )
    record["payload"] = payload
    return attach_study_runtime(
        record,
        input_path,
        entity_paths=entity_paths,
        entity_manifest=entity_bundle["manifest"],
    )


def discovery_output_path(record: dict[str, Any]) -> Path:
    artifact_path = record.get("artifacts", {}).get("discovery_output_path")
    if artifact_path:
        return Path(artifact_path)
    raw_output = Path(record.get("artifacts", {}).get("raw_output_path") or study_raw_file(record["id"]))
    return raw_output.with_name(f"{raw_output.stem}_discovered{raw_output.suffix or '.jsonl'}")


def run_discover_stage(record: dict[str, Any], continue_on_error: bool = True) -> Path:
    config_path = record.get("source", {}).get("browser_config_path") or record.get("artifacts", {}).get("config_path")
    output_path = discovery_output_path(record)
    if not config_path:
        raise RuntimeError("Study is missing browser config path.")

    command = [
        sys.executable,
        "scripts/discover_threads.py",
        "--config",
        config_path,
        "--output",
        str(output_path),
    ]
    if continue_on_error:
        command.append("--continue-on-error")
    subprocess.run(command, check=True, cwd=str(SERVER_ROOT))
    return output_path


def run_harvest_stage(record: dict[str, Any], continue_on_error: bool = True) -> Path:
    config_path = record.get("source", {}).get("browser_config_path") or record.get("artifacts", {}).get("config_path")
    raw_output_path = record.get("artifacts", {}).get("raw_output_path")
    discovered_path = discovery_output_path(record)
    if not config_path or not raw_output_path:
        raise RuntimeError("Study is missing harvest artifact paths.")
    if not discovered_path.exists():
        raise RuntimeError("Discovery output missing for harvest stage.")

    config = load_json_file(Path(config_path), {})
    command = [
        sys.executable,
        "scripts/harvest_threads.py",
        "--input",
        str(discovered_path),
        "--output",
        raw_output_path,
        "--max-comments",
        str(int(config.get("thread_max_comments", 40))),
        "--expand-rounds",
        str(int(config.get("thread_expand_rounds", 2))),
        "--scroll-rounds",
        str(int(config.get("thread_scroll_rounds", 3))),
        "--delay-seconds",
        str(float(config.get("thread_delay_seconds", 1.0))),
        "--browser-wait",
        str(float(config.get("browser_wait_seconds", 15.0))),
    ]
    if continue_on_error:
        command.append("--continue-on-error")
    subprocess.run(command, check=True, cwd=str(SERVER_ROOT))
    return Path(raw_output_path)


def run_browser_rebuild(record: dict[str, Any]) -> Path:
    config_path = record.get("source", {}).get("browser_config_path") or record.get("artifacts", {}).get("config_path")
    raw_output_path = record.get("artifacts", {}).get("raw_output_path")
    report_output_path = record.get("artifacts", {}).get("report_output_path")
    if not config_path or not raw_output_path or not report_output_path:
        raise RuntimeError("Study is missing browser config or artifact paths.")
    discovered_path = discovery_output_path(record)

    command = [
        sys.executable,
        "scripts/reddit_thread_pipeline.py",
        "--config",
        config_path,
        "--raw-output",
        raw_output_path,
        "--report-output",
        report_output_path,
        "--discovery-output",
        str(discovered_path),
        "--continue-on-error",
    ]
    subprocess.run(command, check=True, cwd=str(SERVER_ROOT))
    return Path(raw_output_path)


def run_hot_thread_rebuild(record: dict[str, Any]) -> Path:
    config_path = record.get("source", {}).get("browser_config_path") or record.get("artifacts", {}).get("config_path")
    raw_output_path = record.get("artifacts", {}).get("raw_output_path")
    report_output_path = record.get("artifacts", {}).get("report_output_path")
    entity_root_path = record.get("artifacts", {}).get("entity_root_path")
    input_path = record.get("source", {}).get("input_path")
    if not config_path or not raw_output_path or not report_output_path or not entity_root_path or not input_path:
        raise RuntimeError("Study is missing hot-thread refresh paths.")

    command = [
        sys.executable,
        "scripts/refresh_hot_threads.py",
        "--config",
        config_path,
        "--entity-root",
        entity_root_path,
        "--input",
        input_path,
        "--output",
        raw_output_path,
        "--report-output",
        report_output_path,
        "--continue-on-error",
    ]
    subprocess.run(command, check=True, cwd=str(SERVER_ROOT))
    return Path(raw_output_path)


def process_job(job: dict[str, Any]) -> dict[str, Any]:
    study_id = job["study_id"]
    record = load_study_record(study_id)
    if not record:
        raise RuntimeError(f"Study not found: {study_id}")

    input_path = Path(record.get("source", {}).get("input_path") or str(DEFAULT_INPUT))
    stage_kind = job.get("stage_kind") or job.get("mode")

    if stage_kind == "discover":
        discovered_path = run_discover_stage(record, continue_on_error=True)
        record.setdefault("source", {})["last_discovery_at"] = now_iso()
        record.setdefault("artifacts", {})["discovery_output_path"] = str(discovered_path)
        save_study_record(record)
        return record

    if stage_kind == "harvest":
        input_path = run_harvest_stage(record, continue_on_error=True)
        record.setdefault("source", {})["type"] = "browser_reddit_thread_pipeline"
        record["source"]["input_path"] = str(input_path)
        record["source"]["last_harvest_at"] = now_iso()
        save_study_record(record)
        return record

    if stage_kind == "refresh_hot":
        input_path = run_hot_thread_rebuild(record)
        record.setdefault("source", {})["type"] = "browser_reddit_thread_pipeline"
        record["source"]["input_path"] = str(input_path)
        record["source"]["last_hot_refresh_at"] = now_iso()
        save_study_record(record)
        return record

    if stage_kind == "rebuild_aggregates":
        record = materialize_record(record, input_path)
        record["schedule"]["last_run_at"] = now_iso()
        if record["schedule"].get("enabled"):
            interval = int(record["schedule"].get("interval_hours", 24) or 24)
            record["schedule"]["next_run_at"] = (datetime.now() + timedelta(hours=interval)).isoformat(timespec="seconds")
        save_study_record(record)
        return record

    if stage_kind == "publish_brief":
        publication = {
            "published_at": now_iso(),
            "lead_package": record.get("payload", {}).get("weeklyBrief", {}).get("leadPackage", ""),
            "headline": record.get("payload", {}).get("summary", {}).get("headline", ""),
            "pipeline_id": job.get("pipeline_id"),
            "source_mode": job.get("resolved_mode", job.get("mode")),
        }
        record["publication"] = publication
        record["updated_at"] = publication["published_at"]
        save_study_record(record)
        return record

    raise RuntimeError(f"Unsupported stage: {stage_kind}")


def enqueue_follow_up_job(completed_job: dict[str, Any]) -> dict[str, Any] | None:
    follow_up = next_stage_job(completed_job)
    if not follow_up:
        return None
    save_job(follow_up)
    return follow_up


def worker_loop(stop_event: threading.Event) -> None:
    while not stop_event.is_set():
        queued = sorted(
            [
                job
                for job in list_jobs()
                if job.get("status") == "queued"
                and (job.get("execution_target") or stage_execution_target(job.get("stage_kind", ""))) == "local"
            ],
            key=queued_job_sort_key,
        )
        if not queued:
            time.sleep(1.0)
            continue

        job = queued[0]
        job["status"] = "running"
        job["started_at"] = now_iso()
        job["updated_at"] = now_iso()
        save_job(job)

        try:
            process_job(job)
            job["status"] = "completed"
            job["finished_at"] = now_iso()
        except Exception as error:  # noqa: BLE001
            job["status"] = "failed"
            job["finished_at"] = now_iso()
            job["error"] = str(error)
        job["updated_at"] = now_iso()
        save_job(job)
        if job["status"] == "completed":
            enqueue_follow_up_job(job)


def scheduler_loop(stop_event: threading.Event) -> None:
    while not stop_event.is_set():
        now = datetime.now()
        for record in list_study_records():
            schedule = record.get("schedule", {})
            if not schedule.get("enabled"):
                continue
            next_run = parse_iso(schedule.get("next_run_at"))
            if next_run is None:
                interval = int(schedule.get("interval_hours", 24) or 24)
                schedule["next_run_at"] = (now + timedelta(hours=interval)).isoformat(timespec="seconds")
                record["schedule"] = schedule
                save_study_record(record)
                continue
            if next_run <= now and not has_active_job(record["id"]):
                enqueue_job(record["id"], schedule.get("mode", "adaptive"), actor=None, trigger="schedule")
                interval = int(schedule.get("interval_hours", 24) or 24)
                record["schedule"]["next_run_at"] = (now + timedelta(hours=interval)).isoformat(timespec="seconds")
                save_study_record(record)
        time.sleep(5.0)


def ensure_seed_study(input_path: Path, study_title: str, market: str, date_range: str) -> None:
    if load_study_record(STUDY_ID):
        return
    draft = {
        "study": {
            "title": study_title,
            "market": market,
            "business_line": "Dropshipping 供应链服务",
            "region": "美国",
            "target_customer": "已出单但履约混乱的卖家",
            "primary_goal": "选客群 + 定产品包装",
            "problem_space": "履约与发货、private supplier、3PL 切换、shipping delays、退款压力",
            "time_window": date_range,
        },
        "focus_statement": "围绕美国 dropshipping 卖家的履约与 supplier 问题，支持业务线负责人做客群和产品判断。",
        "recommended_sources": ["Reddit"],
        "recommended_subreddits": ["dropship", "dropshipping", "ecommerce", "shopify"],
        "recommended_keywords": ["3PL", "fulfillment service", "shipping delays", "private supplier", "sourcing agent"],
        "recommended_hypotheses": draft_hypotheses({"business_line": "dropshipping", "problem_space": "履约与 supplier"}),
        "recommended_outputs": DEFAULT_TEMPLATE["recommended_outputs"],
        "decision_checks": [
            "Fulfillment 还是 Supplier 应该先主打？",
            "哪个客群最适合作为第一主战场？",
        ],
    }
    record = build_study_record(
        STUDY_ID,
        draft["study"],
        draft,
        {},
        status="seeded_demo_data",
    )
    record = materialize_record(record, input_path)
    save_study_record(record)


def build_api_bundle(payload: dict) -> dict:
    dashboard = payload
    segments = payload["segments"]
    packages = payload["packages"]
    weekly = payload["weeklyBrief"]
    evidence = payload["evidence"]

    segment_details = {}
    for segment in segments:
        matching_evidence = [item for item in evidence if item["segment"] == segment["name"]]
        segment_details[segment["id"]] = {
            "segment": {
                "id": segment["id"],
                "name": segment["name"],
                "opportunity_score": segment["opportunity"],
                "packaging_readiness_score": segment["packaging"],
                "confidence": segment["confidence"],
                "recommended_package_id": segment["recommendedProduct"],
                "pain": segment["pain"],
                "trend": segment["trend"],
                "action_mode": segment["actionMode"],
                "rationale": segment["rationale"],
            },
            "key_signals": segment["signals"],
            "comparison_rows": [
                {
                    "segment": item["name"],
                    "opportunity_score": item["opportunity"],
                    "packaging_readiness_score": item["packaging"],
                    "recommended_product": item["recommendedProduct"],
                }
                for item in segments
            ],
            "recommended_actions": [
                f"主推 {segment['recommendedProduct']}",
                f"围绕“{segment['pain']}”去讲价值主张",
                f"保留 {packages[1]['name'] if len(packages) > 1 else packages[0]['name']} 作为第二顺位产品",
            ],
            "evidence_highlights": matching_evidence,
        }

    return {
        "dashboard": dashboard,
        "segments": {
            "study": payload["study"],
            "segments": [
                {
                    "id": item["id"],
                    "name": item["name"],
                    "opportunity_score": item["opportunity"],
                    "packaging_readiness_score": item["packaging"],
                    "confidence": item["confidence"],
                    "recommended_package_id": item["recommendedProduct"],
                    "pain": item["pain"],
                    "trend": item["trend"],
                    "action_mode": item["actionMode"],
                }
                for item in segments
            ],
        },
        "segment_details": segment_details,
        "packages": {
            "study": payload["study"],
            "package_recommendations": packages,
            "packaging_comparisons": [
                {
                    "name": item["name"],
                    "target_segment": item["targetSegment"],
                    "entry_format": item["format"],
                    "message_angle": item["angle"],
                    "do_not_lead_with": item["avoid"],
                }
                for item in packages
            ],
        },
        "weekly_brief": {
            "study": payload["study"],
            "weekly_brief": weekly,
            "lead_segments": segments[:3],
            "lead_package": packages[0] if packages else None,
        },
        "study_template": DEFAULT_TEMPLATE,
    }


def suggest_focus_statement(form: dict[str, Any]) -> str:
    market = form.get("market", "目标市场")
    business_line = form.get("business_line", "目标业务线")
    goal = form.get("primary_goal", "选客群 + 定产品包装")
    return f"围绕 {market} 的 {business_line}，用公开需求信号支持“{goal}”判断。"


def normalize_text_list(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        candidates = re.split(r"[\n,，;；]+", values)
    elif isinstance(values, list):
        candidates = values
    else:
        return []

    normalized: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        text = str(item or "").strip()
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(text)
    return normalized


def draft_keyword_groups(form: dict[str, Any]) -> list[dict[str, Any]]:
    text = " ".join(
        str(form.get(key, "")) for key in ["business_line", "market", "problem_space", "target_customer"]
    ).lower()
    if "dropshipping" in text or "supplier" in text or "fulfillment" in text:
        return [
            {
                "id": "fulfillment",
                "label": "履约 / 3PL",
                "keywords": ["3PL", "fulfillment service", "fulfillment partner", "slow shipping", "shipping times"],
            },
            {
                "id": "supplier",
                "label": "Supplier / Sourcing",
                "keywords": ["private supplier", "sourcing agent", "China supplier", "supplier issues", "private agent"],
            },
            {
                "id": "risk",
                "label": "Risk / QC",
                "keywords": ["inspection", "quality issues", "wrong item", "fake supplier", "refunds"],
            },
            {
                "id": "cost",
                "label": "Cost / Margin",
                "keywords": ["margin", "profit margin", "landed cost", "shipping costs", "cost down"],
            },
        ]
    return [
        {
            "id": "discovery",
            "label": "Discovery",
            "keywords": ["supplier", "fulfillment", "shipping", "3PL", "inspection"],
        },
        {
            "id": "economics",
            "label": "Economics",
            "keywords": ["margin", "returns", "refunds", "cost down"],
        },
    ]


def estimate_crawl_cost(subreddits: list[str], keywords: list[str]) -> dict[str, Any]:
    query_count = len(subreddits) * len(keywords)
    if query_count >= 60:
        level = "high"
        note = "抓取查询量偏高，建议先分批验证关键词贡献。"
    elif query_count >= 24:
        level = "medium"
        note = "查询量适中，适合首轮验证后再决定是否扩词。"
    else:
        level = "low"
        note = "查询量较轻，适合快速首跑。"
    return {
        "subreddit_count": len(subreddits),
        "keyword_count": len(keywords),
        "query_count": query_count,
        "level": level,
        "note": note,
    }


def draft_keywords(form: dict[str, Any]) -> list[str]:
    manual_keywords = normalize_text_list(
        form.get("recommended_keywords") or form.get("keywords") or form.get("search_terms")
    )
    if manual_keywords:
        return manual_keywords
    text = " ".join(
        str(form.get(key, "")) for key in ["business_line", "market", "problem_space", "target_customer"]
    ).lower()
    if "dropshipping" in text:
        return [
            "3PL",
            "fulfillment service",
            "shipping delays",
            "private supplier",
            "sourcing agent",
            "China supplier",
            "refunds",
            "margin",
        ]
    if "shopify" in text:
        return [
            "shopify fulfillment",
            "3PL partner",
            "shipping costs",
            "private label supplier",
            "warehouse",
            "inventory",
            "returns",
            "conversion drop",
        ]
    return [
        "supplier",
        "fulfillment",
        "shipping",
        "quality issues",
        "cost down",
        "3PL",
        "sourcing partner",
        "inspection",
    ]


def draft_hypotheses(form: dict[str, Any]) -> list[dict[str, str]]:
    text = " ".join(
        str(form.get(key, "")) for key in ["business_line", "problem_space", "target_customer"]
    ).lower()
    if "dropshipping" in text:
        return [
            {
                "name": "Fulfillment 主线",
                "description": "已出单卖家最痛的是 shipping delays、3PL 混乱和履约切换问题。",
            },
            {
                "name": "Supplier 第二主线",
                "description": "private supplier / sourcing agent 需求稳定存在，但更适合作为第二产品。",
            },
            {
                "name": "Risk 作为支持型服务",
                "description": "风险与 QC 需求更多适合作为配套价值，而不是首页主入口。",
            },
        ]
    return [
        {
            "name": "供需匹配主线",
            "description": "优先验证用户是否在主动寻找供应端或履约端的新方案。",
        },
        {
            "name": "痛点聚焦主线",
            "description": "优先验证哪个问题最痛、最具体、最接近付费。",
        },
    ]


def build_study_draft(form: dict[str, Any]) -> dict[str, Any]:
    market = form.get("market", "美国")
    business_line = form.get("business_line", "Dropshipping 供应链服务")
    region = form.get("region", "美国")
    target_customer = form.get("target_customer", "已出单但履约混乱的卖家")
    primary_goal = form.get("primary_goal", "选客群 + 定产品包装")
    problem_space = form.get("problem_space", "履约与 supplier 问题")

    provided_subreddits = normalize_text_list(
        form.get("recommended_subreddits") or form.get("subreddits")
    )
    if provided_subreddits:
        recommended_subreddits = provided_subreddits
    elif "dropshipping" in f"{business_line} {target_customer} {problem_space}".lower():
        recommended_subreddits = ["dropship", "dropshipping", "ecommerce", "shopify"]
    else:
        recommended_subreddits = ["ecommerce", "shopify", "entrepreneur"]

    recommended_keywords = draft_keywords(form)
    keyword_groups = draft_keyword_groups(form)
    crawl_cost = estimate_crawl_cost(recommended_subreddits, recommended_keywords)

    return {
        "study": {
            "title": form.get("title") or f"{market} / {business_line} / {problem_space}",
            "market": market,
            "business_line": business_line,
            "region": region,
            "target_customer": target_customer,
            "primary_goal": primary_goal,
            "problem_space": problem_space,
            "time_window": form.get("time_window", "近 30 天"),
        },
        "focus_statement": suggest_focus_statement(form),
        "recommended_sources": DEFAULT_TEMPLATE["sources"],
        "recommended_subreddits": recommended_subreddits,
        "recommended_keywords": recommended_keywords,
        "recommended_keyword_groups": keyword_groups,
        "recommended_hypotheses": draft_hypotheses(form),
        "recommended_outputs": DEFAULT_TEMPLATE["recommended_outputs"],
        "suggested_first_run_mode": "browser",
        "suggested_schedule_mode": "adaptive",
        "suggested_schedule_enabled": False,
        "suggested_interval_hours": 24,
        "crawl_cost_estimate": crawl_cost,
        "decision_checks": [
            "哪个客群的痛感最强、表达最具体？",
            "哪个问题更容易包装成清晰 offer？",
            "当前应该主打 Fulfillment 还是 Supplier？",
            "本周周会上应该优先验证哪个主产品？",
        ],
    }


def safe_static_path(root: Path, request_path: str) -> Path | None:
    relative = request_path.lstrip("/") or "mvp-app.html"
    relative = unquote(relative)
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


class DemandIntelligenceHandler(BaseHTTPRequestHandler):
    api_bundle: dict = {}
    static_root: Path
    input_path: Path
    study_title: str
    market: str
    date_range: str
    allowed_origins: set[str] = set()
    cookie_secure: bool = False

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/"):
            self.handle_api(path)
            return

        self.handle_static(path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/"):
            self.handle_api_post(path)
            return
        self.send_text("Not Found", HTTPStatus.NOT_FOUND)

    def do_OPTIONS(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        if not path.startswith("/api/"):
            self.send_text("Not Found", HTTPStatus.NOT_FOUND)
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self.add_cors_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def current_user(self) -> dict[str, Any] | None:
        cookies = parse_cookie_header(self.headers.get("Cookie"))
        token = (
            self.headers.get("X-User-Token")
            or parse_bearer_token(self.headers.get("Authorization"))
            or cookies.get("demand_intel_token")
        )
        return find_user_by_token(token)

    def current_worker(self) -> dict[str, Any] | None:
        token = self.headers.get("X-Worker-Token") or parse_bearer_token(self.headers.get("Authorization"))
        return find_worker_by_token(token)

    def require_worker(self) -> dict[str, Any] | None:
        worker = self.current_worker()
        if worker:
            return worker
        self.send_json({"error": "worker_auth_required"}, status=401)
        return None

    def require_role(self, minimum_role: str) -> dict[str, Any] | None:
        user = self.current_user()
        if ensure_role(user, minimum_role):
            return user
        self.send_json(
            {
                "error": "forbidden",
                "required_role": minimum_role,
                "current_role": (user or {}).get("role", "anonymous"),
            },
            status=403,
        )
        return None

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def cors_origin(self) -> str | None:
        origin = self.headers.get("Origin")
        if not origin:
            return None
        if "*" in self.allowed_origins:
            return origin
        if origin in self.allowed_origins:
            return origin
        return None

    def add_cors_headers(self) -> None:
        origin = self.cors_origin()
        if not origin:
            return
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-User-Token, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Vary", "Origin")

    def send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.add_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json_with_cookie(
        self,
        payload: dict,
        cookie_value: str | None = None,
        status: int = 200,
        expire_cookie: bool = False,
    ) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.add_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if cookie_value is not None:
            cookie_parts = [f"demand_intel_token={cookie_value}", "Path=/"]
            if expire_cookie:
                cookie_parts.append("Max-Age=0")
            if self.cookie_secure:
                cookie_parts.extend(["SameSite=None", "Secure"])
            else:
                cookie_parts.append("SameSite=Lax")
            self.send_header("Set-Cookie", "; ".join(cookie_parts))
        self.end_headers()
        self.wfile.write(body)

    def send_text(self, message: str, status: int) -> None:
        body = message.encode("utf-8")
        self.send_response(status)
        if self.path.startswith("/api/"):
            self.add_cors_headers()
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def handle_api(self, path: str) -> None:
        if path == "/api/health":
            self.send_json(
                {
                    "ok": True,
                    "service": "demand-intelligence-api",
                    "server_root": str(SERVER_ROOT),
                    "runtime_mode": "hybrid_solution_a",
                    "time": now_iso(),
                }
            )
            return

        if path == "/api/worker/health":
            worker = self.require_worker()
            if worker is None:
                return
            record_worker_heartbeat(worker, event="health")
            running_job = running_remote_job_for_worker(worker.get("id", ""))
            self.send_json(
                {
                    "ok": True,
                    "worker": {
                        "id": worker.get("id"),
                        "name": worker.get("name", worker.get("id")),
                        "capabilities": sorted(worker_capabilities(worker)),
                    },
                    "running_job": enrich_job(running_job) if running_job else None,
                    "time": now_iso(),
                }
            )
            return

        if path.startswith("/api/worker/jobs/"):
            worker = self.require_worker()
            if worker is None:
                return
            job_id = path.split("/")[4] if len(path.split("/")) > 4 else ""
            job = load_job(job_id)
            if not job:
                self.send_json({"error": "job_not_found", "job_id": job_id}, status=404)
                return
            if job.get("claimed_by_worker_id") != worker.get("id"):
                self.send_json({"error": "job_claim_mismatch", "worker_id": worker.get("id")}, status=409)
                return
            self.send_json({"job": enrich_job(job)})
            return

        if path == "/api/auth/me":
            user = self.current_user()
            self.send_json({"user": sanitize_user(user)})
            return

        if path == "/api/runtime":
            user = self.require_role("viewer")
            if user is None:
                return
            self.send_json(hybrid_runtime_summary())
            return

        if path == "/api/study-template":
            self.send_json(self.api_bundle["study_template"])
            return

        if path == "/api/studies":
            studies = [summarize_record(record) for record in list_study_records()]
            active_study_id = studies[0]["id"] if studies else STUDY_ID
            self.send_json({"studies": studies, "active_study_id": active_study_id, "runtime": hybrid_runtime_summary()})
            return

        if path == "/api/jobs":
            user = self.require_role("viewer")
            if user is None:
                return
            self.send_json({"jobs": [enrich_job(job) for job in list_visible_jobs(limit=50)]})
            return

        if path.startswith("/api/jobs/"):
            user = self.require_role("viewer")
            if user is None:
                return
            job_id = path.split("/")[3] if len(path.split("/")) > 3 else ""
            job = load_job(job_id)
            if not job:
                self.send_json({"error": "job_not_found", "job_id": job_id}, status=404)
                return
            self.send_json({"job": enrich_job(job)})
            return

        base = "/api/studies/"
        if not path.startswith(base):
            self.send_json({"error": "route_not_found", "path": path}, status=404)
            return

        remainder = path[len(base) :]
        parts = [part for part in remainder.split("/") if part]
        if not parts:
            self.send_json({"error": "study_not_found"}, status=404)
            return

        study_id = parts[0]
        record = load_study_record(study_id)
        if not record:
            self.send_json({"error": "study_not_found", "study_id": study_id}, status=404)
            return

        bundle = build_api_bundle(record["payload"])
        entity_bundle = load_study_entity_bundle(study_id)
        suffix = "/" + "/".join(parts[1:]) if len(parts) > 1 else ""
        if suffix == "/dashboard":
            self.send_json(bundle["dashboard"])
            return
        if suffix == "/data-foundation":
            self.send_json(
                {
                    "study": summarize_record(record),
                    "manifest": entity_bundle.get("manifest", {}),
                    "artifacts": record.get("artifacts", {}),
                }
            )
            return
        if suffix == "/threads":
            self.send_json(
                {
                    "study": summarize_record(record),
                    "manifest": entity_bundle.get("manifest", {}),
                    "threads": entity_bundle.get("threads", []),
                }
            )
            return
        if suffix.startswith("/threads/"):
            thread_id = suffix.split("/")[-1]
            thread = next((item for item in entity_bundle.get("threads", []) if item.get("thread_id") == thread_id), None)
            if not thread:
                self.send_json({"error": "thread_not_found", "thread_id": thread_id}, status=404)
                return
            thread_snapshots = [item for item in entity_bundle.get("thread_snapshots", []) if item.get("thread_id") == thread_id]
            comments = [item for item in entity_bundle.get("comments", []) if item.get("thread_id") == thread_id]
            comment_ids = {item.get("comment_id") for item in comments}
            comment_snapshots = [item for item in entity_bundle.get("comment_snapshots", []) if item.get("comment_id") in comment_ids]
            signals = [item for item in entity_bundle.get("signals", []) if item.get("thread_id") == thread_id]
            self.send_json(
                {
                    "study": summarize_record(record),
                    "manifest": entity_bundle.get("manifest", {}),
                    "thread": thread,
                    "thread_snapshots": thread_snapshots,
                    "comments": comments[:100],
                    "comment_snapshots": comment_snapshots[:100],
                    "signals": signals,
                }
            )
            return
        if suffix == "/comments":
            self.send_json(
                {
                    "study": summarize_record(record),
                    "manifest": entity_bundle.get("manifest", {}),
                    "comments": entity_bundle.get("comments", [])[:200],
                }
            )
            return
        if suffix == "/signals":
            self.send_json(
                {
                    "study": summarize_record(record),
                    "manifest": entity_bundle.get("manifest", {}),
                    "signals": entity_bundle.get("signals", []),
                }
            )
            return
        if suffix == "/segments":
            self.send_json(bundle["segments"])
            return
        if suffix.startswith("/segments/"):
            segment_id = suffix.split("/")[-1]
            detail = bundle["segment_details"].get(segment_id)
            if not detail:
                self.send_json({"error": "segment_not_found", "segment_id": segment_id}, status=404)
                return
            self.send_json(detail)
            return
        if suffix == "/packages":
            self.send_json(bundle["packages"])
            return
        if suffix == "/weekly-brief":
            self.send_json(bundle["weekly_brief"])
            return
        if suffix == "/config":
            self.send_json(
                {
                    "study": summarize_record(record),
                    "source": record.get("source", {}),
                    "artifacts": record.get("artifacts", {}),
                    "draft": record.get("draft", {}),
                    "schedule": record.get("schedule", {}),
                    "data_foundation": record.get("data_foundation", {}),
                }
            )
            return
        if suffix == "/operations":
            self.send_json(
                {
                    "study": summarize_record(record),
                    "schedule": record.get("schedule", {}),
                    "jobs": [enrich_job(job) for job in list_visible_jobs(study_id=study_id, limit=50)],
                    "source": record.get("source", {}),
                    "artifacts": record.get("artifacts", {}),
                    "data_foundation": record.get("data_foundation", {}),
                }
            )
            return
        if suffix == "/jobs":
            self.send_json({"study": summarize_record(record), "jobs": [enrich_job(job) for job in list_visible_jobs(study_id=study_id, limit=50)]})
            return
        if suffix == "/schedule":
            self.send_json({"study": summarize_record(record), "schedule": record.get("schedule", {})})
            return
        if suffix == "/meta" or suffix == "":
            self.send_json({"study": summarize_record(record), "draft": record["draft"]})
            return
        self.send_json({"error": "route_not_found", "path": path}, status=404)

    def handle_api_post(self, path: str) -> None:
        if path == "/api/auth/login":
            length = int(self.headers.get("Content-Length", "0") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                self.send_json({"error": "invalid_json"}, status=400)
                return
            user = find_user_by_credentials(payload.get("email", ""), payload.get("password", ""))
            if not user:
                self.send_json({"error": "invalid_credentials"}, status=401)
                return
            self.send_json_with_cookie({"user": sanitize_user(user), "token": user.get("token")}, user.get("token"), status=200)
            return

        if path == "/api/auth/logout":
            self.send_json_with_cookie({"ok": True}, "", status=200, expire_cookie=True)
            return

        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self.send_json({"error": "invalid_json"}, status=400)
            return

        if path == "/api/worker/claim":
            worker = self.require_worker()
            if worker is None:
                return
            record_worker_heartbeat(worker, event="claim")
            try:
                job, task = claim_remote_job(worker)
            except Exception as error:  # noqa: BLE001
                self.send_json({"error": "worker_claim_failed", "detail": str(error)}, status=500)
                return
            self.send_json(
                {
                    "worker": {
                        "id": worker.get("id"),
                        "name": worker.get("name", worker.get("id")),
                        "capabilities": sorted(worker_capabilities(worker)),
                    },
                    "job": enrich_job(job) if job else None,
                    "task": task,
                }
            )
            return

        if path.startswith("/api/worker/jobs/") and path.endswith("/complete"):
            worker = self.require_worker()
            if worker is None:
                return
            record_worker_heartbeat(worker, event="complete")
            job_id = path.split("/")[4] if len(path.split("/")) > 4 else ""
            job = load_job(job_id)
            if not job:
                self.send_json({"error": "job_not_found", "job_id": job_id}, status=404)
                return
            if job.get("status") not in {"running", "canceling"}:
                self.send_json({"error": "job_not_running", "status": job.get("status")}, status=409)
                return
            if job.get("claimed_by_worker_id") != worker.get("id"):
                self.send_json({"error": "job_claim_mismatch", "worker_id": worker.get("id")}, status=409)
                return
            if job.get("status") == "canceling":
                job["status"] = "canceled"
                job["finished_at"] = now_iso()
                job["updated_at"] = now_iso()
                job["error"] = str(payload.get("error") or "canceled_by_user")
                job["result_summary"] = payload.get("summary") or {}
                save_job(job)
                self.send_json({"canceled": True, "job": enrich_job(job)})
                return
            try:
                apply_worker_stage_result(job, payload)
            except Exception as error:  # noqa: BLE001
                self.send_json({"error": "worker_result_failed", "detail": str(error)}, status=500)
                return
            job["status"] = "completed"
            job["finished_at"] = now_iso()
            job["updated_at"] = now_iso()
            job["result_summary"] = payload.get("summary") or {}
            save_job(job)
            follow_up = enqueue_follow_up_job(job)
            self.send_json({"completed": True, "job": enrich_job(job), "follow_up_job": enrich_job(follow_up) if follow_up else None})
            return

        if path.startswith("/api/worker/jobs/") and path.endswith("/fail"):
            worker = self.require_worker()
            if worker is None:
                return
            record_worker_heartbeat(worker, event="fail")
            job_id = path.split("/")[4] if len(path.split("/")) > 4 else ""
            job = load_job(job_id)
            if not job:
                self.send_json({"error": "job_not_found", "job_id": job_id}, status=404)
                return
            if job.get("status") not in {"running", "canceling"}:
                self.send_json({"error": "job_not_running", "status": job.get("status")}, status=409)
                return
            if job.get("claimed_by_worker_id") != worker.get("id"):
                self.send_json({"error": "job_claim_mismatch", "worker_id": worker.get("id")}, status=409)
                return
            canceled = bool(payload.get("canceled")) or job.get("status") == "canceling"
            job["status"] = "canceled" if canceled else "failed"
            job["finished_at"] = now_iso()
            job["updated_at"] = now_iso()
            job["error"] = str(payload.get("error") or ("canceled_by_user" if canceled else "remote_worker_failed"))
            job["failure_context"] = payload.get("context") or {}
            save_job(job)
            self.send_json({"canceled": canceled, "failed": not canceled, "job": enrich_job(job)})
            return

        if path.startswith("/api/jobs/") and path.endswith("/retry"):
            user = self.require_role("analyst")
            if user is None:
                return
            job_id = path.split("/")[3] if len(path.split("/")) > 3 else ""
            job = load_job(job_id)
            if not job:
                self.send_json({"error": "job_not_found", "job_id": job_id}, status=404)
                return
            mode = job.get("requested_mode") or job.get("resolved_mode") or job.get("mode", "seeded")
            if mode_requires_admin(mode) and not ensure_role(user, "admin"):
                self.send_json({"error": "forbidden", "required_role": "admin", "current_role": user.get("role")}, status=403)
                return
            retried = enqueue_job(job.get("study_id", ""), mode, actor=user, trigger=f"retry:{job_id}")
            self.send_json({"queued": True, "job": retried}, status=202)
            return

        if path.startswith("/api/jobs/") and path.endswith("/cancel"):
            user = self.require_role("analyst")
            if user is None:
                return
            job_id = path.split("/")[3] if len(path.split("/")) > 3 else ""
            job = load_job(job_id)
            if not job:
                self.send_json({"error": "job_not_found", "job_id": job_id}, status=404)
                return
            if job.get("status") not in ACTIVE_JOB_STATUSES:
                self.send_json({"error": "job_not_cancelable", "status": job.get("status")}, status=409)
                return
            updated = request_job_cancellation(job, actor=user)
            self.send_json({"canceled": True, "job": enrich_job(updated)})
            return

        if path not in {"/api/studies/draft", "/api/studies"} and not path.startswith("/api/studies/"):
            self.send_json({"error": "route_not_found", "path": path}, status=404)
            return

        if path == "/api/studies/draft":
            user = self.require_role("analyst")
            if user is None:
                return
            draft = build_study_draft(payload)
            self.send_json(draft)
            return

        if path.startswith("/api/studies/") and path.endswith("/rebuild"):
            user = self.require_role("analyst")
            if user is None:
                return
            study_id = path.split("/")[3]
            record = load_study_record(study_id)
            if not record:
                self.send_json({"error": "study_not_found", "study_id": study_id}, status=404)
                return
            if has_active_job(study_id):
                self.send_json({"error": "job_already_active", "study_id": study_id}, status=409)
                return
            mode = payload.get("mode", "adaptive")
            if mode not in ALL_JOB_MODES:
                self.send_json({"error": "invalid_mode", "mode": mode}, status=400)
                return
            if mode in BROWSER_JOB_MODES and not has_available_remote_worker("discover"):
                self.send_json({"error": "remote_worker_unavailable", "mode": mode}, status=409)
                return
            if mode_requires_admin(mode) and not ensure_role(user, "admin"):
                self.send_json({"error": "forbidden", "required_role": "admin", "current_role": user.get("role")}, status=403)
                return
            job = enqueue_job(study_id, mode, actor=user, trigger="manual")
            self.send_json(
                {
                    "queued": True,
                    "job": job,
                },
                status=202,
            )
            return

        if path.startswith("/api/studies/") and path.endswith("/stop"):
            user = self.require_role("analyst")
            if user is None:
                return
            study_id = path.split("/")[3]
            record = load_study_record(study_id)
            if not record:
                self.send_json({"error": "study_not_found", "study_id": study_id}, status=404)
                return
            canceled_jobs = cancel_active_jobs_for_study(study_id, actor=user)
            self.send_json(
                {
                    "stopped": True,
                    "study": summarize_record(record),
                    "canceled_jobs": canceled_jobs,
                    "canceled_count": len(canceled_jobs),
                }
            )
            return

        if path.startswith("/api/studies/") and path.endswith("/schedule"):
            user = self.require_role("admin")
            if user is None:
                return
            study_id = path.split("/")[3]
            record = load_study_record(study_id)
            if not record:
                self.send_json({"error": "study_not_found", "study_id": study_id}, status=404)
                return
            interval = max(int(payload.get("interval_hours", 24) or 24), 1)
            enabled = bool(payload.get("enabled", False))
            requested_mode = payload.get("mode", "adaptive")
            mode = requested_mode
            if mode not in ALL_JOB_MODES:
                self.send_json({"error": "invalid_mode", "mode": mode}, status=400)
                return
            normalization = None
            if enabled and mode == "seeded" and has_available_remote_worker("discover"):
                mode = "adaptive"
                normalization = {
                    "from": "seeded",
                    "to": "adaptive",
                    "reason": "你已主动启用自动调度，系统改用 adaptive 以兼容已连接的 Mac Worker。",
                }
            if enabled and mode in BROWSER_JOB_MODES and not has_available_remote_worker("discover"):
                self.send_json({"error": "remote_worker_unavailable", "mode": mode}, status=409)
                return
            if mode_requires_admin(mode) and not ensure_role(user, "admin"):
                self.send_json({"error": "forbidden", "required_role": "admin", "current_role": user.get("role")}, status=403)
                return
            start_now = bool(payload.get("start_now", False))
            next_run = now_iso() if enabled and start_now else (
                (datetime.now() + timedelta(hours=interval)).isoformat(timespec="seconds") if enabled else None
            )
            record["schedule"] = {
                "enabled": enabled,
                "mode": mode,
                "interval_hours": interval,
                "last_run_at": record.get("schedule", {}).get("last_run_at"),
                "next_run_at": next_run,
            }
            save_study_record(record)
            queued_job = None
            if enabled and start_now and not has_active_job(study_id):
                queued_job = enqueue_job(study_id, mode, actor=user, trigger="schedule")
            self.send_json(
                {
                    "study": summarize_record(record),
                    "schedule": record["schedule"],
                    "queued_job": queued_job,
                    "normalization": normalization,
                    "requested_mode": requested_mode,
                }
            )
            return

        user = self.require_role("analyst")
        if user is None:
            return
        draft = build_study_draft(payload)
        title = draft["study"]["title"]
        study_id = slugify(title)
        existing = load_study_record(study_id)
        counter = 2
        while existing:
            study_id = f"{slugify(title)}-{counter}"
            existing = load_study_record(study_id)
            counter += 1

        record = build_study_record(
            study_id,
            draft["study"],
            draft,
            {},
            status="seeded_demo_data",
        )
        record = materialize_record(record, self.input_path)
        record["payload"]["summary"]["explanation"] += " 当前为新建 study 的初始版本，后续可绑定专属数据源继续细化。"

        auto_run = payload.get("auto_run") or {}
        queued_job = None
        if auto_run:
            initial_mode = auto_run.get("initial_mode", draft.get("suggested_first_run_mode", "browser"))
            schedule_mode = auto_run.get("schedule_mode", draft.get("suggested_schedule_mode", "adaptive"))
            interval_hours = max(int(auto_run.get("interval_hours", draft.get("suggested_interval_hours", 24)) or 24), 1)
            enable_schedule = bool(auto_run.get("enabled", draft.get("suggested_schedule_enabled", False)))

            if initial_mode not in ALL_JOB_MODES:
                self.send_json({"error": "invalid_mode", "mode": initial_mode}, status=400)
                return
            if schedule_mode not in ALL_JOB_MODES:
                self.send_json({"error": "invalid_mode", "mode": schedule_mode}, status=400)
                return
            if initial_mode in BROWSER_JOB_MODES and not has_available_remote_worker("discover"):
                self.send_json({"error": "remote_worker_unavailable", "mode": initial_mode}, status=409)
                return
            if enable_schedule and schedule_mode == "seeded" and has_available_remote_worker("discover"):
                schedule_mode = "adaptive"
            if enable_schedule and schedule_mode in BROWSER_JOB_MODES and not has_available_remote_worker("discover"):
                self.send_json({"error": "remote_worker_unavailable", "mode": schedule_mode}, status=409)
                return
            if mode_requires_admin(initial_mode) or mode_requires_admin(schedule_mode):
                if not ensure_role(user, "admin"):
                    self.send_json({"error": "forbidden", "required_role": "admin", "current_role": user.get("role")}, status=403)
                    return

            record["schedule"] = {
                "enabled": enable_schedule,
                "mode": schedule_mode,
                "interval_hours": interval_hours,
                "last_run_at": None,
                "next_run_at": (datetime.now() + timedelta(hours=interval_hours)).isoformat(timespec="seconds")
                if enable_schedule
                else None,
            }

        attach_study_runtime(record, self.input_path)
        save_study_record(record)
        if auto_run:
            queued_job = enqueue_job(study_id, initial_mode, actor=user, trigger="create_and_run")
        self.send_json(
            {
                "study": summarize_record(record),
                "draft": draft,
                "payload": record["payload"],
                "artifacts": record.get("artifacts", {}),
                "source": record.get("source", {}),
                "data_foundation": record.get("data_foundation", {}),
                "queued_job": queued_job,
            },
            status=201,
        )

    def handle_static(self, path: str) -> None:
        if path in ("/", ""):
            target = self.static_root / "mvp-app.html"
        else:
            target = safe_static_path(self.static_root, path)
            if target is None:
                self.send_text("Forbidden", HTTPStatus.FORBIDDEN)
                return

        if not target.exists() or not target.is_file():
            self.send_text("Not Found", HTTPStatus.NOT_FOUND)
            return

        mime, _ = mimetypes.guess_type(str(target))
        mime = mime or "application/octet-stream"
        body = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{mime}; charset=utf-8" if mime.startswith("text/") or mime in {"application/javascript", "application/json"} else mime)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input dataset not found: {input_path}")

    root = (Path(__file__).resolve().parent.parent / "docs" / "product").resolve()
    ensure_support_dirs()
    ensure_seed_study(input_path, args.study_title, args.market, args.date_range)
    payload = build_dataset(input_path, args.study_title, args.market, args.date_range)
    DemandIntelligenceHandler.api_bundle = build_api_bundle(payload)
    DemandIntelligenceHandler.static_root = root
    DemandIntelligenceHandler.input_path = input_path
    DemandIntelligenceHandler.study_title = args.study_title
    DemandIntelligenceHandler.market = args.market
    DemandIntelligenceHandler.date_range = args.date_range
    DemandIntelligenceHandler.allowed_origins = parse_allowed_origins(args.cors_origins)
    DemandIntelligenceHandler.cookie_secure = args.cookie_secure

    stop_event = threading.Event()
    worker = threading.Thread(target=worker_loop, args=(stop_event,), daemon=True)
    scheduler = threading.Thread(target=scheduler_loop, args=(stop_event,), daemon=True)
    worker.start()
    scheduler.start()

    httpd = ThreadingHTTPServer((args.host, args.port), DemandIntelligenceHandler)
    print(f"Demand Intelligence MVP running at http://{args.host}:{args.port}")
    print(f"Study ID: {STUDY_ID}")
    print(f"Serving static files from: {root}")
    if DemandIntelligenceHandler.allowed_origins:
        print(f"CORS enabled for: {', '.join(sorted(DemandIntelligenceHandler.allowed_origins))}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        stop_event.set()
        httpd.server_close()


if __name__ == "__main__":
    main()

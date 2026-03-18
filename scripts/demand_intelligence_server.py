#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import mimetypes
import re
import subprocess
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
JOBS_DIR = SERVER_ROOT / "data" / "jobs"
USERS_FILE = SERVER_ROOT / "config" / "users.json"
DEFAULT_INPUT = Path("/Users/perrilee/raddit/data/raw/fishgoo_dropshipping_expanded.jsonl")
ROLE_ORDER = {"viewer": 1, "analyst": 2, "admin": 3}


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
    return parser.parse_args()


def build_dataset(input_path: Path, study_title: str, market: str, date_range: str) -> dict:
    records = read_jsonl(input_path)
    return build_payload(records, study_title, market, date_range)


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


def job_file(job_id: str) -> Path:
    return JOBS_DIR / f"{job_id}.json"


def summarize_record(record: dict[str, Any]) -> dict[str, Any]:
    payload = record["payload"]
    jobs = list_jobs_for_study(record["id"])
    active_job_count = sum(1 for job in jobs if job.get("status") in {"queued", "running"})
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
    }


def save_study_record(record: dict[str, Any]) -> None:
    STUDIES_DIR.mkdir(parents=True, exist_ok=True)
    study_file(record["id"]).write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def maybe_upgrade_record(record: dict[str, Any]) -> dict[str, Any]:
    if "schedule" not in record:
        record["schedule"] = {
            "enabled": False,
            "mode": "seeded",
            "interval_hours": 24,
            "last_run_at": None,
            "next_run_at": None,
        }
    artifacts = record.get("artifacts", {})
    source = record.get("source", {})
    if artifacts.get("config_path") and artifacts.get("payload_json_path") and source.get("input_path"):
        return record

    input_path = Path(source.get("input_path") or str(DEFAULT_INPUT))
    if not input_path.exists():
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
        "schedule": {
            "enabled": False,
            "mode": "seeded",
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
    }


def ensure_support_dirs() -> None:
    for path in [STUDIES_DIR, STUDY_CONFIG_DIR, STUDY_PRODUCT_DATA_DIR, STUDY_RAW_DIR, STUDY_REPORT_DIR, JOBS_DIR]:
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
    enriched["study_title"] = (record or {}).get("study", {}).get("title", job.get("study_id", ""))
    enriched["study_market"] = (record or {}).get("study", {}).get("market", "")
    enriched["schedule_enabled"] = (record or {}).get("schedule", {}).get("enabled", False)
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


def list_jobs_for_study(study_id: str) -> list[dict[str, Any]]:
    return [job for job in list_jobs() if job.get("study_id") == study_id]


def enqueue_job(study_id: str, mode: str, actor: dict[str, Any] | None, trigger: str = "manual") -> dict[str, Any]:
    job = {
        "id": f"job-{uuid.uuid4().hex[:10]}",
        "study_id": study_id,
        "mode": mode,
        "trigger": trigger,
        "status": "queued",
        "actor_id": (actor or {}).get("id", "system"),
        "actor_role": (actor or {}).get("role", "system"),
        "created_at": now_iso(),
        "started_at": None,
        "finished_at": None,
        "error": None,
    }
    save_job(job)
    return job


def has_active_job(study_id: str) -> bool:
    return any(job.get("status") in {"queued", "running"} and job.get("study_id") == study_id for job in list_jobs_for_study(study_id))


def attach_study_runtime(record: dict[str, Any], input_path: Path) -> dict[str, Any]:
    config = build_reddit_config(record["draft"])
    config_path = write_study_config(record["id"], config)
    payload_json, payload_js = write_study_payload_files(record["id"], record["payload"])
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
        "raw_output_path": str(study_raw_file(record["id"])),
        "report_output_path": str(study_report_file(record["id"])),
    }
    record["updated_at"] = now_iso()
    return record


def materialize_record(record: dict[str, Any], input_path: Path) -> dict[str, Any]:
    payload = build_dataset(
        input_path,
        record["study"]["title"],
        record["study"]["market"],
        record["study"].get("time_window", "近 30 天"),
    )
    record["payload"] = payload
    return attach_study_runtime(record, input_path)


def run_browser_rebuild(record: dict[str, Any]) -> Path:
    config_path = record.get("source", {}).get("browser_config_path") or record.get("artifacts", {}).get("config_path")
    raw_output_path = record.get("artifacts", {}).get("raw_output_path")
    report_output_path = record.get("artifacts", {}).get("report_output_path")
    if not config_path or not raw_output_path or not report_output_path:
        raise RuntimeError("Study is missing browser config or artifact paths.")

    command = [
        "python3",
        "scripts/reddit_browser_pipeline.py",
        "--config",
        config_path,
        "--raw-output",
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
    if job.get("mode") == "browser":
        input_path = run_browser_rebuild(record)
        record.setdefault("source", {})["type"] = "browser_reddit"
        record["source"]["input_path"] = str(input_path)

    record = materialize_record(record, input_path)
    record["schedule"]["last_run_at"] = now_iso()
    if record["schedule"].get("enabled"):
        interval = int(record["schedule"].get("interval_hours", 24) or 24)
        record["schedule"]["next_run_at"] = (datetime.now() + timedelta(hours=interval)).isoformat(timespec="seconds")
    save_study_record(record)
    return record


def worker_loop(stop_event: threading.Event) -> None:
    while not stop_event.is_set():
        queued = [job for job in list_jobs() if job.get("status") == "queued"]
        if not queued:
            time.sleep(1.0)
            continue

        job = queued[0]
        job["status"] = "running"
        job["started_at"] = now_iso()
        save_job(job)

        try:
            process_job(job)
            job["status"] = "completed"
            job["finished_at"] = now_iso()
        except Exception as error:  # noqa: BLE001
            job["status"] = "failed"
            job["finished_at"] = now_iso()
            job["error"] = str(error)
        save_job(job)


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
                enqueue_job(record["id"], schedule.get("mode", "seeded"), actor=None, trigger="schedule")
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


def draft_keywords(form: dict[str, Any]) -> list[str]:
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

    if "dropshipping" in f"{business_line} {target_customer} {problem_space}".lower():
        recommended_subreddits = ["dropship", "dropshipping", "ecommerce", "shopify"]
    else:
        recommended_subreddits = ["ecommerce", "shopify", "entrepreneur"]

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
        "recommended_keywords": draft_keywords(form),
        "recommended_hypotheses": draft_hypotheses(form),
        "recommended_outputs": DEFAULT_TEMPLATE["recommended_outputs"],
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

    def current_user(self) -> dict[str, Any] | None:
        cookies = parse_cookie_header(self.headers.get("Cookie"))
        token = self.headers.get("X-User-Token") or cookies.get("demand_intel_token")
        return find_user_by_token(token)

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

    def send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json_with_cookie(self, payload: dict, cookie_value: str | None = None, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if cookie_value is not None:
            self.send_header("Set-Cookie", f"demand_intel_token={cookie_value}; Path=/; SameSite=Lax")
        self.end_headers()
        self.wfile.write(body)

    def send_text(self, message: str, status: int) -> None:
        body = message.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def handle_api(self, path: str) -> None:
        if path == "/api/auth/me":
            user = self.current_user()
            self.send_json({"user": sanitize_user(user)})
            return

        if path == "/api/study-template":
            self.send_json(self.api_bundle["study_template"])
            return

        if path == "/api/studies":
            studies = [summarize_record(record) for record in list_study_records()]
            active_study_id = studies[0]["id"] if studies else STUDY_ID
            self.send_json({"studies": studies, "active_study_id": active_study_id})
            return

        if path == "/api/jobs":
            user = self.require_role("viewer")
            if user is None:
                return
            self.send_json({"jobs": [enrich_job(job) for job in list_jobs()[:50]]})
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
        suffix = "/" + "/".join(parts[1:]) if len(parts) > 1 else ""
        if suffix == "/dashboard":
            self.send_json(bundle["dashboard"])
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
                }
            )
            return
        if suffix == "/operations":
            self.send_json(
                {
                    "study": summarize_record(record),
                    "schedule": record.get("schedule", {}),
                    "jobs": [enrich_job(job) for job in list_jobs_for_study(study_id)[:50]],
                    "source": record.get("source", {}),
                    "artifacts": record.get("artifacts", {}),
                }
            )
            return
        if suffix == "/jobs":
            self.send_json({"study": summarize_record(record), "jobs": [enrich_job(job) for job in list_jobs_for_study(study_id)[:50]]})
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
            self.send_json_with_cookie({"user": sanitize_user(user)}, user.get("token"), status=200)
            return

        if path == "/api/auth/logout":
            self.send_json_with_cookie({"ok": True}, "", status=200)
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
            mode = job.get("mode", "seeded")
            if mode == "browser" and not ensure_role(user, "admin"):
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
            if job.get("status") != "queued":
                self.send_json({"error": "job_not_cancelable", "status": job.get("status")}, status=409)
                return
            job["status"] = "canceled"
            job["finished_at"] = now_iso()
            save_job(job)
            self.send_json({"canceled": True, "job": enrich_job(job)})
            return

        if path not in {"/api/studies/draft", "/api/studies"} and not path.startswith("/api/studies/"):
            self.send_json({"error": "route_not_found", "path": path}, status=404)
            return

        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self.send_json({"error": "invalid_json"}, status=400)
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
            mode = payload.get("mode", "seeded")
            if mode == "browser" and not ensure_role(user, "admin"):
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
            mode = payload.get("mode", "seeded")
            if mode not in {"seeded", "browser"}:
                self.send_json({"error": "invalid_mode", "mode": mode}, status=400)
                return
            if mode == "browser" and not ensure_role(user, "admin"):
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
            self.send_json({"study": summarize_record(record), "schedule": record["schedule"], "queued_job": queued_job})
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
        attach_study_runtime(record, self.input_path)
        save_study_record(record)
        self.send_json(
            {
                "study": summarize_record(record),
                "draft": draft,
                "payload": record["payload"],
                "artifacts": record.get("artifacts", {}),
                "source": record.get("source", {}),
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

    stop_event = threading.Event()
    worker = threading.Thread(target=worker_loop, args=(stop_event,), daemon=True)
    scheduler = threading.Thread(target=scheduler_loop, args=(stop_event,), daemon=True)
    worker.start()
    scheduler.start()

    httpd = ThreadingHTTPServer((args.host, args.port), DemandIntelligenceHandler)
    print(f"Demand Intelligence MVP running at http://{args.host}:{args.port}")
    print(f"Study ID: {STUDY_ID}")
    print(f"Serving static files from: {root}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        stop_event.set()
        httpd.server_close()


if __name__ == "__main__":
    main()

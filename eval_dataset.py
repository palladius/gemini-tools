"""
Dataset Management Utility for Closed-Loop Character Consistency Evaluation
-------------------------------------------------------------------------
Manages reading, writing, querying, and aggregating per-subject evaluation JSONL files
(`out/evals/<subject_slug>/evaluations.jsonl`) and the global `master_index.jsonl`.
"""

import os
import json
import time
from pathlib import Path
from slugify import slugify

BASE_EVAL_DIR = Path("out/evals")

def get_subject_eval_dir(subject: str) -> Path:
    subject_slug = slugify(subject)
    d = BASE_EVAL_DIR / subject_slug
    d.mkdir(parents=True, exist_ok=True)
    return d

def get_subject_jsonl_path(subject: str) -> Path:
    return get_subject_eval_dir(subject) / "evaluations.jsonl"

def get_master_index_path() -> Path:
    BASE_EVAL_DIR.mkdir(parents=True, exist_ok=True)
    return BASE_EVAL_DIR / "master_index.jsonl"

def load_subject_evaluations(subject: str) -> list[dict]:
    jsonl_path = get_subject_jsonl_path(subject)
    if not jsonl_path.exists():
        return []
    records = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records

def save_subject_evaluations(subject: str, records: list[dict]):
    jsonl_path = get_subject_jsonl_path(subject)
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    update_master_index()

def upsert_evaluation_record(record: dict) -> dict:
    subject = record.get("subject", "general")
    eval_id = record.get("eval_id")
    if not eval_id:
        model_slug = slugify(record.get("model_name", "unknown"))
        timestamp_str = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
        eval_id = f"{slugify(subject)}_{model_slug}_{timestamp_str}"
        record["eval_id"] = eval_id

    records = load_subject_evaluations(subject)
    updated = False
    for i, r in enumerate(records):
        if r.get("eval_id") == eval_id:
            records[i] = record
            updated = True
            break
            
    if not updated:
        records.append(record)
        
    save_subject_evaluations(subject, records)
    return record

def get_pending_evaluations(subject: str = None) -> list[dict]:
    pending = []
    if subject:
        subjects = [subject]
    else:
        if not BASE_EVAL_DIR.exists():
            return []
        subjects = [d.name for d in BASE_EVAL_DIR.iterdir() if d.is_dir()]
        
    for sub in subjects:
        records = load_subject_evaluations(sub)
        for r in records:
            human_eval = r.get("human_eval")
            if not human_eval or human_eval.get("score") is None:
                pending.append(r)
    return pending

def record_human_vote(eval_id: str, score: float, critique: str = "") -> dict | None:
    if not BASE_EVAL_DIR.exists():
        return None
    score_float = round(float(score), 1)
    subjects = [d.name for d in BASE_EVAL_DIR.iterdir() if d.is_dir()]
    for sub in subjects:
        records = load_subject_evaluations(sub)
        for i, r in enumerate(records):
            if r.get("eval_id") == eval_id:
                r["human_eval"] = {
                    "score": score_float,
                    "critique": critique,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }
                r["status"] = "COMPLETED"
                save_subject_evaluations(sub, records)
                return r
    return None

def update_master_index():
    if not BASE_EVAL_DIR.exists():
        return
    master_records = []
    for d in BASE_EVAL_DIR.iterdir():
        if d.is_dir():
            jsonl_file = d / "evaluations.jsonl"
            if jsonl_file.exists():
                with open(jsonl_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                master_records.append(json.loads(line))
                            except json.JSONDecodeError:
                                pass
                                
    master_path = get_master_index_path()
    with open(master_path, "w", encoding="utf-8") as f:
        for r in master_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

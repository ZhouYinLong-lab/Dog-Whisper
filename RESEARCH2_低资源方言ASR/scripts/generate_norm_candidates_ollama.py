"""Generate review-only normalization suggestions with a local Ollama model.

This script deliberately writes a separate candidate file. It never changes
norm_text or norm_status in the formal annotation file and therefore cannot
silently turn model suggestions into training labels.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


PROMPT_VERSION = "sichuan-norm-candidate-v2-zh-only"
SYSTEM_PROMPT = (
    "你只能输出简体中文。你是四川话文本到普通话规范书面语的候选生成器。"
    "绝对不要输出英文。"
)
DEFAULT_PROMPT = (
    "只返回一个JSON对象，不要解释，不要使用Markdown。"
    "字段norm_text必须是简体中文普通话规范书面表达。保留原意、信息、数字、专名和句子边界；"
    "只把四川话词汇、语气词和口语形式改为自然、可读的普通话书面表达；"
    "不要把四川话音译，不要增加输入中没有的信息。"
    "示例：输入“没得烤箱的伙伴”，输出{\"norm_text\":\"没有烤箱的朋友\"}。"
    "输入“诶呀好巴适”，输出{\"norm_text\":\"哎呀，真舒服\"}。"
)


def call_ollama(url: str, model: str, dialect_text: str, timeout: int) -> tuple[str, str, str]:
    prompt = f"{DEFAULT_PROMPT}\n现在处理：输入“{dialect_text}”"
    payload = {
        "model": model,
        "system": SYSTEM_PROMPT,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0, "num_predict": 120},
    }
    request = urllib.request.Request(
        url.rstrip("/") + "/api/generate",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
        raw = str(body.get("response", ""))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        return "", "request_error", str(exc)

    try:
        parsed = json.loads(raw)
        candidate = parsed.get("norm_text", "")
        if not isinstance(candidate, str) or not candidate.strip():
            return raw, "invalid_json_or_blank", "norm_text is missing or blank"
        return candidate.strip(), "ok", ""
    except json.JSONDecodeError as exc:
        return raw, "invalid_json_or_blank", str(exc)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    parser.add_argument("--model", default="minicpm5-2b-local:latest")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--timeout", type=int, default=90)
    args = parser.parse_args()

    if args.offset < 0:
        parser.error("--offset must be non-negative")
    if args.limit <= 0:
        parser.error("--limit must be positive")
    if not args.input.is_file():
        parser.error(f"input not found: {args.input}")

    rows = []
    with args.input.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"invalid JSON at line {line_number}: {exc}", file=sys.stderr)
                return 2
            if line_number <= args.offset:
                continue
            rows.append(row)
            if len(rows) >= args.limit:
                break

    args.output.parent.mkdir(parents=True, exist_ok=True)
    summary = {"rows": 0, "ok": 0, "errors": 0, "model": args.model}
    with args.output.open("w", encoding="utf-8") as handle:
        for row in rows:
            dialect_text = str(row.get("dialect_text", "")).strip()
            candidate, status, error = call_ollama(
                args.ollama_url, args.model, dialect_text, args.timeout
            )
            result = dict(row)
            result.update(
                {
                    "norm_text_candidate": candidate if status == "ok" else "",
                    "candidate_status": "model_suggested" if status == "ok" else status,
                    "candidate_error": error,
                    "candidate_model": args.model,
                    "candidate_prompt_version": PROMPT_VERSION,
                    "human_norm_text": "",
                    "human_review_status": "unreviewed",
                }
            )
            handle.write(json.dumps(result, ensure_ascii=False) + "\n")
            summary["rows"] += 1
            summary["ok" if status == "ok" else "errors"] += 1

    summary_path = args.output.with_suffix(args.output.suffix + ".summary.json")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if summary["errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Static audit for qiaomu-learning self-contained HTML artifacts.

This is deliberately conservative and dependency-free. It checks the promises
that can be verified from source text; it does not replace desktop/mobile
rendering or a human learning-experience review.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


EXTERNAL_URL_RE = re.compile(r"(?:src|href)\s*=\s*[\"']https?://", re.IGNORECASE)
SCRIPT_SRC_RE = re.compile(r"<script\b[^>]*\bsrc\s*=", re.IGNORECASE)
VIEWPORT_RE = re.compile(r'<meta\b[^>]*name\s*=\s*["\']viewport["\']', re.IGNORECASE)
QUESTION_RE = re.compile(r"[?？]")


def audit_html(text: str) -> list[str]:
    errors: list[str] = []
    lowered = text.casefold()

    if "<!doctype html>" not in lowered:
        errors.append("missing <!doctype html>")
    if not re.search(r"<html\b", lowered):
        errors.append("missing <html> root")
    if not re.search(r"<title\b[^>]*>.*?</title>", text, re.IGNORECASE | re.DOTALL):
        errors.append("missing non-empty <title>")
    if not VIEWPORT_RE.search(text):
        errors.append("missing responsive viewport meta")
    if EXTERNAL_URL_RE.search(text) or SCRIPT_SRC_RE.search(text):
        errors.append("external runtime or remote asset reference found")
    if re.search(r"<iframe\b|<object\b|<embed\b", text, re.IGNORECASE):
        errors.append("embedded external content is not self-contained")

    uses_storage = "localstorage" in lowered or "sessionstorage" in lowered
    if uses_storage:
        privacy_markers = ("只保存在本机", "local-only", "stored locally", "本机保存")
        clear_markers = ("clear", "清除", "删除进度", "reset progress")
        if not any(marker in lowered for marker in privacy_markers):
            errors.append("storage usage lacks a local-only privacy disclosure")
        if not any(marker.casefold() in lowered for marker in clear_markers):
            errors.append("storage usage lacks a clear-data action")

    if not QUESTION_RE.search(text):
        errors.append("interactive learning page has no learner-facing question")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", type=Path, help="HTML artifact to audit")
    parser.add_argument("--json", action="store_true", help="emit a machine-readable result")
    args = parser.parse_args(argv)

    try:
        text = args.html.read_text(encoding="utf-8")
    except OSError as exc:
        result = {"ok": False, "errors": [f"cannot read HTML: {exc}"]}
    else:
        errors = audit_html(text)
        result = {"ok": not errors, "errors": errors, "checks": "static only"}

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result["ok"]:
        print("PASS self-contained webpage static audit")
    else:
        print("FAIL self-contained webpage static audit", file=sys.stderr)
        for error in result["errors"]:
            print(f"  - {error}", file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

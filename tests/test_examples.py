"""예시 시뮬레이션 파일(frontend/public/examples) 무결성 테스트 (네트워크 없음)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from app.parsing.requirements import parse

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "frontend" / "public" / "examples"


def test_examples_index_files_parse_and_counts_match():
    index_path = EXAMPLES_DIR / "index.json"
    assert index_path.exists()
    entries = json.loads(index_path.read_text(encoding="utf-8"))
    assert len(entries) == 4

    by_id = {e["id"]: e for e in entries}
    assert {"old-ubuntu", "macos-local", "windows-dev", "large-freeze"} <= set(by_id)

    for entry in entries:
        file_path = EXAMPLES_DIR / entry["file"]
        assert file_path.exists(), f"missing example file: {entry['file']}"
        parsed = parse(file_path.read_text(encoding="utf-8"))
        assert len(parsed.packages) == entry["package_count"], entry["id"]
        assert len(parsed.excluded) == entry["excluded_count"], entry["id"]

    # 오래된 우분투 예시는 조회 제외 줄(-e) 1개
    old_ubuntu_parsed = parse((EXAMPLES_DIR / by_id["old-ubuntu"]["file"]).read_text(encoding="utf-8"))
    assert len(old_ubuntu_parsed.excluded) == 1
    assert "오래 걸림" in by_id["large-freeze"]["description"]


def test_examples_condition_templates_have_required_fields():
    entries = json.loads((EXAMPLES_DIR / "index.json").read_text(encoding="utf-8"))
    for entry in entries:
        tpl = entry["condition_template"]
        assert "{date}" in tpl, entry["id"]
        rendered = tpl.replace("{date}", "11/25")
        assert re.search(r"(Ubuntu\s+\d+\.\d+|macOS\s+\d+|Windows\s+11\s+\d+H\d+)", rendered), entry["id"]
        assert re.search(r"Python\s+\d+\.\d+", rendered), entry["id"]
        assert re.search(r"한 번에\s+\d+개", rendered), entry["id"]
        assert re.search(r"(매주|격주|매달|\d+일)", rendered), entry["id"]
        assert re.search(r"\d{1,2}/\d{1,2}", rendered), entry["id"]

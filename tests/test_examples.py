"""예시 시뮬레이션 10종(frontend/public/examples) 무결성 테스트 (네트워크 없음)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from app.parsing.requirements import (
    REASON_DUPLICATE,
    REASON_INVALID,
    REASON_NO_VERSION,
    REASON_NOT_EXACT,
    REASON_NOT_PYPI,
    REASON_OPTION,
    parse,
)

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "frontend" / "public" / "examples"

EXPECTED_IDS = [
    "healthy-check",
    "macos-local",
    "old-ubuntu",
    "windows-dev",
    "web-api",
    "data-science",
    "messy-reqs",
    "legacy-django",
    "conflict-calendar",
    "large-freeze",
]

VALID_GROUPS = {"처음이라면", "흔한 증상", "까다로운 경우"}


def test_examples_index_files_parse_and_counts_match():
    index_path = EXAMPLES_DIR / "index.json"
    assert index_path.exists()
    entries = json.loads(index_path.read_text(encoding="utf-8"))
    assert [e["id"] for e in entries] == EXPECTED_IDS

    by_id = {e["id"]: e for e in entries}

    for entry in entries:
        assert entry["group"] in VALID_GROUPS, entry["id"]
        assert isinstance(entry.get("tags"), list) and 2 <= len(entry["tags"]) <= 3, entry["id"]
        assert all(isinstance(t, str) and t.strip() for t in entry["tags"]), entry["id"]

        file_path = EXAMPLES_DIR / entry["file"]
        assert file_path.exists(), f"missing example file: {entry['file']}"
        parsed = parse(file_path.read_text(encoding="utf-8"))
        assert len(parsed.packages) == entry["package_count"], entry["id"]
        assert len(parsed.excluded) == entry["excluded_count"], entry["id"]

        if entry["id"] == "conflict-calendar":
            se = entry.get("seed_event")
            assert isinstance(se, dict)
            assert se["title"] == "[예시] 정기 배포"
            assert se["offset_days"] == 0
            assert se["start"] == "21:00"
            assert se["end"] == "23:00"
        else:
            assert "seed_event" not in entry, entry["id"]

    # 오래된 우분투 예시는 조회 제외 줄(-e) 1개
    old_ubuntu_parsed = parse((EXAMPLES_DIR / by_id["old-ubuntu"]["file"]).read_text(encoding="utf-8"))
    assert len(old_ubuntu_parsed.excluded) == 1
    assert "오래 걸림" in by_id["large-freeze"]["description"]
    assert "날마다 달라질 수" in by_id["healthy-check"]["description"]


def test_messy_reqs_example_covers_parsing_rules():
    parsed = parse((EXAMPLES_DIR / "messy-reqs.txt").read_text(encoding="utf-8"))
    pkg_map = {p.name: p for p in parsed.packages}
    assert list(pkg_map) == ["requests", "Django", "urllib3", "pywin32"]
    assert pkg_map["Django"].version == "4.2.0"
    assert pkg_map["urllib3"].version == "1.24.1"
    assert pkg_map["pywin32"].marker == 'sys_platform == "win32"'

    excl_reasons = [(e.text, e.reason) for e in parsed.excluded]
    assert excl_reasons == [
        ("-r base.txt", REASON_OPTION),
        ("--index-url https://pypi.org/simple", REASON_OPTION),
        ("flask>=2.0", REASON_NOT_EXACT),
        ("pytest", REASON_NO_VERSION),
        ("Requests==2.25.0", REASON_DUPLICATE),
        ("-e git+https://github.com/example/private.git#egg=private", REASON_NOT_PYPI),
        ("internal-pkg @ https://example.com/internal_pkg-1.0.whl", REASON_NOT_PYPI),
        ("???not_a_package", REASON_INVALID),
    ]


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

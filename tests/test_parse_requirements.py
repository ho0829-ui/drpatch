"""requirements.txt 파싱 (spec "requirements.txt 파싱 규칙")."""

import codecs

import pytest

from app.parsing.requirements import (
    REASON_DUPLICATE,
    REASON_INVALID,
    REASON_NO_VERSION,
    REASON_NOT_EXACT,
    REASON_NOT_PYPI,
    REASON_OPTION,
    Package,
    decode,
    parse,
    parse_bytes,
)


def one_package(line: str) -> Package:
    result = parse(line)
    assert result.excluded == [], result.excluded
    assert len(result.packages) == 1
    return result.packages[0]


def excluded_reason(line: str) -> str:
    result = parse(line)
    assert result.packages == [], result.packages
    assert len(result.excluded) == 1
    return result.excluded[0].reason


def test_spec_example():
    """spec 맨 아래 예시: 조회 2개, 제외 1개(-e)."""
    text = "requests==2.19.0\ndjango==2.2.0\n-e git+https://github.com/me/tool.git#egg=tool\n"
    result = parse(text)
    assert [(p.name, p.version, p.line_no) for p in result.packages] == [
        ("requests", "2.19.0", 1),
        ("django", "2.2.0", 2),
    ]
    assert len(result.excluded) == 1
    assert result.excluded[0].line_no == 3
    assert result.excluded[0].reason == REASON_NOT_PYPI
    assert result.excluded[0].text.startswith("-e git+")


@pytest.mark.parametrize(
    "line,name,version",
    [
        ("django==2.2.0", "django", "2.2.0"),
        ("Django == 2.2.0", "Django", "2.2.0"),
        ("Django[argon2,bcrypt]==2.2.0", "Django", "2.2.0"),
        ("django==2.2.0  # via -r requirements.in", "django", "2.2.0"),
        ("typing_extensions==4.16.0", "typing_extensions", "4.16.0"),
        ("zope.interface==6.0", "zope.interface", "6.0"),
        ("pkg==1.0rc1", "pkg", "1.0rc1"),
        ("pkg==1!2.0+local.1", "pkg", "1!2.0+local.1"),
        ("pkg==1.0 --hash=sha256:abc", "pkg", "1.0"),
    ],
)
def test_queried_lines(line, name, version):
    pkg = one_package(line)
    assert (pkg.name, pkg.version, pkg.marker) == (name, version, None)


def test_marker_is_stripped_and_kept():
    pkg = one_package('pywin32==306 ; sys_platform == "win32"')
    assert (pkg.name, pkg.version) == ("pywin32", "306")
    assert pkg.marker == 'sys_platform == "win32"'


def test_continuation_lines_with_hashes():
    text = "django==2.2.0 \\\n    --hash=sha256:aaa \\\n    --hash=sha256:bbb\nrequests==2.19.0\n"
    result = parse(text)
    assert [(p.name, p.line_no) for p in result.packages] == [("django", 1), ("requests", 4)]
    assert result.excluded == []


@pytest.mark.parametrize("text", ["", "\n\n", "# 주석만\n   # 들여쓴 주석\n"])
def test_blank_and_comments_are_ignored(text):
    result = parse(text)
    assert result.packages == [] and result.excluded == []


@pytest.mark.parametrize(
    "line,reason",
    [
        ("-e git+https://github.com/me/tool.git#egg=tool", REASON_NOT_PYPI),
        ("--editable ./local", REASON_NOT_PYPI),
        ("mytool @ file:///home/me/mytool", REASON_NOT_PYPI),
        ("mytool @ https://example.com/mytool-1.0.tar.gz", REASON_NOT_PYPI),
        ("git+https://github.com/me/tool.git", REASON_NOT_PYPI),
        ("./vendor/pkg.whl", REASON_NOT_PYPI),
        ("django>=2.2", REASON_NOT_EXACT),
        ("django<3", REASON_NOT_EXACT),
        ("django~=2.2.0", REASON_NOT_EXACT),
        ("django!=2.2.1", REASON_NOT_EXACT),
        ("django==2.2.*", REASON_NOT_EXACT),
        ("django===2.2.0", REASON_NOT_EXACT),
        ("django>=2.2,<3", REASON_NOT_EXACT),
        ("-r base.txt", REASON_OPTION),
        ("-c constraints.txt", REASON_OPTION),
        ("--index-url https://pypi.org/simple", REASON_OPTION),
        ("django", REASON_NO_VERSION),
        ("Django[argon2]", REASON_NO_VERSION),
        ("이건 패키지가 아님", REASON_INVALID),
        ("django 2.2.0", REASON_INVALID),
    ],
)
def test_excluded_lines(line, reason):
    assert excluded_reason(line) == reason


def test_duplicates_keep_first_only():
    text = "Django==2.2.0\ndjango==3.2.0\ntyping_extensions==4.0\ntyping-extensions==4.1\n"
    result = parse(text)
    assert [(p.name, p.version) for p in result.packages] == [
        ("Django", "2.2.0"),
        ("typing_extensions", "4.0"),
    ]
    assert [(e.line_no, e.reason) for e in result.excluded] == [(2, REASON_DUPLICATE), (4, REASON_DUPLICATE)]


def test_excluded_does_not_count_as_seen():
    """제외된 줄(>=)은 중복 판단에 쓰지 않는다: 뒤의 정확한 줄은 조회."""
    result = parse("django>=2.2\ndjango==2.2.0\n")
    assert [p.version for p in result.packages] == ["2.2.0"]
    assert [e.reason for e in result.excluded] == [REASON_NOT_EXACT]


def test_crlf_line_endings():
    result = parse("requests==2.19.0\r\ndjango==2.2.0\r\n")
    assert [p.name for p in result.packages] == ["requests", "django"]


FREEZE = "requests==2.19.0\ndjango==2.2.0\n"


@pytest.mark.parametrize(
    "raw",
    [
        FREEZE.encode("utf-8"),
        codecs.BOM_UTF8 + FREEZE.encode("utf-8"),
        FREEZE.encode("utf-16"),  # BOM 포함 (PowerShell `pip freeze >`)
        codecs.BOM_UTF16_LE + FREEZE.encode("utf-16-le"),
        codecs.BOM_UTF16_BE + FREEZE.encode("utf-16-be"),
    ],
)
def test_encodings(raw):
    result = parse_bytes(raw)
    assert [(p.name, p.version) for p in result.packages] == [("requests", "2.19.0"), ("django", "2.2.0")]
    assert result.excluded == []


def test_undecodable_bytes_do_not_raise():
    text = decode(b"requests==2.19.0\n\xff\xfe\xfa broken\n")
    result = parse(text)
    assert [p.name for p in result.packages] == ["requests"]
    assert [e.reason for e in result.excluded] == [REASON_INVALID]


def test_to_dict_shape():
    data = parse('pywin32==306 ; sys_platform == "win32"\ndjango>=2\n').to_dict()
    assert data == {
        "packages": [{"name": "pywin32", "version": "306", "line_no": 1, "marker": 'sys_platform == "win32"'}],
        "excluded": [{"line_no": 2, "text": "django>=2", "reason": REASON_NOT_EXACT}],
    }

"""Agent에게 넘기는 Tool 명세 (이름·설명·입력 형식). docs/spec.md "Tool 명세" 기준.

여기에는 명세만 둔다. 실제 API 호출 구현과 레지스트리는 F3001~F3004 작업에서 붙인다.
형식은 OpenAI function 스키마라서 ChatOpenAI.bind_tools()에 그대로 넘길 수 있다.
"""

GET_EOL = {
    "type": "function",
    "function": {
        "name": "get_eol",
        "description": "OS나 Python이 언제까지 지원되는지 알아야 할 때 쓴다. "
        "일반 지원 종료일, 확장 지원(ESM) 종료일, 지원 종료 여부, LTS 여부, 최신 패치 버전을 돌려준다.",
        "parameters": {
            "type": "object",
            "properties": {
                "product": {
                    "type": "string",
                    "description": "endoflife.date 제품 이름. 예: ubuntu, python",
                },
                "cycle": {
                    "type": "string",
                    "description": "릴리스 줄기. 예: ubuntu는 20.04, python은 3.8",
                },
            },
            "required": ["product", "cycle"],
            "additionalProperties": False,
        },
    },
}

GET_VULNS = {
    "type": "function",
    "function": {
        "name": "get_vulns",
        "description": "특정 PyPI 패키지 버전이 위험한지, 몇 버전에서 고쳐졌는지 알아야 할 때 쓴다. "
        "취약점 개수와 취약점별 등급·수정 버전을 돌려준다.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "PyPI 패키지 이름. 예: django"},
                "version": {"type": "string", "description": "확인할 버전. 예: 2.2.0"},
            },
            "required": ["name", "version"],
            "additionalProperties": False,
        },
    },
}

GET_PACKAGE_VERSIONS = {
    "type": "function",
    "function": {
        "name": "get_package_versions",
        "description": "업그레이드할 버전이 지금 Python에서 설치되는지 알아야 할 때 쓴다. "
        "패키지의 최신 버전과 버전별 requires_python·yanked 여부를 돌려준다.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "PyPI 패키지 이름. 예: requests"},
            },
            "required": ["name"],
            "additionalProperties": False,
        },
    },
}

TOOL_SPECS = [GET_EOL, GET_VULNS, GET_PACKAGE_VERSIONS]

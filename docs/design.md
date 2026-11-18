# 디자인: 보안 관제(SOC) 대시보드 (2026-11-18)

Figma: https://www.figma.com/design/MVNo4L7Ru7X4tFDrpWmMNS (페이지: Screens · Foundations · Components)
Vue 화면은 이 문서의 토큰·화면 구성을 따른다. Figma 변수 이름 = CSS 변수 이름.

## 글꼴
- 본문·제목: **IBM Plex Sans KR** (Regular 400 / Medium 500 / SemiBold 600 / Bold 700)
- 데이터·버전·로그: **JetBrains Mono** (Regular 400 / Bold 700)
- 둘 다 Google Fonts.

## 색 (Dark 하나)
| 토큰 | 값 | 쓰임 |
|---|---|---|
| `--color-bg` | #0A0E15 | 화면 바탕 |
| `--color-surface` | #111722 | 카드·사이드바 |
| `--color-surface-2` | #172030 | 카드 안 줄·입력칸 |
| `--color-surface-3` | #1E293B | 강조 칸 |
| `--color-line` | #243044 | 테두리 |
| `--color-line-strong` | #33415A | 입력칸·버튼 테두리 |
| `--color-text` | #E6EBF2 | 본문 |
| `--color-text-muted` | #8C97AB | 보조 |
| `--color-text-faint` | #5C677A | 시간·라벨 |
| `--color-accent` / `-soft` | #22D3EE / #0E3A44 | 주요 버튼·현재 메뉴·목표 버전·패치 일정 |
| `--color-ok` / `-soft` | #34D399 / #0F3A2C | 성공·안전·확정 |
| `--color-sev-critical` / `-soft` | #F43F5E / #4A1220 | CRITICAL·실패·내 일정 |
| `--color-sev-high` / `-soft` | #FB923C / #4A2410 | HIGH |
| `--color-sev-moderate` / `-soft` | #FACC15 / #3F3508 | MODERATE |
| `--color-sev-low` / `-soft` | #60A5FA / #112A4A | LOW |
| `--color-sev-unknown` / `-soft` | #94A3B8 / #222C3B | 심각도 미상·확인 못 함 |
| `--color-replan` / `-soft` | #F59E0B / #3B2A08 | 재계획·일정 이동·표시(flag)·겹침 경고 |

## 간격·모서리
- 간격: 4 / 8 / 12 / 16 / 24 / 32 (`--space-1`~`--space-6`)
- 모서리: 6(sm) / 10(md) / 14(lg) / 999(pill)

## 글자 스타일
| 이름 | 글꼴 | 크기/줄 높이 |
|---|---|---|
| display | Plex KR Bold | 28/36 |
| title | Plex KR SemiBold | 18/26 |
| subtitle | Plex KR SemiBold | 15/22 |
| body / body-strong | Plex KR Regular / Medium | 14/22 |
| caption | Plex KR Regular | 12/18 |
| label | Plex KR Medium, 자간 6% | 11/16 |
| mono / mono-strong | JetBrains Mono Regular / Bold | 13/20 |
| mono-sm | JetBrains Mono Regular | 11/16 |
| metric | JetBrains Mono Bold | 30/36 |

## 컴포넌트 (Figma Components 페이지)
| 이름 | 변형 | 내용 |
|---|---|---|
| Badge/Severity | CRITICAL·HIGH·MODERATE·LOW·UNKNOWN | 점 + 등급 글자, 등급 색 soft 바탕 |
| Badge/Flag | — | 테두리만 replan 색 (큰 변경·호환 미확인·종료 이후 처리·일정 이동) |
| Button | primary·ghost·danger | |
| NavItem | active·default | 왼쪽 막대 + 글자 |
| StepRow | step·tool-ok·tool-fail·decision·replan·plan | 실행 단계 한 줄 (점 + 글자 + 시간). replan·tool-fail은 바탕색 |
| KpiCard | — | 라벨 · 큰 숫자(metric) · 보조 |
| ItemRow | — | 패키지 이름·이유 / 현재 → 목표(mono, accent) / 등급 배지 |

## 화면 (1440×960 기준)
레이아웃 공통: 왼쪽 사이드바 240px(로고, 메뉴 4개, 아래 대상 서버 카드, 출처) + 위 상단바(제목·설명·세션 칩·새 대화).

1. **대화 + 실시간 실행 단계**: KPI 4개(CRITICAL 패키지·HIGH 이상 항목·재계획·응답 시간) / 왼쪽 업로드 카드 + 메시지(스크롤) + 입력창 고정 / 오른쪽 실행 단계 패널 380px (StepRow, 재계획 강조)
2. **회차 계획 보드**: Python 업그레이드 경로(3.8 → 3.9 → 3.10 종료 → 3.11 확정) / 회차 칸반(회차당 카드) / 오른쪽 "무엇부터(실행 순서)" + 안전·확인 못 함·보류·조회 제외
3. **캘린더 + 계획 관리**: 월 달력(패치 회차 accent, 내 일정 critical, 이동한 회차는 "↻ 원래 날짜") / 오른쪽 저장한 계획(수정 폼·겹침 경고·삭제) + 내 일정 추가
4. **실행 로그**: 세션 목록(실패 표시) / 이벤트 타임라인(#seq) / 오른쪽 판단 근거(judgment, plan_built 규칙)

## Figma에서 남은 것
- 캘린더 칸 안 일정 칩 글자가 잘림 → 칩 글자를 칸 너비에 맞춰 줄바꿈 (Starter 요금제 MCP 호출 한도로 Figma에서는 못 고침, Vue에서 반영)

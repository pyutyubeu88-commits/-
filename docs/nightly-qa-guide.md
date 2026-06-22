# Nightly QA 자동화 가이드

## 개요

매일 새벽 3시(KST) Claude Code가 자동으로 사이트를 검수하고, 문제를 분류·조치합니다.

## 작동 흐름

```
[새벽 3시 자동 실행]
        ↓
  Job 1: QA 검수 (읽기 전용)
  Claude가 5개 파일 분석 → qa-result.json 생성
        ↓
  ┌─────────────────────────────────────────────────────┐
  │ 🔴 긴급 발견 시  → Job 2: 자동 수정 → PR 생성 → 자동 머지│
  │ 🟡 권고 발견 시  → Job 3: GitHub Issue 생성            │
  │ 🟢 이상없음      → Job 3: 리포트 이슈만 생성             │
  └─────────────────────────────────────────────────────┘
        ↓
  Job 3: 일일 리포트 이슈 생성 (항상)

※ 긴급 버그는 사람 개입 없이 완전 자동으로 수정·배포됩니다.
※ PR은 이력 보존 목적으로 생성 후 즉시 자동 머지됩니다.
```

## 사용자가 매일 확인하는 방법

GitHub → 저장소 → **Issues** 탭에서 `nightly-qa` 라벨로 필터링하면
매일 아침 검수 결과 리포트가 올라와 있습니다.

- `[Nightly QA 리포트] 2026-06-23` — 일일 요약
- `[Nightly QA] ebook.html - 가격 불일치` — 권고 이슈 (수동 조치 필요)
- `[Nightly QA] 긴급 자동 수정 (2026-06-23)` — PR (머지만 하면 됨)

## 자동 수정 범위

### Claude가 직접 수정하는 것 (🔴 긴급)
- 가격 문자열 불일치 (14,900원 기준)
- 보안 문제 (API 키 하드코딩 → TODO 플레이스홀더)
- HTML 구조 오류 (중복 id, 태그 미매칭)
- CTA 버튼 href 누락

### Issue로만 등록하는 것 (🟡 권고)
- 이미지 alt 누락
- 반응형 미흡
- 외부 링크 응답 이상
- JS 런타임 오류 가능성

## GitHub 권장 설정

### 1. Branch Protection (자동 수정 PR 안전하게 머지)
Settings → Branches → main → Protection rules:
- [x] Require a pull request before merging
- [x] Dismiss stale PR reviews when new commits are pushed

### 2. 브랜치 자동 삭제 (fix/ 브랜치 쌓임 방지)
Settings → General → Pull Requests:
- [x] Automatically delete head branches

### 3. Issue 라벨 생성 (없으면 수동 생성)
- `nightly-qa` (색상: #0075ca)
- `report` (색상: #e4e669)

## 필요한 GitHub Secret

| Secret 이름 | 값 | 설명 |
|------------|-----|------|
| `CLAUDE_CODE_OAUTH_TOKEN` | `~/.claude/.credentials.json`의 `claudeAiOauthToken` | Claude Pro 인증 |

## 에이전트 아이디어 수집 기록 (2026-06-22)

업그레이드 전 3개 에이전트로부터 아이디어를 수집했습니다.

### 보안/품질 에이전트 제안
- 자동 수정 안전 범위: alt 속성, lang 속성, vercel.json 보안 헤더, 가격 오타
- 자동 수정 불가: XSS 패턴, 외부 링크, JS 로직 오류

### 비즈니스/UX 에이전트 제안
- 매출 직결 우선순위: 가격 불일치 > CTA 버튼 > 연락처 오류 > 날짜 만료
- `--max-turns 25` 이상 권장

### 아키텍처 에이전트 제안
- 3-Job 분리 구조 (scan → fix → report)
- `qa-result.json` 아티팩트로 Job 간 데이터 공유
- 중복 이슈 방지 로직
- 검수 결과 30일 아티팩트 보관

## 수동 실행 방법

GitHub → Actions → `Nightly QA — 자동 검수 + 긴급 자동 수정` → `Run workflow`

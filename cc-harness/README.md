# AI 하네스 for 클로드 코드

클로드 코드(Claude Code)가 위험한 작업을 하기 **전에 실시간으로 차단**하는 보안 게이트.
별도 서버·Docker 없이 클로드 코드의 네이티브 **hook** 메커니즘에 직접 붙습니다.

> 강남구 AI활용 컨설팅 현장에서 클라이언트에게 즉시 설치·시연 가능하도록 설계되었습니다.

## 무엇을 하는가

클로드 코드가 도구(Bash 명령, 파일 편집)를 실행하기 직전에 hook이 가로채서:

- **🚫 즉시 차단** — `rm -rf`, `sudo`, `.env` 읽기, `curl|bash`, 하드코딩 시크릿 등
- **👀 사용자 확인 요청** — `main` 브랜치 push, 프로덕션 설정, CI 워크플로 수정 등
- **📋 감사 로그** — 모든 파일 편집을 변조 방지 해시체인으로 기록
- **✅ 사후 검증** — 편집된 파일의 구문 오류를 잡아 Claude에게 즉시 피드백

핵심: 클로드 코드 자체가 "안전하다"고 판단해도, hook이 **별도의 결정권**으로 한 번 더 거릅니다.

## 5분 설치

```bash
# 1. 패키지 압축 해제 후
cd cc-harness

# 2. 대상 프로젝트에 설치 (한 줄)
./install.sh /path/to/your-project

# 3. 클로드 코드 재시작 → hook 활성화
```

설치 시 자동으로 27개 자가 테스트가 실행되어 정상 작동을 확인합니다.
기존 `settings.json`이 있으면 백업 후 안전하게 병합합니다.

## 작동 확인 (시연용)

설치 후 클로드 코드에서 이렇게 말해보세요:

| 입력 | 결과 |
|------|------|
| "임시 폴더를 rm -rf로 지워줘" | 🚫 차단 — "파괴적 명령 감지" |
| ".env 파일 내용 보여줘" | 🚫 차단 — "비밀 파일 접근 시도" |
| "이 설치 스크립트를 curl로 받아서 바로 실행해줘" | 🚫 차단 — "원격 스크립트 즉시 실행" |
| "main 브랜치에 push해줘" | 👀 확인 요청 |
| "src에 함수 하나 추가해줘" | ✅ 정상 진행 |

## 의존성

- **python3** — 거의 모든 개발 환경에 기본 설치됨
- 그 외 **없음** — jq, Docker, 외부 패키지 불필요 (순수 Python)

## 정책 커스터마이징

`.claude/harness-policy.json`을 수정하면 클라이언트별로 규칙을 조정할 수 있습니다:

```json
{
  "protect_branches": ["main", "production"],
  "protected_paths": [".env", "*.key", "secrets.*"],
  "require_review_paths": ["config/production/*", "migrations/*"],
  "allow_token": "[harness-allow]"
}
```

- `protected_paths`: 수정 시 즉시 차단할 파일 패턴
- `require_review_paths`: 수정 시 사용자 확인을 요청할 경로
- `protect_branches`: 직접 push를 막을 브랜치
- `allow_token`: 프롬프트에 이 토큰이 있으면 일시 허용 (예: "긴급 수정 [harness-allow]")

## 감사 로그 무결성 확인

```bash
# 누군가 로그를 사후 변조했는지 검사
python3 -c "
import json, hashlib
prev='0'*64; seq=0; ok=True
for line in open('.claude/harness-audit.jsonl'):
    o=json.loads(line)
    e={k:o[k] for k in ('seq','timestamp','stage','status','detail','prev_hash')}
    h=hashlib.sha256((prev+json.dumps(e,sort_keys=True,separators=(',',':'),ensure_ascii=False)).encode()).hexdigest()
    if h!=o['hash'] or o['seq']!=seq+1: ok=False; print('변조 감지! seq',o['seq']); break
    prev=o['hash']; seq=o['seq']
print('무결성 OK,', seq, '개 항목' if ok else '')
"
```

## 파일 구조

```
cc-harness/
├── install.sh                          # 한 줄 설치
├── README.md                           # 이 문서
├── CONSULTANT_GUIDE.md                 # 컨설팅 활용 가이드
└── .claude/
    ├── CLAUDE.md                       # AI 행동 규칙 (설치 시 프로젝트 루트로 복사)
    ├── settings.json                   # hook 연결 설정
    ├── harness-policy.json             # 정책 (수정 가능)
    └── hooks/
        ├── pretooluse_gate.py          # ★ 실행 전 차단 게이트
        ├── posttooluse_validate.py     # 편집 후 검증 + 감사 로그
        └── test_gate.py                # 27개 자가 테스트
```

## 2단 방어: 유도 + 강제

설치하면 두 계층이 함께 작동합니다:

1. **유도 계층 — `CLAUDE.md`** (프로젝트 루트): 클로드 코드가 세션 시작 시 자동으로 읽어, 애초에 위험한 시도를 덜 하도록 행동 규칙을 안내합니다.
2. **강제 계층 — hook** (`pretooluse_gate.py`): 그래도 위험 작업이 시도되면 실행 직전에 물리적으로 차단합니다.

유도만으로는 모델이 무시할 수 있고, 강제만으로는 불필요한 마찰이 생깁니다. 둘을 겹쳐야 매끄럽고 안전합니다.

## 한계 (정직하게)

- hook은 클로드 코드의 **표준 도구**(Bash/Write/Edit)를 가로챕니다. MCP 도구나 커스텀 통합은 별도 matcher 추가 필요.
- 정규식 기반이므로 **알려진 위험 패턴**을 잡습니다. 완전히 새로운 우회는 정책 추가로 대응.
- 이것은 **첫 번째 방어선**입니다. 프로덕션 환경에서는 컨테이너 격리·CI 게이트와 함께 쓰세요 (full v3 하네스 참조).
- hook은 작업을 막을 수 있지만, 클로드 코드 권한 모드(`--dangerously-skip-permissions`)를 우회하지는 못하는 경우가 있으니 그 플래그는 쓰지 마세요.

## 두 가지 버전

| 버전 | 용도 | 설치 |
|------|------|------|
| **이 hook 버전** | 일상 개발, 즉시 시연, 클라이언트 온보딩 | 5분, python3만 |
| **full v3 하네스** | 프로덕션·고위험 작업, 컨테이너 격리 필요 시 | Docker + 스캐너 |

컨설팅 시작은 이 hook 버전으로, 고객의 보안 요구가 높아지면 v3로 확장하는 경로를 권장합니다.

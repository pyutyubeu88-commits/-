# 프로젝트 작업 규칙 (AI 하네스 적용 중)

이 프로젝트에는 PreToolUse 보안 게이트가 설치되어 있다.
아래 규칙을 지키면 게이트에 막히지 않고 원활히 작업할 수 있다.

## 절대 하지 말 것 (게이트가 자동 차단)
- `rm -rf`, `rm -fr`, `find ... -delete` 등 대량/재귀 삭제
- `sudo`, `chmod 777`, 권한 상승 명령
- `.env`, `*.key`, `*.pem`, `id_rsa`, `credentials` 파일 읽기/쓰기
- `curl ... | bash`, `wget ... | sh` 등 원격 스크립트 즉시 실행
- 코드에 API 키·패스워드·시크릿 하드코딩
- 환경변수를 외부로 전송 (`env | nc`, `printenv | curl` 등)

## 사용자 확인이 필요한 것 (게이트가 ask)
- `main` / `master` / `production` 브랜치 직접 push, force push
- 프로덕션 설정(`config/production/*`, `*.prod.*`) 수정
- DB 마이그레이션, CI 워크플로(`.github/workflows/*`) 변경
- `eval(input)`, `exec(input)`, `subprocess(..., shell=True)` 등 위험 코드 패턴

## 권장 작업 방식
- 코드 변경은 `src/`, `tests/`, `docs/` 디렉토리 안에서 수행
- 비밀값은 항상 환경변수로 읽기: `os.environ.get("API_KEY")`
- 삭제가 필요하면 대상을 명시: `rm old_file.txt` (와일드카드·재귀 금지)
- 새 의존성을 추가할 때는 그 이유를 변경 설명에 남길 것
- 정당한 사유로 위 규칙을 일시 우회해야 하면 실행할 **명령어 끝에** `# [harness-allow]` 주석 포함
  예: `rm -rf /tmp/old_build  # [harness-allow]`

## 작업 완료 기준
1. 기존 테스트 통과 (회귀 없음)
2. 새 기능에는 테스트 작성
3. 편집한 파일에 구문 오류 없음 (PostToolUse 가 자동 검사하여 피드백)
4. 변경 사항 요약 제공

## 참고
- 게이트 정책은 `.claude/harness-policy.json` 에서 조정 가능
- 모든 파일 편집은 `.claude/harness-audit.jsonl` 에 변조 방지 로그로 기록됨
- 이 규칙은 게이트의 *유도* 계층이다. 게이트 자체가 최종 *강제* 계층으로 작동한다.

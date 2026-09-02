---
name: 숏폼편집
description: 숏폼/릴스 영상을 자연어 한 줄 지시로 무료 로컬 도구(ffmpeg+whisper)로 자동 편집한다 (컷편집, 세로 리프레임, 질문배너/로고, 자막, B-roll 삽입, 효과음). "이 영상 편집해줘", "자막 붙여줘", "세로로 바꿔줘", "숏폼 자동화" 같은 요청에 사용.
---

# 숏폼 자동 편집

**로컬 전용 스킬**. ffmpeg + whisper로 실제 영상 파일을 처리하므로, 영상 파일과 ffmpeg가 있는
로컬 Claude Code(또는 Cowork 데스크톱)에서 돌아간다. 이 클라우드 세션에는 ffmpeg/whisper가 없어서
스크립트 코드는 여기서 작성했지만 실제 영상으로 테스트는 못 했다 — 로컬에서 처음 쓸 때
`## 로컬 세팅` → `## 스모크 테스트`부터 먼저 돌려서 확인할 것.

## 요청 문장 → 처리 방식

| 단계 | 예시 요청 | 처리 방식 | 상태 |
|---|---|---|---|
| 1. 컷 편집 | "이 영상 편집해줘. 빈 공간 다 없애고, 같은 말 여러 번 한 데는 마지막 것만 써. 1.1배속으로." | `scripts/cut_edit.py` (whisper 받아쓰기 → 무음/재테이크 감지 → ffmpeg 컷+배속) | 로컬에서 바로 가능 |
| 2. 화면 리프레임 | "가로 찍은 거 세로로. 얼굴 따라가면서 잘라." | `scripts/reframe_vertical.py` (opencv 얼굴 검출 → ffmpeg 동적 크롭, 1080x1920 출력) | 로컬에서 가능, 얼굴 인식 정확도는 케이스마다 확인 필요 |
| 3. 상단 질문 배너 + 로고 워터마크 | "위에 질문 고정으로 띄우고, 로고 박아줘." | `scripts/add_branding.py` (ffmpeg drawtext/drawbox, 영상 처음부터 끝까지 고정) | 로컬에서 바로 가능, 한글 폰트 파일(.ttf) 경로 필요 |
| 4. 자막 | "자막 붙여줘. 검정 박스에 흰 글씨, 한 줄로, 안 들어가면 대사 쪼개." | `scripts/make_captions.py` (whisper → 스타일 프리셋 적용 ASS → ffmpeg 번인, 1080x1920 캔버스) | 로컬에서 바로 가능 (영문 자막은 번역 파일 필요, 아래 참고) |
| 5. 배경 지우기 | (이 프로젝트는 미사용 — 필요해지면) | Higgsfield `remove_background` | **Higgsfield 커넥터 인증 필요**, 유료 크레딧 |
| 6. 없는 장면 대체 | "이 대사에 붙일 장면 없어. B-roll 끼워줘." | `scripts/insert_broll.py` (직접 찍은 컷 또는 무료 스톡 클립을 지정 구간에 덮어씌움, 나레이션은 안 끊김) | **로컬 무료** — AI 생성 대신 진짜 클립 사용 |
| 7. 효과음 | "효과음 넣어줘. 목소리보다 작게, 자막 뜨는 순간에 맞춰." | `scripts/add_sfx.py` (무료 SFX 파일을 타이밍 맞춰 ffmpeg로 합성) | **로컬 무료** — AI 생성 대신 무료 라이브러리 소스 |
| 8. 최종 검수 | "결과물 폴더 열어주고, 완성본 다시 받아 적어서 대본이랑 맞는지 봐줘." | `scripts/qc_check.py` (whisper 재검증 → 대본 대조) | 로컬에서 바로 가능 — **매 작업 마지막에 반드시 실행** |

파이프라인 순서: **컷편집 → 리프레임 → 브랜딩(질문배너/로고) → B-roll 삽입 → 효과음 → 자막 → QC**.
자막은 항상 제일 마지막(QC 직전)에 입혀야 다른 단계에서 화면이 밀리거나 바뀌어도 자막 타이밍이 안 어긋난다.

Higgsfield는 배경 지우기가 필요해질 때만 쓴다 (`.mcp.json`에 연결은 돼 있지만 OAuth 인증 필요 —
claude.ai 커넥터 설정에서). 그 외 6·7단계는 아래 무료 소스로 전부 대체 가능해서 이 프로젝트는
Higgsfield 없이도 끝까지 완성된다.

### 무료 소스 (6·7단계용)

| 용도 | 사이트 | 라이선스 |
|---|---|---|
| 효과음 | [Pixabay Sound Effects](https://pixabay.com/sound-effects/) | 상업적 이용 무료, 출처 표시 불필요 |
| 효과음 | [Mixkit Sound Effects](https://mixkit.co/free-sound-effects/) | 상업적 이용 무료, 출처 표시 불필요 |
| B-roll 스톡 영상 | [Pexels Videos](https://www.pexels.com/videos/) | 상업적 이용 무료, 출처 표시 불필요 |
| B-roll 스톡 영상 | [Pixabay Videos](https://pixabay.com/videos/) | 상업적 이용 무료, 출처 표시 불필요 |
| 한글 폰트 | [Pretendard](https://cactus.tistory.com/306) (GitHub: orioncactus/pretendard) | SIL OFL — 상업적 이용 무료 |

가장 좋은 B-roll은 결국 직접 찍은 것 — 대본 짤 때 "이 문장엔 무슨 장면이 필요할지"를 같이
정해서 촬영 리스트에 넣어두면 `insert_broll.py`로 바로 끼울 수 있다.

## 레퍼런스 릴스 분석 (2026-09-01, 강남 치과 인터뷰형 숏폼)

사용자가 올려준 예시 릴스(9:16, 720x1280, 39.5초)를 프레임 단위로 직접 뜯어본 결과.
이전에 스레드에서 참고했던 "영문 위/한글 아래 형광펜 박스" 포맷과는 다른, **인터뷰 Q&A형** 포맷이었다.

- **상단 고정 배너**: 흰 배경 띠 위에 "Q." + 질문 2줄(1줄 검정, 2줄 파란 강조), 영상 끝까지 안 바뀜 →
  `add_branding.py --question`
- **하단 자막**: 불투명 검정 박스 + 흰 굵은 글씨, 최대 2줄, 형광펜/그라데이션 없음 → 이 스타일이 기본값이 되도록
  `default_style.json`의 `korean_highlight_bg`를 불투명 검정(`&H00000000&`)으로 맞춰뒀다
  (이전 값 `&HFF00D7FF&`는 alpha가 FF라 사실상 투명 배경이 되는 버그였음 — 수정함)
- **로고 워터마크**: 하단 좌측에 브랜드명+서브텍스트 고정 → `add_branding.py --logo`
- **훅 구조**: 질문에 결론부터 답하고("네 많이 다릅니다") 그다음 이유 설명 — 이건 스크립트가 아니라
  **대본 작성 단계에서 지켜야 할 규칙**. 클라이언트 인터뷰 대본 만들 때 이 순서로 짤 것
- **B-roll 컷인**: 설명 중간에 관련 사진/영상(구강 사진, 시술 장면)을 끼워 넣음 — 이것도 자동화 대상이
  아니라 원본 소스 중에서 어떤 걸 어느 타이밍에 끼울지 클로드가 판단해서 `cut_edit.py` 전에
  수동으로 골라 붙여야 하는 영역

즉 "완전 자동"이 되는 건 컷편집/리프레임/배너·로고/자막/QC고, **대본 구조와 B-roll 선정은 클로드가
매번 판단**해야 하는 영역이다.

## 로컬 세팅 (처음 한 번)

```bash
brew install ffmpeg   # 또는 apt install ffmpeg
pip3 install -r .claude/skills/숏폼편집/requirements.txt
```

## 스모크 테스트

로컬에서 실전 영상에 쓰기 전에 짧은(10~20초) 테스트 클립으로 먼저 돌려서
whisper 인식 품질·크롭 좌표·자막 줄바꿈이 정상인지 확인한다.

```bash
python3 .claude/skills/숏폼편집/scripts/cut_edit.py test.mp4 test_cut.mp4
python3 .claude/skills/숏폼편집/scripts/reframe_vertical.py test_cut.mp4 test_vert.mp4
python3 .claude/skills/숏폼편집/scripts/add_branding.py test_vert.mp4 test_branded.mp4 \
    --question "질문 1줄" "질문 2줄" --logo "브랜드명" "서브텍스트" --font /path/Pretendard-Bold.ttf
# 필요할 때만: B-roll 삽입, 효과음
python3 .claude/skills/숏폼편집/scripts/insert_broll.py test_branded.mp4 broll.mp4 test_broll.mp4 --at 5 --duration 3
python3 .claude/skills/숏폼편집/scripts/add_sfx.py test_broll.mp4 test_sfx.mp4 --cues cues.json
python3 .claude/skills/숏폼편집/scripts/make_captions.py test_sfx.mp4 test_final.mp4
python3 .claude/skills/숏폼편집/scripts/qc_check.py test_final.mp4 test_script.txt
```

## 처음 한 번만 정하면 되는 것

- **폴더 구조**: `output/{날짜}_{주제}/` — 원본, 중간 산출물, 최종본을 매번 같은 구조로
- **자막 스타일**: `presets/default_style.json` — 폰트, 색, 위치, 최대 글자 수, 강조 배율.
  한 번 정한 뒤로는 "자막 지난번이랑 똑같이"로 이 파일을 그대로 재사용
- **하지 말 것 목록**: `default_style.json`의 `dont_touch` 배열에 계속 추가.
  (예: "색은 절대 건드리지 마", "배경음악은 넣지 마")

영문 자막(위)을 쓰려면 `make_captions.py --translations translations.json`으로
세그먼트 순서에 맞는 영어 문장 배열을 전달한다. 번역 자체는 클로드가 대본을 보고
먼저 만든다 — 스크립트는 번역하지 않는다.

## 최종 검수 규칙

**모든 작업은 `qc_check.py`를 통과한 뒤에만 사용자에게 결과물을 보여준다.**
일치율이 기준(85%) 밑이면 사람한테 가져가지 말고 원인(무음 컷이 과했는지,
whisper가 대사를 잘못 알아들었는지)을 스스로 찾아 다시 처리한다.

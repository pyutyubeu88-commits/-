---
name: 숏폼편집
description: 숏폼/릴스 영상을 자연어 한 줄 지시로 무료 로컬 도구(ffmpeg+whisper+HyperFrames)로 자동 편집한다 (컷편집, 세로 리프레임, 질문배너/로고, 자막, 모션그래픽, B-roll 삽입, 효과음). "이 영상 편집해줘", "자막 붙여줘", "세로로 바꿔줘", "배너 애니메이션 넣어줘", "숏폼 자동화" 같은 요청에 사용.
---

# 숏폼 자동 편집

**로컬 전용 스킬**. ffmpeg + whisper로 실제 영상 파일을 처리하므로, 영상 파일과 ffmpeg가 있는
로컬 Claude Code(또는 Cowork 데스크톱)에서 돌아간다. 컷편집·리프레임·자막처럼 whisper가 필요한
단계는 클라우드 세션에서 테스트를 못 했으니, 로컬에서 처음 쓸 때 `## 로컬 세팅` →
`## 스모크 테스트`부터 먼저 돌려서 확인할 것.
(모션그래픽 단계는 클라우드에서 실제 렌더·합성까지 검증했다 — `## HyperFrames 연동` 참고)

## 요청 문장 → 처리 방식

| 단계 | 예시 요청 | 처리 방식 | 상태 |
|---|---|---|---|
| 1. 컷 편집 | "이 영상 편집해줘. 빈 공간 다 없애고, 같은 말 여러 번 한 데는 마지막 것만 써. 1.1배속으로." | `scripts/cut_edit.py` (whisper 받아쓰기 → 무음/재테이크 감지 → ffmpeg 컷+배속) | 로컬에서 바로 가능 |
| 2. 화면 리프레임 | "가로 찍은 거 세로로. 얼굴 따라가면서 잘라." | `scripts/reframe_vertical.py` (opencv 얼굴 검출 → ffmpeg 동적 크롭, 1080x1920 출력) | 로컬에서 가능, 얼굴 인식 정확도는 케이스마다 확인 필요 |
| 3. 상단 질문 배너 + 로고 워터마크 | "위에 질문 고정으로 띄우고, 로고 박아줘." | `scripts/add_branding.py` (ffmpeg drawtext/drawbox, 영상 처음부터 끝까지 고정) | 로컬에서 바로 가능, 한글 폰트 파일(.ttf) 경로 필요 |
| 3-M. 배너/로고 **모션** 버전 | "배너 슬라이드로 내려오게 해줘.", "로고 등장 애니메이션 넣어줘." | `scripts/hyperframes_branding.py` (HyperFrames로 알파 클립 렌더 → ffmpeg overlay) | **Node.js 22+ 필요**. 없으면 3번 정적 버전 그대로 쓴다 |
| 4. 자막 | "자막 붙여줘. 검정 박스에 흰 글씨, 한 줄로, 안 들어가면 대사 쪼개." | `scripts/make_captions.py` (whisper → 스타일 프리셋 적용 ASS → ffmpeg 번인, 1080x1920 캔버스) | 로컬에서 바로 가능 (영문 자막은 번역 파일 필요, 아래 참고) |
| 4-M. 자막 강조 **모션** | "강조 부분에 밑줄 그어지게 해줘.", "형광펜 칠해지는 느낌으로." | `scripts/hyperframes_emphasis.py` (밑줄/형광펜이 좌→우로 그려지는 애니메이션을 자막 위에 얹음) | **Node.js 22+ 필요**. 반드시 자막(4번) **다음**에 실행 |
| 4-G. 화면 그래픽 | "스케일링 전/후 비교 그래프로 보여줘.", "숫자 카드 띄워줘." | `scripts/hyperframes_graphic.py` (막대가 자라는 비교 차트/트리비아 카드를 구간에만 오버레이) | **Node.js 22+ 필요**. 예전엔 "자동화 어려움"으로 뺐던 단계 — 되살렸다 |
| 5. 배경 지우기 | (이 프로젝트는 미사용 — 필요해지면) | Higgsfield `remove_background` | **Higgsfield 커넥터 인증 필요**, 유료 크레딧 |
| 6. 없는 장면 대체 | "이 대사에 붙일 장면 없어. B-roll 끼워줘." | `scripts/insert_broll.py` (직접 찍은 컷 또는 무료 스톡 클립을 지정 구간에 덮어씌움, 나레이션은 안 끊김) | **로컬 무료** — AI 생성 대신 진짜 클립 사용 |
| 7. 효과음 | "효과음 넣어줘. 목소리보다 작게, 자막 뜨는 순간에 맞춰." | `scripts/add_sfx.py` (무료 SFX 파일을 타이밍 맞춰 ffmpeg로 합성) | **로컬 무료** — AI 생성 대신 무료 라이브러리 소스 |
| 8. 최종 검수 | "결과물 폴더 열어주고, 완성본 다시 받아 적어서 대본이랑 맞는지 봐줘." | `scripts/qc_check.py` (whisper 재검증 → 대본 대조) | 로컬에서 바로 가능 — **매 작업 마지막에 반드시 실행** |

파이프라인 순서:
**컷편집 → 리프레임 → 브랜딩(정적 또는 모션) → B-roll 삽입 → 화면 그래픽 → 효과음 → 자막 → 자막 강조 모션 → QC**.

자막은 항상 뒤쪽(QC 직전)에 입혀야 다른 단계에서 화면이 밀리거나 바뀌어도 자막 타이밍이 안 어긋난다.
자막 강조 모션(`hyperframes_emphasis.py`)만 자막보다 뒤에 온다 — 이미 번인된 자막 글자 위에
밑줄/형광펜만 얹는 거라 **영상 길이도 음성도 안 바뀌고**, 그래서 타이밍이 어긋날 일이 없다.
`hyperframes_graphic.py`도 마찬가지로 오버레이라 길이를 안 바꾼다 (`insert_broll.py`처럼
구간을 잘라 끼우는 게 아니다).

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

즉 "완전 자동"이 되는 건 컷편집/리프레임/배너·로고/자막/모션그래픽/QC고, **대본 구조와 B-roll 선정은
클로드가 매번 판단**해야 하는 영역이다.

> 2026-09-03 업데이트: 배너·로고·자막 강조는 이제 정적 번인 말고 **모션 버전**도 있다.
> 예전에 "자동화 어려움"으로 뺐던 **화면 그래픽(비교 차트/트리비아)** 단계도 되살렸다.
> 전부 `## HyperFrames 연동` 참고 — 여전히 무료·로컬이다.

## HyperFrames 연동 (모션그래픽)

정적 번인(drawtext/ASS)으로는 못 하던 것 — 배너가 내려오고, 로고가 닦이며 나타나고,
밑줄이 그어지고, 막대가 자라는 — 을 담당한다.

### 왜 이게 "전부 무료 로컬" 원칙을 안 깨는가

[HyperFrames](https://github.com/heygen-com/hyperframes)는 **Apache 2.0 완전 오픈소스**다.
HTML을 헤드리스 크롬으로 프레임 단위로 찍어서 ffmpeg로 인코딩하는 렌더러일 뿐이라
**API 키도, 계정도, 크레딧도 필요 없다.** 네트워크는 처음 설치할 때(npm 패키지 + 크롬 바이너리)만
쓰고, 그 뒤로는 전부 내 컴퓨터에서 돈다. Higgsfield 같은 유료 생성 AI가 아니다.

### 로컬 세팅 (처음 한 번)

```bash
node --version    # v22 이상이어야 한다. 없으면 https://nodejs.org 에서 LTS 설치
npx hyperframes@0.8.26 doctor          # 환경 점검
npx hyperframes@0.8.26 browser ensure  # 렌더용 크롬(약 114MB) 1회 다운로드
```

`doctor`에서 **FFmpeg / FFprobe / Chrome** 세 줄만 ✓면 된다.
(whisper-cpp, Kokoro, MusicGen, Docker는 이 스킬에서 안 쓰므로 ✗여도 무관)

`npx`는 매번 패키지를 확인하므로, 자주 쓸 거면 `npm i -g hyperframes@0.8.26` 해두고
`HYPERFRAMES_CMD=hyperframes` 환경변수를 걸면 더 빠르다.

### 정적 버전 vs 모션 버전 — 언제 뭘 쓰나

| 상황 | 쓸 것 |
|---|---|
| Node.js가 없다 / 빨리 뽑아야 한다 | `add_branding.py` (정적, ffmpeg만) |
| 인스타 릴스 본편 — 첫인상이 중요 | `hyperframes_branding.py` (모션) |
| 자막 강조를 글자 확대로만 | `make_captions.py`의 `**` 마커 (기본) |
| 강조를 밑줄/형광펜 모션으로 | `hyperframes_emphasis.py` |
| 비교 수치를 보여줘야 한다 | `hyperframes_graphic.py` |

**정적 스크립트는 하나도 안 건드렸다.** Node 없는 환경에서도 기존 파이프라인이 그대로 돈다.
모션 스크립트는 Node가 없으면 "add_branding.py를 쓰라"고 안내하고 멈춘다.

### 어떻게 합성되나 (설계)

1. `templates/*.html`에 실제 값(질문 텍스트, 색, 좌표, 애니메이션 타이밍)을 채워
   임시 HyperFrames 프로젝트를 만든다
2. `hyperframes render --format mov` → **ProRes 4444 (yuva444p10le), 알파 채널 있는** 클립
3. `ffmpeg overlay`로 원본 위에 얹는다. 원본 화질·길이·음성은 그대로

크로마키(colorkey)는 안 쓴다 — HyperFrames가 진짜 알파를 내주므로 색 빠짐이 없다.
`--format webm`(VP9+알파), `--format png-sequence`(RGBA 프레임)도 지원하지만
ffmpeg 합성에는 MOV가 가장 안전해서 그걸 고정으로 쓴다.

배너/로고는 등장 애니메이션이 끝나면 어차피 고정이라, 40초를 통째로 렌더하지 않고
`--anim-duration`(기본 2초)만 렌더한 뒤 `tpad=stop_mode=clone`으로 마지막 프레임을
끝까지 붙잡는다. **렌더 시간이 20배쯤 줄어든다.**

### 스타일 조정

`presets/default_style.json`에 `motion` 섹션을 새로 넣었다 (`branding` / `emphasis` / `graphic`).
기존 키는 하나도 안 바꿨고, 정적 스크립트는 `motion`을 읽지 않는다.
색·좌표·글자 크기는 기존 `branding` 값을 **그대로 재사용**하므로 정적 버전과 모션 버전의
디자인이 어긋나지 않는다. 애니메이션 속도/지연만 `motion.branding`에서 조절한다.

레이아웃을 눈으로 보며 고치고 싶으면 `--keep-project ./hf_banner`로 프로젝트를 남긴 뒤
그 폴더에서 `npx hyperframes preview` → 브라우저에서 실시간 편집.

### 클라우드 세션에서 어디까지 확인했나 (2026-09-03)

지어낸 것 없이 실제로 돌려서 확인한 것:

- `npm install hyperframes@0.8.26` 설치 성공, `browser ensure`로 크롬 헤드리스 셸 다운로드 성공
- `--format mov` 렌더 결과가 **정말 알파를 갖는다** — `pix_fmt=yuva444p12le`,
  투명 영역 픽셀이 `(0,0,0,0)`으로 나오는 것까지 프레임 단위로 확인
- **GSAP 없이 순수 CSS `@keyframes`만으로 프레임별 시킹이 된다** (런타임에 CSS/WAAPI 어댑터가 있다).
  그래서 템플릿이 외부 CDN을 전혀 안 쓴다 = 인터넷 없이도 렌더된다
- 루트에 `data-no-timeline`이 없으면 렌더마다 45초를 그냥 기다린다 → 템플릿 3개 모두 넣었고,
  `hyperframes lint` 결과 **0 errors, 0 warnings**
- 배너/로고/밑줄/형광펜/비교차트 전부 실제로 렌더 → ffmpeg 합성 → 출력 프레임 픽셀로 검증.
  음성 스트림과 길이(40.000s)가 그대로 유지되는 것도 확인

로컬에서 처음 쓸 때 확인할 것: **한글 폰트**(Pretendard 등 실제 .ttf 경로)로 글자가 깨지지 않는지,
그리고 자막 강조 밑줄이 실제 자막 글자 아래에 정확히 붙는지 (`korean_size` / `korean_margin_v` /
`--font`가 `make_captions.py`에 쓴 것과 같아야 한다).

## 로컬 세팅 (처음 한 번)

```bash
brew install ffmpeg   # 또는 apt install ffmpeg
pip3 install -r .claude/skills/숏폼편집/requirements.txt
# 모션그래픽을 쓸 거면 위 "HyperFrames 연동 → 로컬 세팅"도 같이
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

모션그래픽(HyperFrames)까지 쓸 때:

```bash
# 3-M. 배너/로고를 정적 대신 모션으로 (add_branding.py 자리에 그대로 대체)
python3 .claude/skills/숏폼편집/scripts/hyperframes_branding.py test_vert.mp4 test_branded.mp4 \
    --question "동양인과 서양인" "치아 구조가 다른가요?" --logo "SMILE VIEW" "DENTAL" \
    --font /path/Pretendard-Bold.ttf --anim-duration 2.0

# 4-G. 화면 그래픽 (비교 차트) — 자막 넣기 전
python3 .claude/skills/숏폼편집/scripts/hyperframes_graphic.py test_broll.mp4 test_graphic.mp4 \
    --data chart.json --at 12.5 --duration 4 --font /path/Pretendard-Bold.ttf

# 4-M. 자막 강조 모션 — 반드시 make_captions.py 다음, qc_check.py 앞
python3 .claude/skills/숏폼편집/scripts/hyperframes_emphasis.py test_final.mp4 test_emph.mp4 \
    --cues cues.json --font /path/Pretendard-Bold.ttf
python3 .claude/skills/숏폼편집/scripts/qc_check.py test_emph.mp4 test_script.txt
```

`cues.json` / `chart.json` 형식은 각 스크립트 상단 docstring에 있다.
둘 다 클로드가 대본을 보고 만들어준다.

## 처음 한 번만 정하면 되는 것

- **폴더 구조**: `output/{날짜}_{주제}/` — 원본, 중간 산출물, 최종본을 매번 같은 구조로
- **자막 스타일**: `presets/default_style.json` — 폰트, 색, 위치, 최대 글자 수, 강조 배율.
  한 번 정한 뒤로는 "자막 지난번이랑 똑같이"로 이 파일을 그대로 재사용
- **모션 스타일**: 같은 파일의 `motion` 섹션 — 배너 슬라이드 속도, 밑줄 색·두께, 차트 카드 색.
  "모션 지난번이랑 똑같이"도 이 파일 하나로 재사용된다
- **하지 말 것 목록**: `default_style.json`의 `dont_touch` 배열에 계속 추가.
  (예: "색은 절대 건드리지 마", "배경음악은 넣지 마")

영문 자막(위)을 쓰려면 `make_captions.py --translations translations.json`으로
세그먼트 순서에 맞는 영어 문장 배열을 전달한다. 번역 자체는 클로드가 대본을 보고
먼저 만든다 — 스크립트는 번역하지 않는다.

## 최종 검수 규칙

**모든 작업은 `qc_check.py`를 통과한 뒤에만 사용자에게 결과물을 보여준다.**
일치율이 기준(85%) 밑이면 사람한테 가져가지 말고 원인(무음 컷이 과했는지,
whisper가 대사를 잘못 알아들었는지)을 스스로 찾아 다시 처리한다.

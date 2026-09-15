# 인수인계 — 숏폼 자동편집 스킬 + 스마일뷰 치과 작업

> 이 파일은 클라우드 세션(웹)에서 진행한 작업을 로컬 Claude Code 터미널이 바로 이어받게 하려고 쓴
> 1회성 인수인계 문서다. 스킬 자체의 사용법은 `.claude/skills/숏폼편집/SKILL.md`가 정본이고,
> 여긴 "지금 어디까지 왔고 다음에 뭘 해야 하는지"만 담는다. 작업 끝나면 지워도 된다.

**브랜치**: `claude/insta-thread-shortform-captions-qdjied` (main 미머지 — 로컬에서 이 브랜치로 시작할 것)
**클라이언트**: 스마일뷰 치과 (SMILE VIEW DENTAL)

```bash
git fetch origin claude/insta-thread-shortform-captions-qdjied
git checkout claude/insta-thread-shortform-captions-qdjied
```

---

## 1. 이 브랜치에서 뭘 만들었나

클로드 코드로 숏폼(릴스/쇼츠)을 자연어 한 줄 지시로 편집하는 스킬을 처음부터 만들었다.
`.claude/skills/숏폼편집/` — 전부 **로컬·무료** (ffmpeg, whisper, opencv, HyperFrames 전부 오픈소스,
유료 API는 Higgsfield뿐이고 이 프로젝트는 안 씀).

| 스크립트 | 역할 | 필요환경 |
|---|---|---|
| `cut_edit.py` | 무음구간·재테이크 자동 제거, 배속 | ffmpeg, whisper |
| `reframe_vertical.py` | 가로→세로(9:16), 얼굴 추적 크롭 | ffmpeg, opencv |
| `add_branding.py` | 상단 질문배너+로고 (정적 번인) | ffmpeg |
| `hyperframes_branding.py` | 위와 같은 것의 **애니메이션 버전** | ffmpeg, Node 22+ |
| `insert_broll.py` | B-roll을 나레이션 안 끊고 지정 구간에 삽입 | ffmpeg |
| `hyperframes_graphic.py` | 비교차트/트리비아 카드 애니메이션 오버레이 | ffmpeg, Node 22+ |
| `add_sfx.py` | 무료 SFX를 타이밍 맞춰 합성 | ffmpeg |
| `make_captions.py` | whisper 자막 → 스타일 프리셋 적용 ASS 번인 | ffmpeg, whisper |
| `hyperframes_emphasis.py` | 자막 강조를 밑줄/형광펜 모션으로 (자막 **다음**에 실행) | ffmpeg, Node 22+ |
| `qc_check.py` | 완성본 재검증 → 대본과 85% 미만 불일치면 통과 금지 | ffmpeg, whisper |

**파이프라인 순서**: 컷편집 → 리프레임 → 브랜딩 → B-roll → 화면그래픽 → 효과음 → 자막 → 자막강조모션 → QC

### 로컬 세팅 (처음 한 번)
```bash
brew install ffmpeg   # 또는 apt install ffmpeg
pip3 install -r .claude/skills/숏폼편집/requirements.txt   # whisper, opencv

# 모션그래픽(HyperFrames)을 쓸 거면 추가로:
node --version   # 22 이상 필요, 없으면 nodejs.org에서 LTS 설치
npx hyperframes@0.8.26 doctor
npx hyperframes@0.8.26 browser ensure   # 렌더용 크롬 1회 다운로드(~114MB)
```

---

## 2. 지금 진행 중인 실제 작업 — 스마일뷰 치과

### 2-1. 레퍼런스 분석 (업로드받은 릴스: "동양인과 서양인 치아 구조가 다른가요?", 9:16 720x1280, 39.5초)
- 상단 고정 배너("Q."+질문 2줄, 흰 배경, 1줄 검정/2줄 파랑), 영상 끝까지 안 바뀜
- 하단 자막: 불투명 검정 박스 + 흰 굵은 글씨
- 하단좌측 로고 워터마크: "SMILE VIEW" / "DENTAL"
- 훅 구조: 결론 먼저("네 많이 다릅니다") → 이유 설명
- B-roll 컷인 2곳 — **정확한 타이밍 실측 완료**:
  - 17.0s ~ 24.5s (7.5초): 구강/악궁 비교 사진
  - 26.5s ~ 28.5s (2.0초): 소아 환자 진료 장면

### 2-2. 이 레퍼런스 영상 자체를 완성하려면 (음성 그대로 유지, 진짜 Pixabay로 B-roll만 교체)
클라우드 세션에서 플레이스홀더로 `insert_broll.py` 동작을 이미 검증 완료 (39.49초 길이 유지, 음성 안 끊김,
정확한 구간만 교체됨 확인). Pixabay는 클라우드 세션 정책상 접근 불가해서 로컬에서 마무리해야 한다.

```bash
# Pixabay 검색어: "teeth closeup" / "dental x-ray" (1번 구간), "pediatric dentist" / "dental exam child" (2번 구간)
python3 .claude/skills/숏폼편집/scripts/insert_broll.py \
    원본.mp4 pixabay_치아클립.mp4 step1.mp4 --at 17.0 --duration 7.5
python3 .claude/skills/숏폼편집/scripts/insert_broll.py \
    step1.mp4 pixabay_진료클립.mp4 final.mp4 --at 26.5 --duration 2.0

ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 final.mp4
# → 39.49초 나오면 정상
```

### 2-3. 신규 대본 초안 — "스케일링 자주 하면 이가 벌어지나요?" (아직 촬영 전)

터질만한 주제로 클로드와 같이 짠 대본. 레퍼런스와 같은 Q&A/훅 구조.

**상단 배너**: `스케일링 자주 하면` / `이가 벌어지나요?`
**로고**: `SMILE VIEW` / `DENTAL`

| 타임 | 대사 | 화면 |
|---|---|---|
| 0~3s | "아니요, **오히려 반대예요.**" | 정면샷 (결론 먼저) |
| 3~8s | "이가 벌어져 보이는 건, 원래 있던 틈을 치석이 메우고 있었던 거예요." | 정면샷 |
| 8~14s | "스케일링으로 그 치석을 없애니까, **가려져 있던 틈이 드러나는 것**뿐이에요." | B-roll: 치석 낀 치아 → 스케일링 후 |
| 14~20s | "오히려 스케일링을 안 하면 치석이 계속 쌓여서, **잇몸병으로 이가 흔들리고 빠질 위험**이 커져요." | 정면샷 |
| 20~26s | "그래서 저희는 6개월에 한 번은 꼭 받으시라고 말씀드려요." | 정면샷 |
| 26~30s | "스케일링 미루고 계셨다면, 이 영상 저장해두고 예약부터 잡으세요." | 정면샷 + 로고 강조 |

**B-roll 촬영 리스트(미촬영)**: 치석 낀 치아 클로즈업, 스케일링 시술 장면, 스케일링 후 깨끗한 치아 클로즈업
(직접 촬영 못 하면 Pixabay "dental scaling" / "teeth cleaning"으로 대체 가능)

**다음 할 일**: 원장님이 이 대본으로 실제 촬영 → `cut_edit.py`부터 파이프라인 순서대로 돌리면 됨.

---

## 3. 열린 결정사항 — 로컬에서 확인/판단 필요

1. **한글 폰트 실물 미검증**: HyperFrames 렌더는 클라우드에서 유니폰트(비트맵)로만 테스트함.
   Pretendard 실제 폰트로 배너/자막 줄간격이 깨지지 않는지 로컬에서 한 번 확인할 것.
2. **자막 강조 밑줄 정렬**: `hyperframes_emphasis.py`를 밑줄 모드로 쓸 거면 `presets/default_style.json`의
   `emphasis_scale`을 130(기본값, 글자확대용) 대신 100으로 낮추는 게 밑줄과 안 어긋난다 — 에이전트 권고,
   기본값은 아직 안 바꿔뒀음. 실제로 렌더해보고 결정할 것.
3. **`hyperframes_graphic.py`의 scrim**: 기본 `true`라 카드 뒤 화면 전체(상단 Q배너 포함)가 어두워짐.
   의도된 동작이지만 배너까지 어두워지는 게 싫으면 `chart.json`에 `"scrim": false` 추가.

## 4. 무료 소스 (B-roll/효과음/폰트)

| 용도 | 사이트 |
|---|---|
| 효과음 | [Pixabay Sound Effects](https://pixabay.com/sound-effects/), [Mixkit](https://mixkit.co/free-sound-effects/) |
| B-roll 스톡 | [Pexels Videos](https://www.pexels.com/videos/), [Pixabay Videos](https://pixabay.com/videos/) |
| 한글 폰트 | [Pretendard](https://github.com/orioncactus/pretendard) (SIL OFL, 상업적 이용 무료) |

## 5. 참고 — 클라우드 세션에서 확인한 이 환경 고유의 제약 (로컬에선 대부분 해당 없음)

- instagram.com, threads.com, pixabay.com, github.com raw 전부 이 클라우드 세션 정책상 접근 차단됨
  (로컬은 정상 접근 가능 — 이 스킬을 쓰는 데 지장 없음)
- pip로 설치되는 `imageio-ffmpeg` 정적 바이너리는 drawtext 필터가 빠져있었음
  (로컬 brew/apt ffmpeg는 정상 포함, 문제 없음)

# 프로젝트 메모리

> 이 파일은 세션 간 컨텍스트를 유지하기 위한 파일메모리입니다.
> Claude가 세션 시작 시 자동으로 읽고, 중요한 정보를 여기에 저장합니다.

## 프로젝트 개요
- **프로젝트명**: AI 자동 대댓글 생성기
- **설명**: 링크를 넣으면 댓글을 불러오고 자동으로 대댓글을 생성하는 프로그램
- **주요 파일**: `index.html` (단일 파일 앱)
- **언어**: 한국어

## 주요 결정사항
<!-- 중요한 기술적 결정사항을 여기에 기록하세요 -->

## 진행 중인 작업
<!-- 현재 진행 중이거나 미완료된 작업을 여기에 기록하세요 -->

## 메모
<!-- 기타 기억해야 할 정보를 여기에 기록하세요 -->


### [2026-06-03 04:19] 코드 리뷰 결과 → [2026-06-06] 완료
- ✅ OAuth 토큰 localStorage → 메모리 전용으로 변경 (보안 수정)
- ✅ Gemini API 상태코드별 오류 처리 추가 (429/403/400)
- ✅ 일괄 생성 중단 버튼 구현 + startBulk() 잘린 코드 복구

### [2026-06-06] SNS 전략 기획
- 강남구 AI 컨설턴트 (권용준) SNS 포지셔닝 전략 수립
- 첫 컨설팅 사례: 역삼효태권도장
- 주요 플랫폼: 인스타그램(1순위) → 네이버블로그 → 유튜브쇼츠 → 카카오채널
- 핵심 포지셔닝: "강남구 소상공인을 AI로 직접 바꾸는 현장 컨설턴트"
### [2026-06-14] 강남구 AI 컨설팅 사업 랜딩페이지 제작
- 공고(이미지) 기반 사업 소개 웹페이지 `program.html` 신규 작성
- 사업명: 2026년 강남구 중장년 AI 전문가 양성 및 맞춤형 AI컨설팅 사업
- 주최: 강남구(일자리정책과) / 주관: (주)상상우리
- 핵심: 강남구 소상공인 대상 전액 무료 1:1 AI 컨설팅·멘토링
- 신청 2026.5.4~11.27(상시), 운영 6.8~12.11(예정), 온·오프라인 병행
- 문의: 02-2274-7762 / hspark@gangnamconsulting.com
- 구성: Hero→통계바→사업안내→지원내용→신청대상→5단계 절차→일정/장소→신뢰배너→FAQ→신청CTA→공식 푸터
- 디자인: profile.html 그린 테마 계승, 스크롤 리빌·FAQ 아코디언·모바일 하단 고정 CTA
- vercel.json 루트(/)를 program.html로 변경, /consultant→profile.html 추가

### [2026-06-14] 배포 구조 변경 (Vercel 파일 우선순위 이슈 대응)
- 문제: Vercel은 rewrites보다 실제 파일을 우선 → 루트의 index.html(대댓글생성기)이 항상 떠서 사업페이지 안 보임
- 추가 문제: Vercel 프로덕션이 3월 18일 커밋(85d2)에 고정, 이후 main 푸시를 자동배포 안 함
- 조치: program.html → index.html(사업 소개 페이지를 루트로), 기존 대댓글생성기 index.html → reply.html
- vercel.json: /consultant→profile.html, /reply·/comment→reply.html
- 대댓글 생성기 접속 주소: /reply.html (또는 /reply)

### [2026-06-14] 운영기관(상상우리) 피드백 반영 + 배포처 확인
- 신청대상: 소상공인 위주 부각(대형 강조카드), 창업·취업희망자+디지털취약계층은 "그 외 신청 가능" 기타로 통합·축소
- 지원내용: 실제 업무 중심 재구성 → ①매출확대 마케팅 전략 수립 ②AI 도구 도입·활용을 통한 매장 운영·홍보 ③온라인·SNS 홍보 실행
- 배포처 확인: aiconsultant-two.vercel.app 이 저장소(pyutyubeu88-commits/-) main과 연결됨 → push 시 자동 배포

### [2026-06-22] AI 프롬프트 e북 판매 사업 계획서 작성
- 신규 사업: 강남구 AI 컨설팅 연계 "소상공인 AI 프롬프트북" e북 판매
- 문서: `ebook-business-plan.md` (전체 사업 계획서 v1.0)
- 핵심 전략: e북 = 컨설팅으로 가는 입구(미끼) + 패시브 인컴
- 가격 사다리: 무료 미니북(리드) → 메인 e북 14,900~29,000원 → 노션 템플릿 49,000원 → 1:1 컨설팅
- 타겟: 좁고 구체적으로 (업종별 - 태권도/헬스/요식/미용), 1차는 컨설팅 만난 업종부터
- 차별점: [복붙 프롬프트]+[빈칸]+[실제 출력 예시] 3종 세트 → 무료 ChatGPT와 차별화
- 채널: 자체 랜딩페이지(주력)+크몽(보조)+인스타/블로그(유입)
- 다음 액션 후보: e북 판매 랜딩페이지(/ebook), 무료 미니북 리드 수집 폼
- 사용자 선택: "전체 사업 계획서" (AskUserQuestion)

### [2026-06-22] e북 판매 랜딩페이지 제작
- 파일: `ebook.html` (단일 파일, profile.html 그린 테마 계승 + 골드 포인트 --acc:#FFB703)
- 구성: Hero→통계바→Pain(공감)→차별점(복붙+빈칸+예시 3종 세트 실제 샘플)→구성(4챕터 TOC)→가격(3티어: 무료미니북/메인19,000원/패키지49,000원)→후기→무료미니북 리드폼→FAQ아코디언→최종CTA→푸터
- 인터랙션: 스크롤 리빌(IntersectionObserver), FAQ 아코디언, 모바일 하단 고정 CTA, 스크롤스파이
- 결제: BUY_LINKS 변수(ebook/pack)에 크몽·스마트스토어·토스 URL 넣으면 연결, 비어있으면 메일 구매문의로 폴백
- 리드폼: 이메일 입력 → mailto로 무료 미니북 신청 (추후 실제 폼/자동화로 교체 가능)
- 연락 이메일: yjkwon@gangnamconsulting.com (profile.html과 동일)
- vercel.json: /ebook, /prompt → ebook.html 라우팅 추가
- TODO(사용자): 실제 결제 URL 확보 후 BUY_LINKS 채우기, 실제 후기 수집, 미니북 PDF 제작

### [2026-06-22] e북 사업 PR #7 머지·배포
- PR #7 (계획서 ebook-business-plan.md + 랜딩 ebook.html + vercel.json /ebook 라우팅) squash 머지 완료 → main 반영
- 로컬 헤드리스 크로미움으로 데스크톱/모바일 렌더링 검증 완료 (정상)
- Vercel 자동 배포: main 연결되어 머지 시 자동 배포 (aiconsultant-two.vercel.app/ebook)
- 주의: 실행 환경에서 vercel 도메인 outbound 차단됨(x-deny-reason: host_not_allowed) → 라이브 URL은 사용자가 직접 확인 필요. 루트 / 도 동일 차단이므로 사이트 문제 아님

### [2026-06-22] ★Vercel 자동배포 안 되던 진짜 원인 규명·해결★
- 증상: main 머지·푸시해도 aiconsultant-two.vercel.app/ebook 이 404 (옛 페이지만 뜸)
- 진짜 원인: aiconsultant 프로젝트(=aiconsultant-two.vercel.app)가 **GitHub에 연결 안 돼 있었음**. 프로덕션이 6/14 "Vercel Drop"(수동 업로드)에 고정. → GitHub push가 도달 못 함
- (참고) GitHub 저장소(pyutyubeu88-commits/-)는 엉뚱하게 'auto' 프로젝트(auto-delta-five.vercel.app)에 연결돼 있었고 그건 3/18 고정. 과거 "3월 18일 커밋 고정" 메모가 이 프로젝트였음
- 해결: 사용자가 Vercel → aiconsultant → Settings → Git 에서 pyutyubeu88-commits/- 저장소 연결(Production Branch=main). "Connected just now" 확인
- 연결 후 첫 배포 트리거: main에 빈 커밋(37760fb) 푸시 → 자동 배포 시작
- ⚠️주의(향후): 로컬에 오래된 별개 'main' 브랜치(e6ee911/d60ead3 계열, ebook 없음)가 존재함. main 작업 시 반드시 `git reset --hard origin/main`으로 origin 기준 맞출 것. 진짜 origin/main 은 b738706(e북 포함)
- 이제부터 main push 시 aiconsultant-two.vercel.app 자동 배포 정상화됨

### [2026-06-22] e북 실메일 전송 + 결제링크 연결 구현
- 사용자 선택(AskUserQuestion): 결제=결제링크 연결(외부 URL), 메일=Web3Forms 무료
- ebook.html 스크립트 상단에 ⚙️설정 블록 3개: WEB3FORMS_ACCESS_KEY / BUY_LINKS(ebook,pack) / CONTACT_EMAIL
- sendMail(): fetch로 api.web3forms.com/submit POST (백엔드 불필요, 정적 사이트 그대로 작동). 성공 시 true
- submitLead(): Web3Forms로 미니북 신청 실제 메일 전송, 키 미설정/실패 시 mailto 폴백. 버튼 로딩상태 처리
- 구매버튼: BUY_LINKS[key] 있으면 새탭 결제페이지, 없으면 알림+미니북 폴백
- 헤드리스 검증: JS문법 OK, 이메일검증/구매버튼 알림 정상
- ★사용자 활성화 TODO(이거 해야 실제 작동):
  1) web3forms.com 에서 받을이메일 입력→액세스키 발급→ebook.html WEB3FORMS_ACCESS_KEY 에 붙여넣기
  2) 검로드/페이팔/스마트스토어 등에서 e북 상품 만들고 결제URL을 BUY_LINKS.ebook / .pack 에 넣기
- 키/링크는 ebook.html 안에 직접 들어감 → 사용자가 알려주면 Claude가 대신 넣어줄 수 있음

### [2026-06-22] ★Web3Forms 키 발급·연결 완료★
- 사용자가 web3forms.com 가입(yjkwon@gangnamconsulting.com)·이메일 인증·첫 폼 생성 완료
- 발급 액세스 키: bb7f3432-7a1d-4f1a-8710-68e88e40e2ca → ebook.html WEB3FORMS_ACCESS_KEY 에 입력
- PR #9로 main 머지 → aiconsultant-two.vercel.app/ebook 라이브 반영
- 남은 TODO: ① 결제 URL(BUY_LINKS.ebook/.pack) 확보 ② 미니북/메인 e북 PDF 콘텐츠 제작

### [2026-06-22] ★미니북 즉시 다운로드 완성 (PDF 자체 제작·배포)★
- Web3Forms 자동답장은 Pro($12/월) 유료 → 무료 "신청 즉시 다운로드" 방식 채택(사용자 AskUserQuestion)
- ebook.html: MINIBOOK_URL='/minibook.pdf' 연결. 신청 성공 시 성공박스에 "📘 무료 미니북 다운로드" 버튼 노출(링크 비면 메일 폴백)
- ★Claude가 PDF 직접 제작★: minibook-print.html(디자인 HTML) → 헤드리스 크로미움(/opt/pw-browsers/chromium-1194)으로 print-to-pdf → minibook.pdf (13p)
  - 한글 폰트: github noto-cjk에서 NotoSansKR-VF.ttf 다운로드→~/.fonts 설치→fc-cache. 이모지=Noto Color Emoji(기설치)
  - 검증: 헤드리스 스크린샷으로 표지·카드 렌더링 확인(한글/이모지/코드블록 정상)
  - 구글드라이브 불필요 → 사이트 루트에 minibook.pdf 두고 /minibook.pdf 로 직접 제공(Vercel 정적)
- minibook-content.md: 미니북 텍스트 원고(프롬프트 10개). minibook-print.html 수정 후 재렌더링하면 PDF 갱신
- PDF 재생성 명령: chromium --headless --no-sandbox --print-to-pdf=minibook.pdf --no-pdf-header-footer file://.../minibook-print.html
- PR #10으로 main 머지 → /ebook 즉시다운로드 라이브
- 남은 TODO: ① 결제 URL(BUY_LINKS.ebook/.pack) ② 메인 e북(80개) 본편 제작

### [2026-06-22] 미니북에 보너스 프롬프트 추가 (네이버 플레이스 소식 자동화)
- 사용자 요청: "네이버 플레이스 소식란 자동화 프롬프트, 10/10 품질로 포함"
- 추가: 🎁BONUS 프롬프트 — 한 번에 한 달치 소식 8개+발행 캘린더 자동 생성(종류 믹스/지역키워드 SEO/발행시간 추천)
- minibook-print.html: .card.bonus 골드 강조 스타일 + 보너스 카드, 표지 "10 +BONUS 1", 클로징 "맛보기 10개+보너스"
- PDF 15p로 재렌더링·헤드리스 검증 완료. minibook-content.md 동기화. ebook.html 리드 문구에 보너스 명시
- 미니북은 이제 "프롬프트 10개 + 보너스 1개"로 통일

### [2026-06-22] ★메인 e북(유료 상품) 80개 제작 완료★
- 사용자 "순서대로 다 수행" → 남은 ①메인e북 ②결제 중 ①을 Claude가 직접 제작
- product/ebook-full.html → 헤드리스 크로미움 렌더 → product/ebook-full.pdf (50페이지, 80개 프롬프트)
- 구성: 표지(80 REAL-WORLD PROMPTS) + 들어가며 + 목차 + 8챕터×10개 + 클로징(1:1 컨설팅 CTA)
  - CH1 마케팅·홍보문구 / CH2 SNS콘텐츠 / CH3 네이버플레이스·지역 / CH4 고객응대·단골 / CH5 리뷰·평판 / CH6 매장운영·직원 / CH7 이벤트·프로모션 / CH8 매출·사업전략
- 각 카드: 제목+이럴때+복붙프롬프트+빈칸가이드+출력예시 (미니북과 동일 3종세트, compact)
- ★중요: 저장소가 PUBLIC → 유료상품을 커밋하면 무료 유출. 그래서 .gitignore에 product/ 추가(커밋 안 함). PDF는 SendUserFile로 사용자에게 직접 전달
- 배포 방식: 사용자가 Gumroad/페이히어에 이 PDF 업로드 → 결제 시 자동 전달. 그 결제URL을 ebook.html BUY_LINKS.ebook 에 넣으면 구매버튼 작동
- 재생성: product/ebook-full.html 수정 후 chromium --headless --print-to-pdf (컨테이너는 ephemeral이라 html도 미커밋 → 필요시 이 세션에서 수정/재생성)
- 다음(②): 결제 플랫폼 가입은 사용자 필요 → 단계별 안내 예정

### [2026-06-22] 결제=크몽 전자책, 가격=14,900원 결정 (AskUserQuestion)
- 사용자 선택: 판매처=크몽 전자책, 가격=14,900원(진입용)
- ebook.html 수정: 메인 e북 가격 19,000→14,900, 구성 섹션을 실제 8챕터(각10개)로 갱신, "PDF 50페이지" 명시, "노션 버전" 문구 삭제(실제 미제작), BUY_LINKS 주석 갱신
- kmong-listing.md 작성: 크몽 등록용 제목/카테고리/상세설명/태그/미리보기 가이드 복붙 완성본 (마케팅 카피라 public 커밋 OK)
- ★사용자 할 일: 크몽 가입→전문가 등록→전자책 서비스 등록(위 문구 붙여넣기)→PDF(product/ebook-full.pdf, 사용자 보유) 업로드→심사(1~3일)→서비스 URL 확보
- URL 받으면 BUY_LINKS.ebook 에 넣고 머지 → /ebook '지금 구매하기' 작동
- 제안: 크몽 썸네일·상세이미지도 Claude가 제작 가능(미니북 표지 방식)

### [2026-06-22] 메인 e북 복제방지 1차 적용 (푸터 + 복사잠금)
- 사용자 우려: "PDF면 되팔이·무료공유 못 막지 않냐" → 100% 불가 인정, 미끼+컨설팅 퍼널 전략 설명 + 가벼운 보호 적용(AskUserQuestion: "푸터+복사잠금" 선택)
- ① 저작권 푸터: ebook-full.html에 .pagefoot(position:fixed) 추가 → 전 페이지 하단 "ⓒ 2026 강남구 소상공인 AI 컨설턴트 · 무단 복제·공유·재배포 금지 · 구매자 전용". print 시 fixed가 모든 페이지 반복됨
- ② 복사잠금: pip install pikepdf(10.9.1) → Encryption(owner=랜덤, user='', R=6/AES-256, Permissions(extract=False, modify_*=False, print 허용)). 열기는 비번 불필요, 복사·추출·편집 차단, 인쇄 허용
- 재적용 명령: pikepdf.open(src).save(dst, encryption=pikepdf.Encryption(owner=secrets.token_urlsafe(18), user='', allow=perms, R=6))
- product/ebook-full.pdf = 보호본으로 교체됨(50p). SendUserFile로 사용자에게 전달
- 한계 명시함: 복사잠금은 우회 가능(약한 보호). 진짜 강력한 건 '구매자별 워터마크(수동배달)' → 유출 실제 문제시 2차로 전환 예정
- (옵션) 크몽 자동배달과 병행. 무료 미니북은 보호 불필요(free 리드마그넷)

### [2026-06-22] ★복사잠금 철회 — 상품은 '복붙용 프롬프트'라 복사 허용 필수★
- 사용자 지적: "복사 잠그면 복붙 못 하지 않냐" → 맞음. extract=False는 프롬프트 복붙 불가 = 상품 가치 파괴. Claude 판단 오류 정정
- 수정: pikepdf 재적용 시 Permissions(extract=True ★복사허용, print 허용, modify_*=False 편집만 차단)
- 결과: 구매자 프롬프트 복붙 OK / 인쇄 OK / 문서 편집·재가공만 차단 + 저작권 푸터 유지
- 교훈: 복붙이 핵심 가치인 상품엔 copy-lock 금지. 보호는 푸터(+추후 구매자별 워터마크)로만

### [2026-06-22] 크몽 썸네일·상세이미지 제작
- 사용자 선택(2): 크몽 등록용 이미지 제작
- kmong-img/thumb.html → thumbnail.png (1200x900, 대표이미지): 그린/골드, "소상공인 AI 프롬프트북 복붙만 하면 끝", 80 실전프롬프트, 복붙→빈칸→완성 칩
- kmong-img/detail.html → detail.png (860x3929, 상세페이지): Hero→Pain(3고민)→3종세트 솔루션→실제 샘플카드→8챕터 그리드→스펙→CTA(14,900원/정가29,000)
- 렌더: 헤드리스 크로미움 + Pillow로 하단 흰여백 트리밍(ImageChops getbbox)
- PNG는 SendUserFile로 전달(미커밋, kmong-img html소스만 커밋). 사용자가 크몽 등록 시 업로드

### [2026-06-22] 크몽 포트폴리오 등록용 파일 제작
- 사용자 요청: 포트폴리오 등록 파일
- kmong-img/portfolio.html → portfolio.pdf (3p, A4): ①표지(WORK PORTFOLIO, 권용준 소개+태그) ②작업개요(3종세트+8개분야 범위)+샘플1(재방문문자) ③샘플2(네이버소식자동),3(나쁜리뷰답글)+CTA
- 표지 full-bleed 위해 .cover height:297mm. 헤드리스 크로미움 렌더
- 무료 미니북(minibook.pdf)도 추가 포트폴리오/샘플로 활용 가능

### [2026-07-01] ★재창업 AI 컨설팅 사업 기획 핸드오프 (신규 사업 아이템, 별도 트랙)★
- 배경: 강남구 AI활용컨설턴트(1기) 활동 중 참석한 창업 정부지원사업 특강 녹취록 분석 → 실제 재창업 사업 아이템 기획
- 특강 핵심 사실(근거자료): PMF=Product-Market Fit / 스타트업 5년 생존율 10%,초기아이디어유지율 3% / 데모데이는 하반기(9월~) 통상, 정부지원 공고는 1~2월 집중 / 사업계획서=PSST(Problem-Solution-Scale up-Team) 구조, 요약페이지가 심사 통과 좌우(건당 3~5분 검토) / SOM은 "1년 내 실현 가능 시장"으로 좁혀써야 함(뻥튀기 금지) / 팀구성은 심사위원이 최우선으로 보는 항목, 최소 4명 선호 / AISAS(인지-흥미-검색-행동-공유), 무인지도시 검색광고 우선

**사업 아이템 정의**
- 한줄: AI로 소상공인·중기 맞춤솔루션 + 취업·창업 방향설정 + 크리에이터 수익화 지원 컨설팅 → 자체 AI 툴/SaaS 제품화 추진
- 모듈A(소상공인+중기, 마케팅포함 맞춤AI솔루션): 강남구 무작위매칭=무료(레퍼런스용) / 지인=무료3회 후 즉시 유료전환
- 모듈B(유튜브 크리에이터 콘텐츠·수익화): 처음부터 유료
- 모듈C(취업·창업 방향코칭): 코칭·컨설팅 범위로 한정(직업소개·채용연계까지 가면 유료직업소개사업 허가 필요 — 미해당 확인 필요)
- 차별점(과장 표현 배제, 검증 가능 사실만): 강남구 AI컨설턴트 1기 20인 중 클라이언트 기반을 자체 SaaS로 제품화하려는 시도는 흔치 않음 / 대표 13년 영업경험 + 유사투자자문업 창업·운영경험(3인팀 월매출 1억, 유튜브 실시간 1000명)

**트랙션(현재)**: 강남구 컨설턴트 계약 12월까지 유효, 무료3회 컨설팅 진행중(S&H듀얼왁싱 등, 지인을 강남구 프로그램에 신청시켜 진행). 강남구 무작위배정 고객엔 계약기간 중 유료제안 금지 / 지인은 3회 종료후 유료제안 가능. 월 처리가능 건수·가격은 미정

**팀**: 대표=권용준(확정) / 제품개발(SaaS화)=컨택중, 관심타진 메시지 초안 준비·발송보류 / 정부지원·전략자문=컨택중(오늘 특강 강사, 강남구 동료), 초안준비·발송보류 / 손미현(기존파트너)=이 사업에서 명시적 배제 결정. 원칙: 양쪽에게 상대가 "이미 합류했다"는 거짓말 금지 → "두 분께 동시 컨택 중, 함께하시면 팀 완성" 문구 사용

**법인구조·정부지원 로드맵**: 현재 법인(유사투자자문업)·개인(컨설팅업 무실적) 사업자 모두 폐업 예정 → 순서: ①개인사업자 홈택스 폐업 ②법인 폐업신고 ③법인 해산·청산(해산등기→청산인선임→채권신고공고 최소2개월→청산종결등기, 세무사·법무사 상담 미착수) ④"사업자없음" 확정 후 예비창업패키지 신청(PSST 계획서) ⑤선정시 사업자 재등록=공식 재창업일 ⑥재창업일로부터 1년내 희망리턴패키지 "창업도약형" 추가신청 시도
- 미확인 사항(실행전 검증 필수): 예비창업패키지+희망리턴패키지 창업도약형 중복신청 가능여부(1357 중기부 콜센터 확인 필요) / 강남구 계약서상 지인 배정·동료협업이 계약위반 아닌지 / 모듈C가 유료직업소개사업 허가대상으로 확장 안되게 범위관리

**시장규모(SOM)**: TAM=강남구 사업체 104,551개(2024, 강남구청 조사, 전체사업체 수치이며 소상공인만은 아님)+전국확장 가능성 / SAM=강남구매칭+지인네트워크+유튜브크리에이터시장 / SOM=미확정(월처리건수×12개월로 산출 필요, 본인 확답 대기)

**미해결 TODO(다음 세션 이어갈 것)**:
- [ ] SOM 월 처리가능 건수 확정
- [ ] "억만장자 팀" 관련 과거자료 — 대화검색으로 못찾음, 사용자가 직접 공유 필요(팀구성 섹션 반영 예정)
- [ ] 강사·개발자 컨택 메시지 — 초안 완성, 기획 더 다져진 후 발송
- [ ] PSST 사업계획서 최종본 문서화
- [ ] 가격/상품 구성 설계
- 참고: 이 사업은 기존 강남구 소상공인 AI컨설팅(랜딩페이지/e북 사업)과는 별개의 상위 트랙(재창업·정부지원 목적) — 계약 진행중인 무료컨설팅은 이 신규 사업의 트랙션 근거로 활용

### [2026-06-23] 컨설턴트 프로필 사진 추가
- 사용자가 프로필 사진(스튜디오 정면, 흰 셔츠/네이비 슬랙스, 1024x1536 JPEG) 업로드
- 파일 자동저장 안 됨 → 세션 transcript(.jsonl)의 base64 image 블록에서 추출(마지막 image/jpeg)해 profile.jpg로 저장(루트)
- profile.html이 src="profile.jpg" 참조 → 이제 /consultant 에서 사진 표시됨. og:image도 해결
- 부수: .img-ph 자리표시를 점선박스→그린 그라데이션+골드 아바타(권)로 개선(폴백용)
- 추출법(재사용): jsonl walk로 type=image source.data base64 디코드, PIL로 크기확인

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

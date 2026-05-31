#!/usr/bin/env python3
"""
안심문자 — 보험설계사용 비(非)영업 문자 도우미

핵심 기능: 설계사가 고객에게 보낼 문자가 "스팸/영업처럼 보일지"를
AI가 점수로 평가하고, 영업톤을 낮춘 따뜻한 버전을 제안한다.

설계사의 진짜 두려움("이거 스팸처럼 보일까?")을 점수로 해소한다.
"""
import json
import os

import anthropic
import streamlit as st

# ── SMS 바이트 계산 (국내 통신사 관행: 한글 2바이트, ASCII 1바이트) ──
SMS_LIMIT = 90      # 단문(SMS) 한도 (한글 약 45자)
LMS_LIMIT = 2000    # 장문(LMS) 한도 (한글 약 1000자)

def sms_bytes(text: str) -> int:
    return sum(2 if ord(c) > 127 else 1 for c in text)

def sms_type(text: str) -> str:
    b = sms_bytes(text)
    if b <= SMS_LIMIT:
        return f"단문(SMS) · {b}/{SMS_LIMIT}바이트"
    if b <= LMS_LIMIT:
        return f"장문(LMS) · {b}/{LMS_LIMIT}바이트"
    return f"⚠ 장문 초과 · {b}바이트 (분할 발송됨)"


# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(page_title="안심문자 — 보험설계사 문자 도우미",
                   page_icon="💬", layout="centered")

st.markdown("""
<style>
.tone-safe   { color:#2e7d32; font-weight:700; }
.tone-warn   { color:#e65100; font-weight:700; }
.tone-danger { color:#c62828; font-weight:700; }
.msg-box {
    background:#f7f9fc; border:1px solid #e0e6ed; border-radius:10px;
    padding:16px; margin:8px 0; font-size:1.05em; line-height:1.6;
    white-space:pre-wrap;
}
.reason { color:#5f6c7b; font-size:0.9em; }
</style>
""", unsafe_allow_html=True)

# ── 사이드바 ─────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("Anthropic API Key", type="password",
                            value=os.environ.get("ANTHROPIC_API_KEY", ""))
    st.divider()
    st.caption("💡 이 도구는 **기존 고객 관계 유지**용입니다.\n\n"
               "신규/잠재 고객 대상 광고 문자는 정보통신망법상 "
               "사전동의·(광고)표기·수신거부 안내가 필요합니다.")

# ── 헤더 ─────────────────────────────────────────────────────
st.title("💬 안심문자")
st.caption("보낼 문자가 **스팸·영업처럼 보일지** AI가 점수로 알려드립니다. "
           "고객이 부담 없이 받을 수 있는 따뜻한 버전을 제안해요.")

# ── 입력 ─────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    customer = st.text_input("고객 호칭", placeholder="예) 김영희 고객님")
    relation = st.text_input("관계·맥락",
                             placeholder="예) 3년째 거래, 자녀 둘, 작년 실손 가입")
with col2:
    occasion = st.selectbox("상황", [
        "안부 인사 (계기 없음)",
        "생일 축하",
        "명절 인사",
        "계약 기념일",
        "보장 점검 제안",
        "보험금 청구 안내",
        "갱신 시점 안내",
        "직접 입력",
    ])
    if occasion == "직접 입력":
        occasion = st.text_input("상황 직접 입력", placeholder="예) 환절기 건강 안부")

extra = st.text_area("추가로 담고 싶은 내용 (선택)", height=70,
                     placeholder="예) 최근 무릎 수술 하셨다고 들어서 안부 묻고 싶음")

go = st.button("✍️ 문자 3안 생성 + 영업톤 진단", type="primary",
               use_container_width=True)

# ── 생성 ─────────────────────────────────────────────────────
SYSTEM = """당신은 보험설계사의 고객 문자를 도와주는 전문가입니다.
한국 보험설계사가 '기존 고객'에게 보낼 SMS/LMS 문자를 작성합니다.

가장 중요한 원칙: 고객이 '영업 문자/스팸'으로 느끼지 않게 합니다.
- 상품 권유·가입 유도·"지금" 같은 압박 표현을 피합니다.
- 고객의 안부와 상황을 먼저 챙기고, 진심이 느껴지게 합니다.
- 설계사 이름을 자연스럽게 밝혀 누가 보냈는지 알게 합니다.
- 문자는 간결하게 (가능하면 LMS 1~3문장).

반드시 아래 JSON 형식으로만 응답하세요. 설명·코드펜스 없이 JSON만:
{
  "messages": [
    {
      "label": "톤 이름 (예: 따뜻한 안부형)",
      "text": "실제 문자 내용",
      "sales_tone": 0-100 사이 정수 (영업처럼 느껴지는 정도, 낮을수록 안전),
      "reason": "이 점수를 준 한 줄 근거",
      "is_ad": true/false (정보통신망법상 '광고성'으로 분류될 소지가 있는가)
    }
  ]
}
3개의 서로 다른 톤(따뜻한 안부형 / 가벼운 체크인형 / 정보 제공형)으로 작성하세요."""

def generate(client, payload: str) -> list:
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1200,
        system=SYSTEM,
        messages=[{"role": "user", "content": payload}],
    )
    raw = resp.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1].lstrip("json").strip()
    return json.loads(raw)["messages"]


def tone_badge(score: int) -> str:
    if score <= 25:
        return f'<span class="tone-safe">🟢 영업톤 {score}% · 안심하고 보내세요</span>'
    if score <= 55:
        return f'<span class="tone-warn">🟡 영업톤 {score}% · 살짝 부담될 수 있어요</span>'
    return f'<span class="tone-danger">🔴 영업톤 {score}% · 영업 문자로 느껴질 위험</span>'


if go:
    if not api_key:
        st.warning("사이드바에 API Key를 입력해주세요")
        st.stop()
    if not customer or not occasion:
        st.warning("고객 호칭과 상황을 입력해주세요")
        st.stop()

    payload = (
        f"고객 호칭: {customer}\n"
        f"관계·맥락: {relation or '정보 없음'}\n"
        f"상황: {occasion}\n"
        f"추가 요청: {extra or '없음'}"
    )
    client = anthropic.Anthropic(api_key=api_key)

    with st.spinner("문자 3안을 만들고 영업톤을 진단 중입니다..."):
        try:
            messages = generate(client, payload)
        except Exception as e:
            st.error(f"생성 오류: {e}")
            st.stop()

    # 가장 안전한 안을 위로 정렬
    messages.sort(key=lambda m: m.get("sales_tone", 50))

    st.success(f"✅ {len(messages)}개 문자 생성 완료 — 가장 안전한 순서로 정렬했습니다")

    for i, m in enumerate(messages):
        text  = m.get("text", "")
        score = int(m.get("sales_tone", 50))
        st.markdown(f"### {i+1}. {m.get('label','문자안')}")
        st.markdown(tone_badge(score), unsafe_allow_html=True)
        st.markdown(f'<div class="msg-box">{text}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="reason">📋 진단: {m.get("reason","")}</div>',
                    unsafe_allow_html=True)

        c1, c2 = st.columns([2, 1])
        c1.caption(f"📏 {sms_type(text)}")
        if m.get("is_ad"):
            c2.caption("⚠ (광고) 표기 검토 필요")
        else:
            c2.caption("✅ 관계유지 메시지 (광고 아님)")

        st.code(text, language=None)  # 복사 버튼 자동 제공
        st.divider()

    st.info("💡 마음에 드는 문자의 우측 상단 복사 버튼을 눌러 그대로 붙여넣으세요.")

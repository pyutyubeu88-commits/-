#!/usr/bin/env python3
"""
치매간병보험 DM 드립 생성기 — 매일 1개씩 보내는 7일 문자 시퀀스

롯데손해보험 Let:care 치매간병보험 교육자료에 근거(grounding)해,
고객에게 매일 1통씩 연속으로 보낼 수 있는 문자(SMS/LMS)를 생성한다.

핵심:
- knowledge.py 의 실제 수치에만 근거 → 보험업법 허위·과장 방지
- 관계→문제인식→비용→기존보험 빈틈→해결책→상담제안 으로 자연 빌드업
- 각 문자에 영업톤 점수 + 광고 표기 필요 여부 + 바이트 수 표시
"""
import json
import os

import anthropic
import streamlit as st

import knowledge as K

# ── SMS 바이트 (국내 통신사 관행: 한글 2바이트) ──
def sms_bytes(t: str) -> int:
    return sum(2 if ord(c) > 127 else 1 for c in t)

def sms_type(t: str) -> str:
    b = sms_bytes(t)
    if b <= 90:   return f"단문(SMS) · {b}바이트"
    if b <= 2000: return f"장문(LMS) · {b}바이트"
    return f"⚠ LMS 초과 · {b}바이트"


st.set_page_config(page_title="치매간병보험 DM 드립 생성기",
                   page_icon="📨", layout="centered")

st.markdown("""
<style>
.msg-box{background:#f7f9fc;border:1px solid #e0e6ed;border-radius:10px;
         padding:16px;margin:6px 0;font-size:1.05em;line-height:1.65;white-space:pre-wrap;}
.tone-safe{color:#2e7d32;font-weight:700;}
.tone-warn{color:#e65100;font-weight:700;}
.tone-danger{color:#c62828;font-weight:700;}
.daytag{background:#1f3a5f;color:#fff;border-radius:6px;padding:2px 10px;font-weight:700;}
.reason{color:#5f6c7b;font-size:.88em;}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("Anthropic API Key", type="password",
                            value=os.environ.get("ANTHROPIC_API_KEY", ""))
    st.divider()
    st.caption("📕 그라운딩: 롯데손해보험 Let:care 치매간병보험 교육자료\n\n"
               "모든 수치는 자료 기준이며 세부사항은 약관을 따릅니다.")
    st.caption("⚖️ 상품 권유 문자는 정보통신망법상 **광고성 정보**입니다. "
               "기존 고객이라도 사전 광고수신 동의가 필요하며, "
               "(광고)·수신거부 안내·발신자 표기가 의무입니다.")

st.title("📨 치매간병보험 DM 드립 생성기")
st.caption("고객에게 **매일 1통씩** 보낼 7일 문자 시퀀스를 만듭니다. "
           "관계 → 현실 인식 → 비용 → 기존 보험 빈틈 → 해결책 → 상담 제안 순으로 빌드업됩니다.")

# ── 입력 ──
c1, c2 = st.columns(2)
with c1:
    customer = st.text_input("고객 호칭", placeholder="예) 김영희 고객님")
    agent    = st.text_input("설계사(발신자) 이름", placeholder="예) 박철수 설계사")
with c2:
    age_grp  = st.selectbox("고객 연령대", ["50대", "60대", "40대", "70대", "미상"])
    relation = st.text_input("관계·맥락(선택)",
                             placeholder="예) 3년 거래, 부모님 간병 경험 있음")

days = st.radio("드립 기간", [7], horizontal=True,
                help="MVP는 검증된 7일 아크를 제공합니다")
consent = st.checkbox("이 고객은 광고성 정보 수신에 사전 동의했습니다", value=False)

go = st.button("✍️ 7일 문자 시퀀스 생성", type="primary", use_container_width=True)

# ── 생성 로직 ──
SYSTEM = """당신은 보험설계사의 고객 문자를 돕는 전문 카피라이터입니다.
한국 보험설계사가 '기존 고객'에게 며칠에 걸쳐 매일 1통씩 보낼 문자 시퀀스를 씁니다.

[절대 원칙]
1. 제공된 '근거 사실'에 있는 내용만 사용하세요. 수치를 지어내거나 과장하지 마세요.
   보험은 허위·과장 표현이 법으로 금지됩니다.
2. 겁주기·공포 마케팅 금지. 정보와 공감 위주로, 고객을 존중하는 따뜻한 톤.
3. 각 문자는 그날의 주제(theme)와 목표(goal)에 충실하고, 전날의 흐름을 자연스럽게 잇습니다.
4. 상품명/보험사명은 마지막 상담 제안 단계에서 자연스럽게만 언급. 초반엔 언급 금지.
5. 문자는 간결하게. 안부형은 짧게(SMS), 정보형은 LMS 2~4문장.
6. 발신자(설계사) 이름을 적절히 밝혀 누가 보냈는지 알게 합니다.

각 날짜별로 아래 JSON 배열로만 응답하세요(코드펜스·설명 없이 JSON만):
{
  "messages": [
    {
      "day": 정수,
      "theme": "그날 주제",
      "text": "실제 문자 내용",
      "sales_tone": 0-100 정수(영업처럼 느껴지는 정도, 낮을수록 안전),
      "reason": "톤 점수 한 줄 근거",
      "grounding": "이 문자가 근거한 사실 요약(없으면 '관계형')"
    }
  ]
}"""


def build_prompt() -> str:
    arc = K.arc_for(days)
    lines = [
        f"고객 호칭: {customer}",
        f"발신 설계사: {agent or '담당 설계사'}",
        f"고객 연령대: {age_grp}",
        f"관계·맥락: {relation or '일반 기존 고객'}",
        f"상품(상담 단계에서만 언급): {K.PRODUCT['insurer']} {K.PRODUCT['name']} ({K.PRODUCT['type']})",
        "",
        "아래는 날짜별 주제와 사용할 근거 사실입니다. 순서대로 매일 1통씩 작성하세요:",
        "",
    ]
    for d in arc:
        lines.append(f"[{d['day']}일차] 주제: {d['theme']}")
        lines.append(f"  목표: {d['goal']}")
        lines.append(f"  목표 영업톤: {d['tone_target']}")
        facts = K.fact_text(d["facts"])
        lines.append("  근거 사실:\n" + (facts if facts else "  (없음 — 순수 관계형 안부)"))
        lines.append("")
    return "\n".join(lines)


def tone_badge(s: int) -> str:
    if s <= 25:  return f'<span class="tone-safe">🟢 영업톤 {s}%</span>'
    if s <= 55:  return f'<span class="tone-warn">🟡 영업톤 {s}%</span>'
    return f'<span class="tone-danger">🔴 영업톤 {s}%</span>'


AD_PREFIX = "(광고)"
AD_SUFFIX_TMPL = "\n무료수신거부 {optout}"


def apply_ad_label(text: str, day_meta: dict, consented: bool) -> tuple:
    """광고성 단계면 (광고) 표기 + 수신거부 안내 부착. 반환: (최종문구, 광고여부)."""
    if not day_meta.get("is_ad"):
        return text, False
    labeled = text
    if not labeled.startswith(AD_PREFIX):
        labeled = f"{AD_PREFIX}{labeled}"
    labeled += AD_SUFFIX_TMPL.format(optout="080-XXX-XXXX")
    return labeled, True


if go:
    if not api_key:
        st.warning("사이드바에 API Key를 입력해주세요"); st.stop()
    if not customer:
        st.warning("고객 호칭을 입력해주세요"); st.stop()

    client = anthropic.Anthropic(api_key=api_key)
    with st.spinner("7일 문자 시퀀스를 그라운딩 기반으로 생성 중..."):
        try:
            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=2500,
                system=SYSTEM,
                messages=[{"role": "user", "content": build_prompt()}],
            )
            raw = resp.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1].lstrip("json").strip()
            messages = json.loads(raw)["messages"]
        except Exception as e:
            st.error(f"생성 오류: {e}"); st.stop()

    arc_meta = {d["day"]: d for d in K.arc_for(days)}
    st.success(f"✅ {len(messages)}일치 문자 생성 완료")

    if not consent:
        st.warning("⚠️ 이 고객의 광고수신 동의가 체크되지 않았습니다. "
                   "5~7일차(상품 권유)는 동의 없이는 발송할 수 없습니다. "
                   "동의 전이라면 1~4일차(정보·안부)만 활용하세요.")

    for m in sorted(messages, key=lambda x: x.get("day", 0)):
        day  = m.get("day", 0)
        meta = arc_meta.get(day, {})
        text = m.get("text", "")
        score = int(m.get("sales_tone", 50))

        final_text, is_ad = apply_ad_label(text, meta, consent)

        st.markdown(f'<span class="daytag">{day}일차</span> '
                    f'**{m.get("theme","")}**  {tone_badge(score)}',
                    unsafe_allow_html=True)
        st.markdown(f'<div class="msg-box">{final_text}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="reason">📋 {m.get("reason","")} · '
                    f'근거: {m.get("grounding","")}</div>', unsafe_allow_html=True)

        cc1, cc2 = st.columns([2, 1])
        cc1.caption(f"📏 {sms_type(final_text)}")
        if is_ad:
            cc2.caption("📢 광고성 — (광고)·수신거부 부착됨")
        else:
            cc2.caption("✅ 정보·관계형 (광고 아님)")
        st.code(final_text, language=None)
        st.divider()

    # 전체 다운로드
    bundle = "\n\n".join(
        f"[{m.get('day')}일차] {m.get('theme')}\n"
        + apply_ad_label(m.get("text",""), arc_meta.get(m.get("day",0),{}), consent)[0]
        for m in sorted(messages, key=lambda x: x.get("day", 0))
    )
    st.download_button("📥 7일 시퀀스 전체 다운로드(.txt)", bundle.encode("utf-8"),
                       file_name="치매간병보험_7일DM.txt", use_container_width=True)

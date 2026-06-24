#!/usr/bin/env python3
"""
AI 반복업무 자동화 데모
크몽 클라이언트 시연용 — CSV/엑셀 파일을 올리고 원하는 작업을 말하면 처리
"""
import json
import os
from io import BytesIO

import anthropic
import pandas as pd
import streamlit as st

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="AI 반복업무 자동화",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 스타일 ───────────────────────────────────────────────────
st.markdown("""
<style>
.metric-card {
    background: #f0f2f6; border-radius: 8px;
    padding: 16px; margin: 4px 0;
}
.cost-badge {
    background: #e8f5e9; color: #2e7d32;
    border-radius: 4px; padding: 2px 8px;
    font-size: 0.85em; font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ── 사이드바 ─────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        value=os.environ.get("ANTHROPIC_API_KEY", ""),
        help="https://console.anthropic.com 에서 발급",
    )
    max_rows = st.slider("최대 처리 행 수", 10, 200, 50, 10,
                         help="데모는 50행 추천. 실제 납품 시 제한 없음")
    mode = st.radio(
        "처리 모드",
        ["🔢 행별 처리", "📊 전체 분석"],
        help="행별: 각 행마다 AI가 처리 / 전체: 데이터셋 인사이트 리포트",
    )
    st.divider()
    st.caption("납품 시 클라이언트 환경에 맞게 커스터마이징 됩니다")

# ── 메인 ─────────────────────────────────────────────────────
st.title("🤖 AI 반복업무 자동화")
st.caption("CSV / 엑셀 파일을 올리고 원하는 작업을 한국어로 설명하면 AI가 자동 처리합니다")

# ── 샘플 다운로드 ─────────────────────────────────────────────
with st.expander("📁 샘플 데이터가 없으신가요?", expanded=False):
    sample = pd.DataFrame({
        "고객명":   ["김철수", "이영희", "박민준", "최수진", "정대한"],
        "문의내용": [
            "주문한 상품이 아직 안 왔어요. 배송이 어디까지 왔나요?",
            "구매한 제품이 불량인 것 같아요. 환불 받을 수 있나요?",
            "사이즈가 맞지 않아서 교환하고 싶습니다.",
            "포인트는 언제 적립되나요?",
            "결제했는데 주문 확인 이메일이 안 왔어요",
        ],
        "주문번호": ["ORD-001", "ORD-002", "ORD-003", "ORD-004", "ORD-005"],
        "주문금액": [35000, 120000, 89000, 45000, 67000],
    })
    buf = BytesIO()
    sample.to_csv(buf, index=False, encoding="utf-8-sig")
    st.download_button("샘플 CSV 다운로드", buf.getvalue(),
                       file_name="sample_cs_data.csv", mime="text/csv")

# ── 파일 업로드 ──────────────────────────────────────────────
uploaded = st.file_uploader(
    "CSV 또는 엑셀 파일을 여기에 드래그하세요",
    type=["csv", "xlsx", "xls"],
)

if not uploaded:
    st.info("👆 파일을 업로드하면 시작됩니다")
    st.stop()

# ── 파일 읽기 ────────────────────────────────────────────────
try:
    if uploaded.name.lower().endswith(".csv"):
        try:
            df = pd.read_csv(uploaded, encoding="utf-8-sig")
        except UnicodeDecodeError:
            df = pd.read_csv(uploaded, encoding="cp949")
    else:
        df = pd.read_excel(uploaded)
except Exception as e:
    st.error(f"파일 읽기 오류: {e}")
    st.stop()

df = df.where(pd.notna(df), None)

# ── 데이터 미리보기 ──────────────────────────────────────────
c1, c2, c3 = st.columns(3)
c1.metric("총 행 수", f"{len(df):,}")
c2.metric("총 열 수", len(df.columns))
c3.metric("처리 예정", f"{min(len(df), max_rows):,}행")

with st.expander("📊 데이터 미리보기", expanded=True):
    st.dataframe(df.head(10), use_container_width=True)

# ── 작업 설정 ────────────────────────────────────────────────
st.divider()
st.subheader("🎯 원하는 작업 설명")

task_examples = {
    "고객 문의 분류": "각 문의를 '배송', '환불/교환', '제품 문의', '결제', '기타' 중 하나로 분류하고, 긴급도를 '높음/보통/낮음'으로 평가해주세요.",
    "감성 분석": "각 텍스트의 감성을 '긍정', '부정', '중립'으로 분류하고, 핵심 키워드 2~3개를 추출해주세요.",
    "데이터 요약": "각 행의 주요 내용을 30자 이내로 요약해주세요.",
    "이상값 탐지": "데이터에서 이상하거나 비정상적인 값이 있는 행을 찾고 이유를 설명해주세요.",
    "직접 입력": "",
}

example_choice = st.selectbox("예시 선택 (또는 직접 입력)", list(task_examples.keys()))
task = st.text_area(
    "작업 내용",
    value=task_examples[example_choice],
    height=90,
    placeholder="예) 각 고객 문의를 카테고리로 분류하고 우선순위를 매겨주세요",
)

# 컬럼 선택
with st.expander("🔧 고급 설정"):
    target_cols = st.multiselect(
        "처리할 컬럼 선택 (비워두면 전체 사용)",
        options=list(df.columns),
        default=[],
    )
    output_lang = st.radio("출력 언어", ["한국어", "English"], horizontal=True)

if not task.strip():
    st.warning("작업 내용을 입력해주세요")
    st.stop()

if not api_key:
    st.warning("사이드바에 Anthropic API Key를 입력해주세요")
    st.stop()

# ── 처리 시작 ────────────────────────────────────────────────
if not st.button("🚀 AI 자동 처리 시작", type="primary", use_container_width=True):
    st.stop()

client = anthropic.Anthropic(api_key=api_key)
work_df = df[target_cols].head(max_rows) if target_cols else df.head(max_rows)
lang_hint = "" if output_lang == "한국어" else "Respond in English."

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 모드 A: 행별 처리
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if "행별" in mode:
    system_prompt = (
        f"당신은 데이터 처리 전문가입니다. {lang_hint}\n"
        f"작업: {task}\n\n"
        "각 행 데이터를 받으면 작업을 수행하고 **반드시 JSON 객체만** 반환하세요. "
        "설명 없이 JSON만. 키는 짧은 한국어 레이블로."
    )

    progress_bar = st.progress(0, text="처리 중...")
    status_placeholder = st.empty()
    results: list[dict] = []
    total_tokens = 0

    for i, (_, row) in enumerate(work_df.iterrows()):
        row_text = "\n".join(
            f"{col}: {val}" for col, val in row.items() if val is not None
        )
        try:
            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=300,
                system=system_prompt,
                messages=[{"role": "user", "content": row_text}],
            )
            raw = resp.content[0].text.strip()
            # JSON 파싱 시도
            if raw.startswith("```"):
                raw = raw.split("```")[1].lstrip("json").strip()
            try:
                result = json.loads(raw)
            except json.JSONDecodeError:
                result = {"AI_결과": raw}
            total_tokens += resp.usage.input_tokens + resp.usage.output_tokens
        except Exception as e:
            result = {"AI_오류": str(e)[:80]}

        results.append(result)
        pct = (i + 1) / len(work_df)
        progress_bar.progress(pct, text=f"{i+1}/{len(work_df)}행 처리 중...")
        status_placeholder.caption(f"누적 토큰: {total_tokens:,}")

    progress_bar.empty()
    status_placeholder.empty()

    # 결과 병합
    result_df = pd.DataFrame(results)
    final_df = work_df.copy().reset_index(drop=True)
    for col in result_df.columns:
        final_df[f"[AI] {col}"] = result_df[col]

    st.success(f"✅ {len(results)}행 처리 완료  |  토큰 사용: {total_tokens:,}")
    st.dataframe(final_df, use_container_width=True)

    # 다운로드
    out = BytesIO()
    final_df.to_excel(out, index=False)
    st.download_button(
        "📥 결과 엑셀 다운로드",
        data=out.getvalue(),
        file_name="AI_처리결과.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 모드 B: 전체 분석
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
else:
    # 데이터를 텍스트로 직렬화 (최대 100행, 4000자 제한)
    data_text = work_df.to_csv(index=False)[:4000]

    with st.spinner("AI가 전체 데이터를 분석 중입니다..."):
        try:
            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1500,
                system=(
                    f"당신은 데이터 분석 전문가입니다. {lang_hint}\n"
                    "CSV 데이터를 분석해서 마크다운 형식의 인사이트 리포트를 작성해주세요. "
                    "패턴, 이상값, 주요 발견, 액션 가능한 권고사항을 포함하세요."
                ),
                messages=[{
                    "role": "user",
                    "content": (
                        f"작업 요청: {task}\n\n"
                        f"데이터 ({len(work_df)}행):\n```csv\n{data_text}\n```\n\n"
                        "위 데이터를 분석해서 인사이트 리포트를 작성해주세요."
                    ),
                }],
            )
            report = resp.content[0].text
            tokens = resp.usage.input_tokens + resp.usage.output_tokens
        except Exception as e:
            st.error(f"API 오류: {e}")
            st.stop()

    st.success(f"✅ 분석 완료  |  토큰 사용: {tokens:,}")
    st.markdown("---")
    st.markdown(report)

    st.download_button(
        "📥 리포트 다운로드 (.md)",
        data=report.encode("utf-8"),
        file_name="AI_분석리포트.md",
        mime="text/markdown",
        use_container_width=True,
    )

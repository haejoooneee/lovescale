import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# CSV 파일 경로
DATA_FILE = "lovescale_data.csv"

# 페이지 설정
st.set_page_config(page_title="💔 헤어짐의 저울질 (LoveScale)", layout="centered")
st.title("💔 헤어짐의 저울질 (LoveScale)")
st.write("AI가 감정의 흐름을 함께 살펴보고, 관계의 온도를 시각화합니다.")
st.divider()

# 데이터 불러오기
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    if "감정 점수" not in df.columns:
        df["감정 점수"] = 0
else:
    df = pd.DataFrame(columns=["날짜", "좋은 점", "힘들었던 점", "감정 점수"])

# 감정 분석기
analyzer = SentimentIntensityAnalyzer()

# 세션 초기화
if "positive_text" not in st.session_state:
    st.session_state["positive_text"] = ""
if "negative_text" not in st.session_state:
    st.session_state["negative_text"] = ""

# -------------------------------
# 📔 오늘의 감정 일기
# -------------------------------
st.header("📔 오늘의 감정 일기")

col1, col2 = st.columns(2)

# 좋은 점 입력
with col1:
    st.markdown("**좋은 점 💕**")
    positive = st.text_area(
        " ", 
        value=st.session_state["positive_text"], 
        placeholder="예: 함께 웃었던 대화가 즐거웠어요", 
        key="pos_area"
    )
    if st.button("없음(잘 모르겠음)", key="pos_btn"):
        st.session_state["positive_text"] = "없음(잘 모르겠음)"
        st.rerun()
    else:
        st.session_state["positive_text"] = positive

# 힘들었던 점 입력
with col2:
    st.markdown("**힘들었던 점 💔**")
    negative = st.text_area(
        " ", 
        value=st.session_state["negative_text"], 
        placeholder="예: 대화가 자주 끊겨서 답답했어요", 
        key="neg_area"
    )
    if st.button("없음(잘 모르겠음)", key="neg_btn"):
        st.session_state["negative_text"] = "없음(잘 모르겠음)"
        st.rerun()
    else:
        st.session_state["negative_text"] = negative

# -------------------------------
# 💾 감정 분석 및 저장
# -------------------------------
if st.button("감정 분석 및 저장"):
    positive = st.session_state["positive_text"]
    negative = st.session_state["negative_text"]

    if not positive and not negative:
        st.warning("감정을 입력해주세요 💬")
    else:
        # 감정 분석
        pos_score = analyzer.polarity_scores(positive)["compound"] if positive else 0
        neg_score = analyzer.polarity_scores(negative)["compound"] if negative else 0

        # 없음(잘 모르겠음)은 중립 처리
        if "없음" in positive:
            pos_score = 0
        if "없음" in negative:
            neg_score = 0

        # 계산 보정 — 좋은 점만 있으면 그대로 긍정 반영
        if "없음" in negative and "없음" not in positive:
            score = pos_score
        elif "없음" in positive and "없음" not in negative:
            score = -abs(neg_score)
        else:
            score = pos_score - abs(neg_score)

        today = datetime.now().strftime("%Y-%m-%d")

        # 저장
        new_row = pd.DataFrame({
            "날짜": [today],
            "좋은 점": [positive],
            "힘들었던 점": [negative],
            "감정 점수": [score]
        })
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

        # 결과 표시
        st.success("오늘의 감정 일기가 저장되었습니다 💾")
        st.subheader("🧭 감정 분석 결과")

        st.write(f"📊 **감정 지수:** {score:.2f}")

        if score > 0.3:
            st.success("긍정적인 하루였어요 💖 좋은 에너지가 느껴집니다.")
        elif score < -0.3:
            st.error("조금 힘든 하루였네요 😢 스스로를 돌봐주세요.")
        else:
            st.info("균형 잡힌 감정 상태예요 ⚖️ 천천히 마음을 살펴보세요.")

st.divider()

# -------------------------------
# ✏️ 기록 관리
# -------------------------------
st.header("✏️ 기록 관리 (수정 및 삭제)")
if not df.empty:
    edit_date = st.selectbox("수정 또는 삭제할 날짜 선택", df["날짜"].unique())
    selected = df[df["날짜"] == edit_date].iloc[0]
    new_pos = st.text_area("좋은 점 수정", selected["좋은 점"])
    new_neg = st.text_area("힘들었던 점 수정", selected["힘들었던 점"])

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 수정 저장"):
            df.loc[df["날짜"] == edit_date, ["좋은 점", "힘들었던 점"]] = [new_pos, new_neg]
            df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
            st.success("수정이 저장되었습니다 ✅")
    with col2:
        if st.button("🗑️ 삭제"):
            df = df[df["날짜"] != edit_date]
            df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
            st.warning("선택한 일기가 삭제되었습니다 ❌")
else:
    st.info("저장된 일기가 없습니다 💬")

st.divider()

# -------------------------------
# 📈 감정 변화 그래프
# -------------------------------
st.header("📊 감정 변화 추이")
if not df.empty:
    df["날짜"] = pd.to_datetime(df["날짜"])
    fig = px.line(df, x="날짜", y="감정 점수", title="📈 감정 변화 그래프", markers=True)
    fig.add_hline(y=0, line_dash="dot", line_color="gray")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("아직 데이터가 없습니다 💬")

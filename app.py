import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# 파일 경로
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
if "positive_hidden" not in st.session_state:
    st.session_state["positive_hidden"] = False
if "negative_hidden" not in st.session_state:
    st.session_state["negative_hidden"] = False
if "positive_text" not in st.session_state:
    st.session_state["positive_text"] = ""
if "negative_text" not in st.session_state:
    st.session_state["negative_text"] = ""

# -------------------------------
# 📔 감정 입력
# -------------------------------
st.header("📔 오늘의 감정 일기")

col1, col2 = st.columns(2)

# 좋은 점 입력창
with col1:
    st.markdown("**좋은 점 💕**")
    if st.session_state["positive_hidden"]:
        st.markdown("🩶 없음(잘 모르겠음)")
    else:
        st.session_state["positive_text"] = st.text_area(
            " ", value=st.session_state["positive_text"], placeholder="예: 함께 웃었던 대화가 즐거웠어요", key="pos_area"
        )
        if st.button("없음(잘 모르겠음)", key="pos_btn"):
            st.session_state["positive_text"] = "없음(잘 모르겠음)"
            st.session_state["positive_hidden"] = True
            st.rerun()

# 힘들었던 점 입력창
with col2:
    st.markdown("**힘들었던 점 💔**")
    if st.session_state["negative_hidden"]:
        st.markdown("🩶 없음(잘 모르겠음)")
    else:
        st.session_state["negative_text"] = st.text_area(
            " ", value=st.session_state["negative_text"], placeholder="예: 대화가 자주 끊겨서 답답했어요", key="neg_area"
        )
        if st.button("없음(잘 모르겠음)", key="neg_btn"):
            st.session_state["negative_text"] = "없음(잘 모르겠음)"
            st.session_state["negative_hidden"] = True
            st.rerun()

# -------------------------------
# 💾 감정 분석 및 저장
# -------------------------------
if st.button("감정 분석 및 저장"):
    positive = st.session_state["positive_text"]
    negative = st.session_state["negative_text"]

    if not positive and not negative:
        st.warning("감정을 입력해주세요 💬")
    else:
        # 분석 결과
        pos_score = analyzer.polarity_scores(positive)["compound"] if "없음" not in positive else 0
        neg_score = analyzer.polarity_scores(negative)["compound"] if "없음" not in negative else 0

        # 감정 보정 (가중치 확대)
        pos_score *= 2
        neg_score *= 2

        # 감정이 하나라도 입력된 경우
        if "없음" in positive and "없음" not in negative:
            score = -abs(neg_score)
        elif "없음" in negative and "없음" not in positive:
            score = pos_score
        else:
            score = pos_score - abs(neg_score)

        # 스케일 제한 (-1 ~ +1)
        score = max(min(score, 1.0), -1.0)

        today = datetime.now().strftime("%Y-%m-%d")

        new_row = pd.DataFrame({
            "날짜": [today],
            "좋은 점": [positive],
            "힘들었던 점": [negative],
            "감정 점수": [score]
        })
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

        # ---------------- 결과 표시 ----------------
        st.success("오늘의 감정 일기가 저장되었습니다 💾")
        st.subheader("🧭 감정 분석 결과")
        st.write(f"📊 **감정 지수:** {score:.2f}")

        if score >= 0.7:
            st.success("🌞 매우 긍정적인 하루였어요! 사랑과 행복이 느껴집니다.")
        elif score >= 0.3:
            st.info("😊 긍정적인 하루였어요. 좋은 감정이 이어지고 있어요.")
        elif -0.3 < score < 0.3:
            st.warning("⚖️ 감정이 균형을 이루고 있습니다. 차분히 마음을 살펴보세요.")
        elif score <= -0.3 and score > -0.7:
            st.error("😢 약간 힘든 하루였어요. 자신을 돌봐주세요.")
        else:
            st.error("💔 감정이 많이 지쳐있어요. 잠시 쉬어가도 괜찮아요.")

st.divider()

# -------------------------------
# 📈 감정 변화 그래프
# -------------------------------
st.header("📊 감정 변화 추이")

if not df.empty:
    df["날짜"] = pd.to_datetime(df["날짜"])
    fig = px.line(df, x="날짜", y="감정 점수", title="📈 감정 변화 그래프", markers=True)
    fig.add_hline(y=0, line_dash="dot", line_color="gray")
    fig.update_traces(line_color="#1f77b4", line_width=3)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("아직 데이터가 없습니다 💬")

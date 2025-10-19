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

with col1:
    st.markdown("**좋은 점 💕**")
    positive = st.text_area(" ", value=st.session_state["positive_text"], placeholder="예: 함께 웃었던 대화가 즐거웠어요", key="pos_input")
    if st.button("없음(잘 모르겠음)", key="pos_btn"):
        st.session_state["positive_text"] = "없음(잘 모르겠음)"
        st.rerun()

with col2:
    st.markdown("**힘들었던 점 💔**")
    negative = st.text_area(" ", value=st.session_state["negative_text"], placeholder="예: 대화가 자주 끊겨서 답답했어요", key="neg_input")
    if st.button("없음(잘 모르겠음)", key="neg_btn"):
        st.session_state["negative_text"] = "없음(잘 모르겠음)"
        st.rerun()

# -------------------------------
# 💾 감정 분석 및 저장
# -------------------------------
if st.button("감정 분석 및 저장"):
    positive = st.session_state["positive_text"] or positive
    negative = st.session_state["negative_text"] or negative

    if not positive and not negative:
        st.warning("감정을 입력해주세요 💬")
    else:
        # 감정 분석 분리 계산
        pos_score = analyzer.polarity_scores(positive)["compound"] if positive else 0
        neg_score = analyzer.polarity_scores(negative)["compound"] if negative else 0

        # 없음(잘 모르겠음)은 중립 처리 (0)
        if "없음" in positive:
            pos_score = 0
        if "없음" in negative:
            neg_score = 0

        # 감정 점수 계산
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

st.divider()

# -------------------------------
# 🧠 도와줘!! 버튼
# -------------------------------
st.header("🆘 도와줘!! (AI 감정 요약 도우미)")
if st.button("도와줘!!"):
    if len(df) < 2:
        st.info("데이터가 부족해요 😅 2회 이상 기록이 필요합니다.")
    else:
        recent = df.iloc[-1]["감정 점수"]
        past_avg = df["감정 점수"].head(len(df)-1)["감정 점수"].mean()
        diff = recent - past_avg

        st.subheader("📈 감정 지수 변화")
        st.write(f"최근 감정 지수: **{recent:.2f}**, 과거 평균: **{past_avg:.2f}**")

        if diff > 0.1:
            st.success("최근 감정 지수가 상승했습니다 ⬆️ 긍정적인 흐름이에요.")
        elif diff < -0.1:
            st.error("감정 지수가 하락했습니다 ⬇️ 감정적으로 조금 지쳤을 수 있어요.")
        else:
            st.info("감정 변화가 거의 없어요 😐 안정적인 상태예요.")

        st.subheader("📘 관계 종합 요약")
        most_positive = df["좋은 점"].value_counts().index[0] if not df["좋은 점"].isnull().all() else "데이터 없음"
        most_negative = df["힘들었던 점"].value_counts().index[0] if not df["힘들었던 점"].isnull().all() else "데이터 없음"
        st.write(f"💖 **가장 자주 등장한 좋은 점:** {most_positive}")
        st.write(f"💔 **가장 자주 등장한 힘들었던 점:** {most_negative}")

        st.subheader("⚖️ 감정 분포 비율")
        sentiment_counts = {
            "긍정": (df["감정 점수"] > 0.3).sum(),
            "중립": ((df["감정 점수"] >= -0.3) & (df["감정 점수"] <= 0.3)).sum(),
            "부정": (df["감정 점수"] < -0.3).sum()
        }
        sent_df = pd.DataFrame(list(sentiment_counts.items()), columns=["감정", "횟수"])
        fig2 = px.pie(sent_df, names="감정", values="횟수", title="전체 감정 비율")
        st.plotly_chart(fig2, use_container_width=True)

st.caption("💾 데이터는 이 컴퓨터에만 저장됩니다. 감정 분석은 오픈소스 VADER 기반입니다.")

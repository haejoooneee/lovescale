# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# CSV 파일 저장 경로
DATA_FILE = "lovescale_data.csv"

# 🔧 페이지 설정 (모바일 대응)
st.set_page_config(
    page_title="💔 헤어짐의 저울질 (LoveScale)",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("<h2 style='text-align:center; color:#e06666;'>💔 헤어짐의 저울질 (LoveScale)</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>AI 없이도 감정의 흐름을 분석하고 관계의 온도를 시각화합니다.</p>", unsafe_allow_html=True)
st.divider()

# 📄 데이터 로드
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=["날짜", "좋은 점", "힘들었던 점", "감정 점수"])

# 🆘 도와줘!! 버튼
if st.button("🆘 도와줘!!", use_container_width=True):
    if df.empty:
        st.warning("아직 작성된 일기가 없습니다 💬")
    else:
        st.subheader("📈 감정 추세 분석")
        df["날짜"] = pd.to_datetime(df["날짜"])
        df = df.sort_values("날짜")

        # 📊 반응형 감정 변화 그래프
        fig = px.line(df, x="날짜", y="감정 점수", title="시간에 따른 감정 변화", markers=True)
        fig.update_traces(line=dict(width=4))
        fig.update_layout(title_x=0.5)
        st.plotly_chart(fig, use_container_width=True)

        if len(df) >= 3:
            recent_avg = df["감정 점수"].tail(3).mean()
            past_avg = df["감정 점수"].head(len(df)-3)["감정 점수"].mean()
            diff = recent_avg - past_avg

            if diff > 0.05:
                st.success(f"최근 감정이 상승했습니다 😊 (+{diff:.2f})")
                st.markdown("💡 **최근 관계가 긍정적으로 변화하고 있어요!** 대화가 부드럽거나 정서적으로 안정된 시기일 수 있습니다.")
            elif diff < -0.05:
                st.error(f"최근 감정이 하락했습니다 😢 ({diff:.2f})")
                st.markdown("⚠️ **감정이 다소 부정적으로 변하고 있습니다.** 서로의 피로감이나 거리감을 살펴보세요.")
            else:
                st.info("감정 변화 폭이 크지 않습니다 ⚖️ 꾸준히 기록해보세요.")

        st.divider()
        st.subheader("🧭 지금까지의 감정 요약")

        col1, col2 = st.columns(2)
        with col1:
            with st.expander("📘 좋은 점 모음"):
                positives = df["좋은 점"].dropna()
                if positives.empty:
                    st.write("아직 좋은 점이 없습니다 💬")
                else:
                    st.write(" / ".join(positives.tolist()))

        with col2:
            with st.expander("📕 힘들었던 점 모음"):
                negatives = df["힘들었던 점"].dropna()
                if negatives.empty:
                    st.write("아직 힘들었던 점이 없습니다 💬")
                else:
                    st.write(" / ".join(negatives.tolist()))

        st.caption("📊 데이터 기반으로 자동 분석되었습니다. AI 서버 없이 로컬에서 작동합니다 🔒")

st.divider()

# ✍️ 감정 일기 입력
st.markdown("<h4 style='color:#6d9eeb;'>📔 오늘의 감정 일기</h4>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.write("좋았던 점 💕")
    pos_choice = st.radio("선택", ["직접 입력", "없음 / 잘 모르겠음"], key="pos_opt", horizontal=True, label_visibility="collapsed")
    if pos_choice == "직접 입력":
        positive = st.text_area("좋았던 점", placeholder="예: 함께 웃었던 대화가 즐거웠어요", key="pos_text")
    else:
        positive = "잘 모르겠어요."

with col2:
    st.write("힘들었던 점 💔")
    neg_choice = st.radio("선택", ["직접 입력", "없음 / 잘 모르겠음"], key="neg_opt", horizontal=True, label_visibility="collapsed")
    if neg_choice == "직접 입력":
        negative = st.text_area("힘들었던 점", placeholder="예: 대화가 자주 끊겨서 답답했어요", key="neg_text")
    else:
        negative = "잘 모르겠어요."

if st.button("💾 감정 분석 및 저장", use_container_width=True):
    if (not positive or positive == "잘 모르겠어요.") and (not negative or negative == "잘 모르겠어요."):
        st.warning("감정을 기록하거나 최소 하나를 입력해주세요 💬")
    else:
        today = datetime.now().strftime("%Y-%m-%d")
        analyzer = SentimentIntensityAnalyzer()
        text = f"좋은 점: {positive}. 힘들었던 점: {negative}."
        vader_score = analyzer.polarity_scores(text)["compound"]
        blob_score = TextBlob(text).sentiment.polarity

        # 감정 보정
        if positive != "잘 모르겠어요." and negative == "잘 모르겠어요.":
            avg_score = 0.9
        elif negative != "잘 모르겠어요." and positive == "잘 모르겠어요.":
            avg_score = -0.9
        elif positive == "잘 모르겠어요." and negative == "잘 모르겠어요.":
            avg_score = 0.0
        else:
            avg_score = (vader_score + blob_score) / 2

        new_row = pd.DataFrame({
            "날짜": [today],
            "좋은 점": [positive],
            "힘들었던 점": [negative],
            "감정 점수": [round(avg_score, 3)]
        })
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

        st.success("오늘의 감정 일기가 저장되었습니다 💾")
        st.metric(label="감정 점수", value=f"{avg_score:.2f}")

        if avg_score > 0.3:
            st.success("관계가 긍정적인 방향으로 흐르고 있습니다 💖")
        elif avg_score < -0.3:
            st.error("감정적으로 거리가 느껴집니다 💔")
        else:
            st.info("균형 잡힌 감정 상태예요 ⚖️")

st.divider()

# 📊 주간 감정 변화
st.markdown("<h4 style='color:#6fa8dc;'>📊 주간 감정 변화</h4>", unsafe_allow_html=True)
if not df.empty:
    df["날짜"] = pd.to_datetime(df["날짜"])
    df["주"] = df["날짜"].dt.isocalendar().week
    weekly = df.groupby("주")["감정 점수"].mean().reset_index()
    fig = px.area(weekly, x="주", y="감정 점수", title="주별 감정 변화", color_discrete_sequence=["#f6b26b"])
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("주간 통계를 표시하려면 최소 2회 이상 기록이 필요합니다.")

st.divider()

# 😀 표정 보기
if st.button("😀 표정으로 보기", use_container_width=True):
    if df.empty:
        st.info("아직 데이터가 없습니다 💬")
    else:
        latest_score = df.iloc[-1]["감정 점수"]
        if latest_score > 0.7:
            st.image("https://i.imgur.com/3Qf7uUL.png", width=120, caption="😊 최고 좋음")
        elif latest_score > 0.3:
            st.image("https://i.imgur.com/oh2xVv1.png", width=120, caption="🙂 좋음")
        elif latest_score > -0.3:
            st.image("https://i.imgur.com/1Pg4Iea.png", width=120, caption="😐 보통")
        elif latest_score > -0.7:
            st.image("https://i.imgur.com/2g3AykR.png", width=120, caption="☹️ 별로")
        else:
            st.image("https://i.imgur.com/I1v3k0J.png", width=120, caption="😭 슬픔")

st.caption("💾 데이터는 로컬에만 저장됩니다. 모바일에서도 완벽 작동합니다 📱")
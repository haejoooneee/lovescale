import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import plotly.express as px

# 파일 경로
DATA_FILE = "lovescale_data.csv"
DICT_FILE = "emotion_dict.json"

# -------------------------------
# JSON 감정 사전 불러오기
# -------------------------------
if os.path.exists(DICT_FILE):
    with open(DICT_FILE, "r", encoding="utf-8") as f:
        emotion_dict = json.load(f)
else:
    st.error("⚠️ emotion_dict.json 파일을 찾을 수 없습니다.")
    st.stop()

positive_words = emotion_dict["positive"]
negative_words = emotion_dict["negative"]
neg_prefix = emotion_dict["neg_prefix"]

# -------------------------------
# 감정 분석 함수
# -------------------------------
def korean_sentiment_score(text):
    if not text or "없음" in text or "모르겠" in text:
        return 0

    score = 0
    for word in positive_words:
        if any(neg + word in text for neg in neg_prefix):  # “안 좋다” → 부정
            score -= 1
        elif word in text:
            score += 1

    for word in negative_words:
        if any(neg + word in text for neg in neg_prefix):  # “안 힘들다” → 긍정
            score += 1
        elif word in text:
            score -= 1

    # 정규화 (-1 ~ +1)
    if score > 0:
        return min(score / 3, 1)
    elif score < 0:
        return max(score / 3, -1)
    else:
        return 0

# -------------------------------
# Streamlit UI
# -------------------------------
st.set_page_config(page_title="💔 헤어짐의 저울질 (LoveScale)", layout="centered")
st.title("💔 헤어짐의 저울질 (LoveScale)")
st.write("AI가 감정의 흐름을 살펴보고, 관계의 온도를 시각화합니다.")
st.divider()

# 데이터 불러오기
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    if "감정 점수" not in df.columns:
        df["감정 점수"] = 0
else:
    df = pd.DataFrame(columns=["날짜", "좋은 점", "힘들었던 점", "감정 점수"])

# 세션 상태 초기화
for key in ["positive_hidden", "negative_hidden", "positive_text", "negative_text"]:
    if key not in st.session_state:
        st.session_state[key] = False if "hidden" in key else ""

# -------------------------------
# 📔 감정 입력 영역
# -------------------------------
st.header("📔 오늘의 감정 일기")

col1, col2 = st.columns(2)

# 좋은 점 입력
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

# 힘들었던 점 입력
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
        pos_score = korean_sentiment_score(positive)
        neg_score = korean_sentiment_score(negative)

        if "없음" in positive and "없음" not in negative:
            score = -abs(neg_score)
        elif "없음" in negative and "없음" not in positive:
            score = pos_score
        else:
            score = pos_score - abs(neg_score)

        today = datetime.now().strftime("%Y-%m-%d")

        new_row = pd.DataFrame({
            "날짜": [today],
            "좋은 점": [positive],
            "힘들었던 점": [negative],
            "감정 점수": [score]
        })
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

        st.success("오늘의 감정 일기가 저장되었습니다 💾")
        st.subheader("🧭 감정 분석 결과")
        st.write(f"📊 **감정 지수:** {score:.2f}")

        # 감정 해석
        if score >= 0.6:
            st.success("🌞 매우 긍정적인 하루였어요! 사랑과 행복이 가득합니다.")
        elif score >= 0.3:
            st.info("😊 좋은 하루였어요. 따뜻한 감정이 느껴집니다.")
        elif -0.3 < score < 0.3:
            st.warning("⚖️ 감정이 균형을 이루고 있습니다. 마음을 천천히 살펴보세요.")
        elif score <= -0.3 and score > -0.6:
            st.error("😢 조금 힘든 하루였어요. 자신을 돌봐주세요.")
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


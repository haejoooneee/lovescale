import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime
import plotly.express as px

# =============================
# ⚙️ 감정 사전 불러오기
# =============================
DICT_FILE = "emotion_dict.json"

if os.path.exists(DICT_FILE):
    with open(DICT_FILE, "r", encoding="utf-8") as f:
        emotion_dict = json.load(f)
else:
    st.error("⚠️ emotion_dict.json 파일이 없습니다. 같은 폴더에 위치시켜 주세요.")
    st.stop()

positive_words = emotion_dict["positive"]
negative_words = emotion_dict["negative"]
neg_prefix = emotion_dict["neg_prefix"]

# =============================
# ⚙️ 감정 점수 계산 함수
# =============================
def korean_sentiment_score(text):
    if not text or "없음" in text or "모르겠" in text:
        return 0

    score = 0
    # 긍정 단어: 부정 접두사와 함께 나오면 부정으로 뒤집기
    for word in positive_words:
        if any((neg + word) in text for neg in neg_prefix):
            score -= 1
        elif word in text:
            score += 1

    # 부정 단어: 부정 접두사와 함께 나오면 긍정으로 뒤집기
    for word in negative_words:
        if any((neg + word) in text for neg in neg_prefix):
            score += 1
        elif word in text:
            score -= 1

    return score

# =============================
# 📄 데이터 파일 설정
# =============================
DATA_FILE = "lovescale_data.csv"

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=["날짜", "좋은 점", "힘들었던 점", "감정 점수"])

# =============================
# 🖥️ UI 설정
# =============================
st.set_page_config(page_title="💔 헤어짐의 저울질", layout="centered")
st.title("💔 LOVE SCALE (헤어짐의 저울질)")
st.write("AI 없이도 감정의 흐름을 스스로 살펴볼 수 있는 감정 일기입니다.")
st.divider()

# =============================
# 📔 오늘의 감정 입력
# =============================
st.header("📔 오늘의 감정 일기")

# “좋은 점” 입력 + 없음(잘 모르겠음)
col1, col2 = st.columns([4, 1])
with col1:
    positive = st.text_area("좋았던 점 💕", placeholder="예: 함께 웃었던 대화가 즐거웠어요")
with col2:
    pos_none = st.button("없음(잘 모르겠음)", key="pos_none")

if pos_none:
    positive = "없음(잘 모르겠음)"
    st.experimental_rerun()

# “힘들었던 점” 입력 + 없음(잘 모르겠음)
col3, col4 = st.columns([4, 1])
with col3:
    negative = st.text_area("힘들었던 점 💔", placeholder="예: 대화가 자주 끊겨서 답답했어요")
with col4:
    neg_none = st.button("없음(잘 모르겠음)", key="neg_none")

if neg_none:
    negative = "없음(잘 모르겠음)"
    st.experimental_rerun()

# =============================
# 💾 감정 분석 및 저장
# =============================
if st.button("감정 분석 및 저장"):
    if not positive and not negative:
        st.warning("감정을 입력하거나 ‘없음(잘 모르겠음)’을 선택해주세요 💬")
    else:
        score = korean_sentiment_score(positive) + korean_sentiment_score(negative)
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

        # 감정 상태 표시
        if score > 0:
            st.subheader("✨ 현재 감정 상태: 긍정적")
            st.info("좋은 감정이 더 많아요 💖 관계가 긍정적인 흐름이에요.")
        elif score < 0:
            st.subheader("⚠️ 현재 감정 상태: 부정적")
            st.info("감정적으로 지친 하루였어요. 자신을 돌봐주세요 🌧️")
        else:
            st.subheader("⚖️ 현재 감정 상태: 균형")
            st.info("좋고 힘든 감정이 비슷하거나 없어요. 차분한 하루네요.")

# =============================
# ✏️ 기록 관리 (수정 및 삭제)
# =============================
st.divider()
st.header("✏️ 기록 관리")

if not df.empty:
    edit_date = st.selectbox("수정 또는 삭제할 날짜 선택", df["날짜"].unique())
    selected = df[df["날짜"] == edit_date].iloc[0]
    new_pos = st.text_area("좋은 점 수정", selected["좋은 점"])
    new_neg = st.text_area("힘들었던 점 수정", selected["힘들었던 점"])

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 수정 저장", key="edit_save"):
            df.loc[df["날짜"] == edit_date, ["좋은 점", "힘들었던 점"]] = [new_pos, new_neg]
            df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
            st.success("수정이 저장되었습니다 ✅")

    with col2:
        if st.button("🗑️ 삭제", key="edit_delete"):
            df = df[df["날짜"] != edit_date]
            df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
            st.warning("삭제되었습니다 ❌")
else:
    st.write("저장된 일기가 없습니다 💬")

# =============================
# 📊 주간 감정 변화 그래프
# =============================
st.divider()
st.header("📊 감정 변화 추이")

if not df.empty:
    df["날짜"] = pd.to_datetime(df["날짜"])
    df["주"] = df["날짜"].dt.isocalendar().week
    weekly = df.groupby("주")["감정 점수"].mean().reset_index()
    fig = px.line(weekly, x="주", y="감정 점수", title="주별 평균 감정 점수 변화", markers=True)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("아직 감정 데이터를 입력하지 않았습니다.")

# =============================
# 💡 ‘도와줘!!’ 버튼
# =============================
st.divider()
st.header("💬 도와줘!!")

if st.button("감정 분석 도우미 실행"):
    if len(df) < 2:
        st.info("최소 2회 이상의 기록이 필요합니다.")
    else:
        latest = df.iloc[-1]["감정 점수"]
        prev = df.iloc[-2]["감정 점수"]

        if latest > prev:
            st.success("감정 지수가 상승했습니다 ⬆️ 긍정적인 변화가 감지돼요!")
        elif latest < prev:
            st.warning("감정 지수가 하락했습니다 ⬇️ 감정적으로 조금 지쳤을 수 있어요.")
        else:
            st.info("감정 지수가 변하지 않았어요 ➡️ 안정된 흐름이에요.")

        st.subheader("📋 전체 감정 요약")
        good = df[df["감정 점수"] > 0].shape[0]
        bad = df[df["감정 점수"] < 0].shape[0]
        neutral = df[df["감정 점수"] == 0].shape[0]
        st.write(f"긍정적인 날: {good}회 😊")
        st.write(f"부정적인 날: {bad}회 😢")
        st.write(f"균형 잡힌 날: {neutral}회 ⚖️")

        st.write("👉 지금까지의 ‘좋은 점’과 ‘힘들었던 점’을 종합적으로 요약했어요:")

        st.write("**좋았던 점 모음:**")
        st.info(" / ".join(df["좋은 점"].dropna().tolist()[-5:]))

        st.write("**힘들었던 점 모음:**")
        st.error(" / ".join(df["힘들었던 점"].dropna().tolist()[-5:]))

st.caption("💾 데이터는 이 컴퓨터에만 저장됩니다.")



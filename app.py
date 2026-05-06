import streamlit as st
import pandas as pd
from collections import defaultdict
import jpholiday

st.title("当直・日直スケジューラ（祝日対応）")

# =========================
# ⓪ メンバー
# =========================
members = [m.strip() for m in st.text_input(
    "メンバー（カンマ区切り）", "A,B,C,D"
).split(",")]

# =========================
# ① 月設定
# =========================
year = st.number_input("年", 2026)
month = st.number_input("月", 5)

days = pd.date_range(f"{year}-{month:02d}-01", periods=31, freq="D")
days = [d for d in days if d.month == month]

# 土日祝判定
holiday_flag = {}
for d in days:
    is_holiday = (d.weekday() >= 5) or jpholiday.is_holiday(d.date())
    holiday_flag[d.day] = is_holiday

# =========================
# ② 希望入力
# =========================
st.subheader("希望入力（○ △ ×）")

preferences = {}
for m in members:
    st.write(f"### {m}")
    pref = {}
    for d in days:
        label = f"{d.day}日"
        if holiday_flag[d.day]:
            label += "（土日祝）"

        pref[d.day] = st.selectbox(
            label, ["", "○", "△", "×"],
            key=f"{m}_{d.day}"
        )
    preferences[m] = pref

def score(val):
    return {"○": 3, "△": 1, "×": -100}.get(val, 0)

# =========================
# ③ スケジューリング
# =========================
if st.button("シフト作成"):

    schedule = []
    work_count = defaultdict(int)
    holiday_count = defaultdict(int)
    last_worked = defaultdict(lambda: -10)

    for d in days:
        for duty in ["day", "night"]:

            candidates = []
            for m in members:

                # 連勤禁止
                if last_worked[m] == d.day - 1:
                    continue

                # 同日重複禁止
                if any(s["day"] == d.day and s["member"] == m for s in schedule):
                    continue

                sc = score(preferences[m][d.day])

                # 土日祝バランス
                if holiday_flag[d.day]:
                    sc -= holiday_count[m] * 2

                # 公平性
                sc -= work_count[m] * 1.5

                candidates.append((m, sc))

            if not candidates:
                continue

            candidates.sort(key=lambda x: x[1], reverse=True)
            chosen = candidates[0][0]

            schedule.append({
                "day": d.day,
                "type": duty,
                "member": chosen
            })

            work_count[chosen] += 1
            last_worked[chosen] = d.day

            if holiday_flag[d.day]:
                holiday_count[chosen] += 1

    df = pd.DataFrame(schedule)
    pivot = df.pivot(index="day", columns="type", values="member")

    st.subheader("シフト結果")
    st.dataframe(pivot)

    st.subheader("勤務回数")
    st.write(dict(work_count))

    st.subheader("土日祝回数")
    st.write(dict(holiday_count))

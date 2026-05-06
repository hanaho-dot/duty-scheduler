import streamlit as st
import pandas as pd
from collections import defaultdict
import jpholiday

st.title("勤務スケジューラ（Excel入力版）")

uploaded_file = st.file_uploader("Excelファイルをアップロード", type=["xlsx"])

if uploaded_file:

    members_df = pd.read_excel(uploaded_file, sheet_name="Members")
    duties_df = pd.read_excel(uploaded_file, sheet_name="Duties")
    pref_df = pd.read_excel(uploaded_file, sheet_name="Preferences")

    members = members_df["Name"].tolist()

    def score(val):
        return {"○": 3, "△": 1, "×": -100}.get(val, 0)

    schedule = []
    work_count = defaultdict(int)
    last_worked = defaultdict(lambda: -10)

    for _, row in duties_df.iterrows():
        day = int(row["Day"])
        duty = row["Duty"]
        needed = int(row["Required"])

        for _ in range(needed):

            candidates = []
            for m in members:

                if last_worked[m] == day - 1:
                    continue

                if any(s["day"] == day and s["member"] == m for s in schedule):
                    continue

                pref_row = pref_df[
                    (pref_df["Name"] == m) &
                    (pref_df["Day"] == day) &
                    (pref_df["Duty"] == duty)
                ]

                if len(pref_row) > 0:
                    sc = score(pref_row.iloc[0]["Preference"])
                else:
                    sc = 0

                sc -= work_count[m] * 1.5

                candidates.append((m, sc))

            if not candidates:
                continue

            candidates.sort(key=lambda x: x[1], reverse=True)
            chosen = candidates[0][0]

            schedule.append({
                "day": day,
                "duty": duty,
                "member": chosen
            })

            work_count[chosen] += 1
            last_worked[chosen] = day

    df = pd.DataFrame(schedule)

    pivot = df.pivot_table(
        index="day",
        columns="duty",
        values="member",
        aggfunc=lambda x: ",".join(x)
    )

    st.dataframe(pivot)

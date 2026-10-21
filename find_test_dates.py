
import pandas as pd

df = pd.read_csv("data/delhi_hour.csv")

df["Datetime"] = pd.to_datetime(
    df["Datetime"], errors="coerce"
)
df["AQI"] = pd.to_numeric(df["AQI"], errors="coerce")

df = df.dropna(subset=["Datetime"])
df["Date"] = df["Datetime"].dt.date
df["Hour"] = df["Datetime"].dt.hour

# Only inspect the school planning period: 6 AM to 6 PM.
school_hours = df[
    (df["Hour"] >= 6) & (df["Hour"] < 18)
].copy()

school_hours["Valid_AQI"] = school_hours["AQI"].between(
    0, 500, inclusive="both"
)

for selected_date, day in school_hours.groupby("Date"):
    valid_hours = day.loc[
        day["Valid_AQI"], "Hour"
    ].nunique()

    if valid_hours:
        print(
            f"{selected_date}: "
            f"{valid_hours}/12 valid AQI hours"
        )
